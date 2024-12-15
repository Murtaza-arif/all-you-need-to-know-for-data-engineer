import snowflake.connector
import time
from datetime import datetime
import pandas as pd
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Snowflake connection parameters
conn_params = {
    'user': os.getenv('SNOWFLAKE_USER'),
    'password': os.getenv('SNOWFLAKE_PASSWORD'),
    'account': os.getenv('SNOWFLAKE_ACCOUNT'),
    'warehouse': os.getenv('SNOWFLAKE_WAREHOUSE'),
    'database': os.getenv('SNOWFLAKE_DATABASE'),
    'schema': os.getenv('SNOWFLAKE_SCHEMA')
}

def connect_to_snowflake():
    """Establish connection to Snowflake"""
    try:
        conn = snowflake.connector.connect(**conn_params)
        return conn
    except Exception as e:
        print(f"Error connecting to Snowflake: {e}")
        return None

def execute_query_with_timing(cursor, query):
    """Execute a query and measure its execution time"""
    start_time = time.time()
    try:
        cursor.execute(query)
        results = cursor.fetchall()
        end_time = time.time()
        execution_time = end_time - start_time
        return results, execution_time
    except Exception as e:
        print(f"Error executing query: {e}")
        return None, None

def main():
    # Connect to Snowflake
    conn = connect_to_snowflake()
    if not conn:
        return

    cursor = conn.cursor()

    # Sample queries demonstrating data management importance
    queries = [
        # Query 1: Using a well-organized table with proper clustering
        """
        SELECT order_date, 
               SUM(order_amount) as total_amount
        FROM sales_clustered
        WHERE order_date BETWEEN '2023-01-01' AND '2023-12-31'
        GROUP BY order_date
        ORDER BY order_date;
        """,
        
        # Query 2: Same query on non-clustered table
        """
        SELECT order_date, 
               SUM(order_amount) as total_amount
        FROM sales_non_clustered
        WHERE order_date BETWEEN '2023-01-01' AND '2023-12-31'
        GROUP BY order_date
        ORDER BY order_date;
        """,
        
        # Query 3: Using partitioned table for efficient filtering
        """
        SELECT region,
               product_category,
               SUM(revenue) as total_revenue
        FROM sales_partitioned
        WHERE year = 2023 AND month = 12
        GROUP BY region, product_category
        ORDER BY total_revenue DESC;
        """,
        
        # Query 4: Same query on non-partitioned table
        """
        SELECT region,
               product_category,
               SUM(revenue) as total_revenue
        FROM sales_non_partitioned
        WHERE YEAR(transaction_date) = 2023 
        AND MONTH(transaction_date) = 12
        GROUP BY region, product_category
        ORDER BY total_revenue DESC;
        """,

        # Query 5: Data inspection query
        """
        SELECT 
            MIN(daily_revenue) as min_revenue,
            MAX(daily_revenue) as max_revenue,
            AVG(daily_revenue) as avg_revenue,
            MIN(transaction_count) as min_transactions,
            MAX(transaction_count) as max_transactions,
            AVG(transaction_count) as avg_transactions,
            MIN(high_value_transactions) as min_high_value,
            MAX(high_value_transactions) as max_high_value,
            AVG(high_value_transactions) as avg_high_value
        FROM daily_sales_mv;
        """,
        
        # Query 6: Using materialized view with adjusted thresholds
        """
        WITH avg_metrics AS (
            SELECT 
                AVG(daily_revenue) as avg_daily_revenue,
                AVG(transaction_count) as avg_daily_transactions
            FROM daily_sales_mv
        )
        SELECT 
            mv.*,
            (mv.daily_revenue - avg_daily_revenue) / avg_daily_revenue * 100 as revenue_variance_pct,
            (mv.high_value_transactions::FLOAT / mv.transaction_count) * 100 as high_value_tx_pct,
            (mv.max_transaction - mv.min_transaction) / mv.avg_transaction_value as price_range_ratio
        FROM daily_sales_mv mv, avg_metrics
        WHERE mv.daily_revenue > avg_daily_revenue * 0.5  -- Days with at least 50% of average revenue
        AND mv.transaction_count > avg_daily_transactions * 0.5  -- Days with at least 50% of average transactions
        AND mv.high_value_transactions >= 1  -- Days with at least 1 high-value transaction
        ORDER BY mv.daily_revenue DESC
        LIMIT 100;
        """,
        
        # Query 7: Same analysis without materialized view - adjusted thresholds
        """
        WITH daily_stats AS (
            SELECT 
                sale_date,
                SUM(amount) as daily_revenue,
                COUNT(*) as transaction_count,
                AVG(amount) as avg_transaction_value,
                SUM(CASE WHEN amount > 500 THEN 1 ELSE 0 END) as high_value_transactions,
                MIN(amount) as min_transaction,
                MAX(amount) as max_transaction
            FROM sales_transactions
            GROUP BY sale_date
        ),
        avg_metrics AS (
            SELECT 
                AVG(daily_revenue) as avg_daily_revenue,
                AVG(transaction_count) as avg_daily_transactions
            FROM daily_stats
        )
        SELECT 
            ds.*,
            (ds.daily_revenue - avg_daily_revenue) / avg_daily_revenue * 100 as revenue_variance_pct,
            (ds.high_value_transactions::FLOAT / ds.transaction_count) * 100 as high_value_tx_pct,
            (ds.max_transaction - ds.min_transaction) / ds.avg_transaction_value as price_range_ratio
        FROM daily_stats ds, avg_metrics
        WHERE ds.daily_revenue > avg_daily_revenue * 0.5  -- Days with at least 50% of average revenue
        AND ds.transaction_count > avg_daily_transactions * 0.5  -- Days with at least 50% of average transactions
        AND ds.high_value_transactions >= 1  -- Days with at least 1 high-value transaction
        ORDER BY ds.daily_revenue DESC
        LIMIT 100;
        """
    ]

    # Execute each query and measure performance
    print("\nQuery Performance Comparison - Data Management Impact:")
    print("-" * 60)
    
    for i, query in enumerate(queries, 1):
        print(f"\nQuery {i}:")
        if i % 2 == 1:
            print("(Optimized data management approach)")
        else:
            print("(Non-optimized approach)")
        results, execution_time = execute_query_with_timing(cursor, query)
        
        if results and execution_time:
            print(f"Execution time: {execution_time:.4f} seconds")
            print(f"Number of rows returned: {len(results)}")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    main()
