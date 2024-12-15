import snowflake.connector
import os
from dotenv import load_dotenv
import pandas as pd
import random
from datetime import datetime, timedelta

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

def create_sample_sales_data(start_date, num_records):
    """Create sample sales data"""
    regions = ['North', 'South', 'East', 'West']
    product_categories = ['Electronics', 'Clothing', 'Food', 'Home', 'Sports']
    
    data = []
    for _ in range(num_records):
        date = start_date + timedelta(days=random.randint(0, 365))
        date_str = date.strftime('%Y-%m-%d')
        data.append({
            'transaction_date': date_str,
            'order_date': date_str,
            'region': random.choice(regions),
            'product_category': random.choice(product_categories),
            'amount': round(random.uniform(10, 1000), 2),
            'customer_id': random.randint(1, 1000),
            'order_amount': round(random.uniform(50, 5000), 2),
            'revenue': round(random.uniform(100, 10000), 2),
            'year': date.year,
            'month': date.month
        })
    
    return pd.DataFrame(data)

def batch_insert(cursor, table_name, columns, values, batch_size=10000):
    """Insert data in batches"""
    for i in range(0, len(values), batch_size):
        batch_values = values[i:i + batch_size]
        placeholders = ','.join(['(' + ','.join(['%s'] * len(columns)) + ')'] * len(batch_values))
        flattened_values = [val for row in batch_values for val in row]
        
        insert_sql = f"""
        INSERT INTO {table_name} ({','.join(columns)})
        VALUES {placeholders}
        """
        cursor.execute(insert_sql, flattened_values)
        print(f"Inserted {len(batch_values)} records into {table_name}")

def setup_snowflake_tables(conn):
    """Set up Snowflake tables with different optimization strategies"""
    cursor = conn.cursor()
    
    try:
        # Generate sample data
        print("Generating sample data...")
        start_date = datetime(2023, 1, 1)
        df = create_sample_sales_data(start_date, 100000)  # Reduced to 10k records for testing
        
        # 1. Create and load clustered table
        cursor.execute("""
        CREATE OR REPLACE TABLE sales_clustered (
            transaction_id NUMBER AUTOINCREMENT,
            order_date DATE,
            order_amount FLOAT,
            customer_id INTEGER
        ) CLUSTER BY (order_date)
        """)
        
        # 2. Create non-clustered table with same schema
        cursor.execute("""
        CREATE OR REPLACE TABLE sales_non_clustered (
            transaction_id NUMBER AUTOINCREMENT,
            order_date DATE,
            order_amount FLOAT,
            customer_id INTEGER
        )
        """)
        
        # 3. Create partitioned table
        cursor.execute("""
        CREATE OR REPLACE TABLE sales_partitioned (
            transaction_id NUMBER AUTOINCREMENT,
            transaction_date DATE,
            region STRING,
            product_category STRING,
            revenue FLOAT,
            year INTEGER,
            month INTEGER
        ) CLUSTER BY (year, month)
        """)
        
        # 4. Create non-partitioned table
        cursor.execute("""
        CREATE OR REPLACE TABLE sales_non_partitioned (
            transaction_id NUMBER AUTOINCREMENT,
            transaction_date DATE,
            region STRING,
            product_category STRING,
            revenue FLOAT
        )
        """)
        
        # 5. Create base table for materialized view
        cursor.execute("""
        CREATE OR REPLACE TABLE sales_transactions (
            transaction_id NUMBER AUTOINCREMENT,
            sale_date DATE,
            amount FLOAT,
            customer_id INTEGER
        )
        """)
        
        # 6. Create materialized view
        cursor.execute("""
        CREATE OR REPLACE MATERIALIZED VIEW daily_sales_mv AS
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
        """)
        
        # Prepare data for batch insertion
        print("Preparing data for batch insertion...")
        
        # Prepare clustered/non-clustered table data
        clustered_data = [(row['order_date'], row['order_amount'], row['customer_id']) 
                         for _, row in df.iterrows()]
        
        # Prepare partitioned table data
        partitioned_data = [(row['transaction_date'], row['region'], row['product_category'],
                           row['revenue'], row['year'], row['month']) 
                          for _, row in df.iterrows()]
        
        # Prepare non-partitioned table data
        non_partitioned_data = [(row['transaction_date'], row['region'], row['product_category'],
                               row['revenue']) 
                              for _, row in df.iterrows()]
        
        # Prepare transactions table data
        transactions_data = [(row['transaction_date'], row['amount'], row['customer_id'])
                           for _, row in df.iterrows()]
        
        print("Loading data into tables using batch insertion...")
        
        # Batch insert into clustered table
        batch_insert(cursor, 'sales_clustered', 
                    ['order_date', 'order_amount', 'customer_id'],
                    clustered_data)
        
        # Batch insert into non-clustered table
        batch_insert(cursor, 'sales_non_clustered',
                    ['order_date', 'order_amount', 'customer_id'],
                    clustered_data)
        
        # Batch insert into partitioned table
        batch_insert(cursor, 'sales_partitioned',
                    ['transaction_date', 'region', 'product_category', 'revenue', 'year', 'month'],
                    partitioned_data)
        
        # Batch insert into non-partitioned table
        batch_insert(cursor, 'sales_non_partitioned',
                    ['transaction_date', 'region', 'product_category', 'revenue'],
                    non_partitioned_data)
        
        # Batch insert into transactions table
        batch_insert(cursor, 'sales_transactions',
                    ['sale_date', 'amount', 'customer_id'],
                    transactions_data)
        
        print("Successfully created tables and loaded sample data!")
        
        # Verify data
        for table in ['sales_clustered', 'sales_non_clustered', 'sales_partitioned', 
                     'sales_non_partitioned', 'sales_transactions']:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"Total records in {table}: {count}")
        
    except Exception as e:
        print(f"Error setting up Snowflake tables: {e}")
        raise e
    finally:
        cursor.close()

def main():
    try:
        # Connect to Snowflake
        conn = snowflake.connector.connect(**conn_params)
        print("Connected to Snowflake successfully!")
        
        # Setup tables and load data
        setup_snowflake_tables(conn)
        
    except Exception as e:
        print(f"Error connecting to Snowflake: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    main()
