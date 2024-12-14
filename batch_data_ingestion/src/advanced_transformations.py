from typing import Iterator
import pandas as pd
import numpy as np
from pyspark.sql import SparkSession
from pyspark.sql.pandas.functions import pandas_udf, PandasUDFType
from pyspark.sql.types import (
    StructType, StructField, StringType, IntegerType, 
    DoubleType, ArrayType, TimestampType
)
from datetime import datetime, timedelta
from packaging.version import Version as LooseVersion
import os

# Define Arrow-optimized Pandas UDF for inventory analysis
@pandas_udf(returnType=DoubleType())
def calculate_inventory_score(
    quantity: pd.Series,
    capacity: pd.Series,
    last_updated: pd.Series
) -> pd.Series:
    """Calculate inventory score based on quantity, capacity and last update time"""
    # Convert last_updated to pandas datetime if it's not already
    last_updated_dt = pd.to_datetime(last_updated)
    current_time = pd.Timestamp.now()
    
    # Calculate days since update using vectorized operations
    days_since_update = (current_time - last_updated_dt).dt.total_seconds() / 86400
    
    # Calculate utilization ratio
    utilization_ratio = quantity / capacity
    
    # Score formula: Higher score for balanced inventory (not too low, not too high)
    # and penalize for old updates
    score = (
        (1 - (utilization_ratio - 0.5).abs() * 2) * 100 -  # Optimal at 50% capacity
        days_since_update * 2  # Penalty for old data
    )
    return score.clip(0, 100)

# Schema for order analysis UDTF
order_analysis_schema = StructType([
    StructField("customer_id", IntegerType(), False),
    StructField("total_orders", IntegerType(), False),
    StructField("total_spent", DoubleType(), False),
    StructField("avg_order_value", DoubleType(), True),
    StructField("avg_days_between_orders", DoubleType(), True),
    StructField("peak_order_hour", IntegerType(), True)
])

# Define Python UDTF for order analysis
@pandas_udf(returnType=order_analysis_schema)
def analyze_order_patterns(customer_id: pd.Series, order_date: pd.Series, total_amount: pd.Series) -> pd.DataFrame:
    """Analyze order patterns and generate insights"""
    # Create empty lists to store results
    results = []
    
    # Process each unique customer
    for cid in customer_id.unique():
        mask = customer_id == cid
        customer_orders = pd.DataFrame({
            'order_date': order_date[mask],
            'total_amount': total_amount[mask]
        }).sort_values('order_date')
        
        # Calculate order frequency
        date_diffs = customer_orders['order_date'].diff()
        avg_days_between_orders = date_diffs.dt.total_seconds().mean() / 86400 if not date_diffs.empty else None
        
        # Calculate spending patterns
        total_spent = customer_orders['total_amount'].sum()
        avg_order_value = customer_orders['total_amount'].mean()
        order_count = len(customer_orders)
        
        # Identify peak ordering times
        if not customer_orders.empty:
            peak_hour = customer_orders['order_date'].dt.hour.mode().iloc[0]
        else:
            peak_hour = None
        
        results.append({
            'customer_id': cid,
            'total_orders': order_count,
            'total_spent': float(total_spent),
            'avg_order_value': float(avg_order_value),
            'avg_days_between_orders': float(avg_days_between_orders) if avg_days_between_orders else None,
            'peak_order_hour': int(peak_hour) if peak_hour is not None else None
        })
    
    return pd.DataFrame(results)

def create_complex_inventory_view(spark: SparkSession) -> None:
    """Create a complex view combining inventory, orders, and customer data"""
    
    # Register the UDFs
    spark.udf.register("calculate_inventory_score", calculate_inventory_score)
    
    # Load tables from MySQL and create temporary views
    mysql_properties = {
        "driver": "com.mysql.cj.jdbc.Driver",
        "url": f"jdbc:mysql://{os.getenv('MYSQL_HOST')}:{os.getenv('MYSQL_PORT')}/{os.getenv('MYSQL_DATABASE')}",
        "user": os.getenv("MYSQL_USER"),
        "password": os.getenv("MYSQL_PASSWORD")
    }
    
    # Load and register each required table
    for table in ["products", "product_inventory", "inventory_locations", "orders", "order_items", "customers"]:
        df = spark.read.format("jdbc") \
            .options(**mysql_properties) \
            .option("dbtable", table) \
            .load()
        df.createOrReplaceTempView(table)
    
    # Create base views
    inventory_view = spark.sql("""
        SELECT 
            p.product_id,
            p.name as product_name,
            p.price,
            pi.quantity,
            il.capacity,
            il.warehouse_code,
            il.city,
            pi.last_updated
        FROM products p
        JOIN product_inventory pi ON p.product_id = pi.product_id
        JOIN inventory_locations il ON pi.location_id = il.location_id
    """)
    inventory_view.createOrReplaceTempView("detailed_inventory")
    
    # Create complex view with inventory scores
    spark.sql("""
        CREATE OR REPLACE TEMPORARY VIEW inventory_analytics AS
        SELECT 
            product_id,
            product_name,
            price,
            quantity,
            capacity,
            warehouse_code,
            city,
            CAST(last_updated AS TIMESTAMP) as last_updated,
            calculate_inventory_score(
                CAST(quantity AS DOUBLE),
                CAST(capacity AS DOUBLE),
                CAST(last_updated AS TIMESTAMP)
            ) as inventory_score
        FROM detailed_inventory
    """)
    
    # Create order analysis view using SQL aggregations
    spark.sql("""
        CREATE OR REPLACE TEMPORARY VIEW customer_order_analytics AS
        SELECT 
            customer_id,
            COUNT(*) as total_orders,
            SUM(total_amount) as total_spent,
            AVG(total_amount) as avg_order_value,
            (UNIX_TIMESTAMP(MAX(order_date)) - UNIX_TIMESTAMP(MIN(order_date))) / (86400.0 * GREATEST(COUNT(*) - 1, 1)) as avg_days_between_orders,
            HOUR(order_date) as peak_order_hour
        FROM orders
        GROUP BY customer_id, HOUR(order_date)
    """)
    
    # Final complex view combining all analytics
    spark.sql("""
        CREATE OR REPLACE TEMPORARY VIEW business_analytics AS
        SELECT 
            i.*,
            c.first_name,
            c.last_name,
            coa.total_orders,
            coa.total_spent,
            coa.avg_order_value,
            coa.avg_days_between_orders,
            coa.peak_order_hour,
            o.order_id,
            o.order_date,
            oi.quantity as ordered_quantity
        FROM inventory_analytics i
        LEFT JOIN order_items oi ON i.product_id = oi.product_id
        LEFT JOIN orders o ON oi.order_id = o.order_id
        LEFT JOIN customers c ON o.customer_id = c.customer_id
        LEFT JOIN customer_order_analytics coa ON c.customer_id = coa.customer_id
        WHERE o.order_date >= date_sub(current_date(), 30)
    """)

def get_business_insights(spark: SparkSession):
    """Get business insights from the complex view"""
    return spark.sql("""
        SELECT 
            product_name,
            city,
            warehouse_code,
            inventory_score,
            quantity as current_stock,
            sum(ordered_quantity) as total_ordered,
            count(distinct order_id) as number_of_orders,
            avg(avg_order_value) as customer_avg_order_value
        FROM business_analytics
        GROUP BY 
            product_name,
            city,
            warehouse_code,
            inventory_score,
            quantity
        ORDER BY inventory_score DESC
    """)
