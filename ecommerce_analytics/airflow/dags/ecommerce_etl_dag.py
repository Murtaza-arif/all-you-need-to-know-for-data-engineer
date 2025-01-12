from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.snowflake.operators.snowflake import SnowflakeOperator
import pandas as pd
import os
from dotenv import load_dotenv
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Constants
DATA_DIR = '/opt/airflow/data'
RAW_DATA_FILE = 'raw_sales.csv'
CLEANED_DATA_FILE = 'cleaned_sales.csv'

# Load environment variables
load_dotenv()

# Default arguments for the DAG
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
    'start_date': datetime(2025, 1, 12),
}

def get_file_path(filename):
    """Helper function to get full file path"""
    return os.path.join(DATA_DIR, filename)

def ingest_sales_data(**context):
    """Ingest sales data from source"""
    try:
        logger.info("Starting ingest_sales_data task")
        
        # Create data directory if it doesn't exist
        logger.info(f"Creating directory if not exists: {DATA_DIR}")
        os.makedirs(DATA_DIR, exist_ok=True)
        
        # Sample data creation (replace with actual data source)
        data = {
            'order_id': range(1000, 1010),
            'customer_id': range(1, 11),
            'product_id': range(100, 110),
            'quantity': [2, 1, 3, 2, 1, 4, 2, 3, 1, 2],
            'amount': [100.0, 50.0, 150.0, 200.0, 75.0, 300.0, 125.0, 175.0, 80.0, 90.0],
            'order_date': [datetime.now().strftime('%Y-%m-%d')] * 10
        }
        df = pd.DataFrame(data)
        
        # Save to CSV
        output_path = get_file_path(RAW_DATA_FILE)
        logger.info(f"Saving raw data to: {output_path}")
        df.to_csv(output_path, index=False)
        
        # Push file path to XCom for next task
        context['task_instance'].xcom_push(key='raw_data_path', value=output_path)
        logger.info("Sales data ingestion completed successfully")
        
    except Exception as e:
        logger.error(f"Error in ingest_sales_data: {str(e)}")
        raise

def clean_data(**context):
    """Clean and transform the data"""
    try:
        logger.info("Starting clean_data task")
        
        # Get input path from previous task
        input_path = context['task_instance'].xcom_pull(task_ids='ingest_data', key='raw_data_path')
        logger.info(f"Reading data from: {input_path}")
        
        df = pd.read_csv(input_path)
        
        # Perform cleaning operations
        df['amount'] = df['amount'].fillna(0)
        df['quantity'] = df['quantity'].fillna(0)
        
        # Save cleaned data
        output_path = get_file_path(CLEANED_DATA_FILE)
        logger.info(f"Saving cleaned data to: {output_path}")
        df.to_csv(output_path, index=False)
        
        # Push file path to XCom for next task
        context['task_instance'].xcom_push(key='cleaned_data_path', value=output_path)
        logger.info("Data cleaning completed successfully")
        
    except Exception as e:
        logger.error(f"Error in clean_data: {str(e)}")
        raise

# Create DAG
dag = DAG(
    'ecommerce_etl_v1',  # Updated DAG ID
    default_args=default_args,
    description='E-commerce ETL pipeline',
    schedule_interval=timedelta(days=1),
    catchup=False,
    tags=['ecommerce', 'etl'],
)

# Create tasks
ingest_task = PythonOperator(
    task_id='ingest_data',
    python_callable=ingest_sales_data,
    provide_context=True,
    dag=dag,
)

clean_task = PythonOperator(
    task_id='clean_data',
    python_callable=clean_data,
    provide_context=True,
    dag=dag,
)

# Snowflake loading task
create_stage_sql = """
CREATE OR REPLACE STAGE sales_data_stage
FILE_FORMAT = (TYPE = CSV FIELD_DELIMITER = ',' SKIP_HEADER = 1);

PUT file:///opt/airflow/data/cleaned_sales.csv @sales_data_stage AUTO_COMPRESS=FALSE;
"""

snowflake_sql = """
CREATE TABLE IF NOT EXISTS sales_data (
    order_id INTEGER,
    customer_id INTEGER,
    product_id INTEGER,
    quantity INTEGER,
    amount FLOAT,
    order_date DATE
);

COPY INTO sales_data
FROM @sales_data_stage
FILE_FORMAT = (TYPE = CSV FIELD_DELIMITER = ',' SKIP_HEADER = 1)
PATTERN = '.*cleaned_sales.csv'
ON_ERROR = 'CONTINUE';
"""

create_stage = SnowflakeOperator(
    task_id='create_stage',
    sql=create_stage_sql,
    snowflake_conn_id='snowflake_default',
    warehouse='COMPUTE_WH',
    database='DATAMANAGEMENT',
    schema='PUBLIC',
    autocommit=True,
    dag=dag,
)

load_to_snowflake = SnowflakeOperator(
    task_id='load_to_snowflake',
    sql=snowflake_sql,
    snowflake_conn_id='snowflake_default',
    warehouse='COMPUTE_WH',
    database='DATAMANAGEMENT',
    schema='PUBLIC',
    autocommit=True,
    dag=dag,
)

# Set task dependencies
ingest_task >> clean_task >> create_stage >> load_to_snowflake
