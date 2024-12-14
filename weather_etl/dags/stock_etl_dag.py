from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator, BranchPythonOperator
from airflow.operators.dummy import DummyOperator
from airflow.exceptions import AirflowException
import pandas as pd
import yfinance as yf
import logging
import os

# Configure logging
logger = logging.getLogger(__name__)

# Constants
DATA_DIR = '/opt/airflow/data'
COMPANIES = {
    'AAPL': 'Apple',
    'GOOGL': 'Google',
    'MSFT': 'Microsoft',
    'AMZN': 'Amazon',
    'META': 'Meta'
}
RAW_DATA_PATTERN = 'raw_stock_data_{}.csv'
PROCESSED_DATA_PATTERN = 'processed_stock_data_{}.csv'
QUALITY_THRESHOLD = 0.9  # 90% data quality threshold

# Default arguments for the DAG
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 12, 14),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

def get_file_path(filename):
    """Helper function to get full file path"""
    return os.path.join(DATA_DIR, filename)

def extract_stock_data(company_code, **context):
    """Extract stock data for a specific company"""
    try:
        logger.info(f"Starting data extraction for {COMPANIES[company_code]} ({company_code})")
        
        # Create data directory if it doesn't exist
        os.makedirs(DATA_DIR, exist_ok=True)
        
        # Download stock data
        stock = yf.Ticker(company_code)
        data = stock.history(period="1mo")
        
        if data.empty:
            raise AirflowException(f"No data retrieved for {company_code}")
        
        # Save raw data
        output_path = get_file_path(RAW_DATA_PATTERN.format(company_code))
        data.to_csv(output_path)
        
        logger.info(f"Stock data saved to {output_path}")
        logger.info(f"Data shape: {data.shape}")
        
        # Push metrics to XCom
        metrics = {
            'rows': len(data),
            'missing_values': data.isnull().sum().sum(),
            'trading_days': len(data[data['Volume'] > 0])
        }
        context['task_instance'].xcom_push(
            key=f'metrics_{company_code}',
            value=metrics
        )
        
        return output_path
    
    except Exception as e:
        logger.error(f"Error extracting data for {company_code}: {str(e)}")
        raise AirflowException(f"Failed to extract stock data for {company_code}: {str(e)}")

def check_data_quality(company_code, **context):
    """Check data quality and decide processing path"""
    try:
        logger.info(f"Checking data quality for {company_code}")
        
        # Get metrics from XCom
        task_instance = context['task_instance']
        metrics = task_instance.xcom_pull(
            key=f'metrics_{company_code}'
        )
        
        if not metrics:
            raise AirflowException(f"No metrics found for {company_code}")
        
        # Calculate quality score
        total_expected_values = metrics['rows'] * 6  # 6 columns in typical stock data
        missing_values = metrics['missing_values']
        quality_score = 1 - (missing_values / total_expected_values)
        
        logger.info(f"Quality score for {company_code}: {quality_score:.2f}")
        
        # Decide processing path based on quality score
        if quality_score >= QUALITY_THRESHOLD:
            return f'process_stock_data_{company_code}'
        else:
            return f'flag_low_quality_{company_code}'
    
    except Exception as e:
        logger.error(f"Error checking data quality for {company_code}: {str(e)}")
        raise AirflowException(f"Failed to check data quality for {company_code}: {str(e)}")

def process_stock_data(company_code, **context):
    """Process stock data for a specific company"""
    try:
        logger.info(f"Processing data for {company_code}")
        
        # Read raw data
        input_path = get_file_path(RAW_DATA_PATTERN.format(company_code))
        df = pd.read_csv(input_path)
        
        # Calculate technical indicators
        df['SMA_20'] = df['Close'].rolling(window=20).mean()
        df['EMA_20'] = df['Close'].ewm(span=20, adjust=False).mean()
        df['Daily_Return'] = df['Close'].pct_change()
        df['Volatility'] = df['Daily_Return'].rolling(window=20).std()
        
        # Save processed data
        output_path = get_file_path(PROCESSED_DATA_PATTERN.format(company_code))
        df.to_csv(output_path, index=False)
        
        logger.info(f"Processed data saved to {output_path}")
        return output_path
    
    except Exception as e:
        logger.error(f"Error processing data for {company_code}: {str(e)}")
        raise AirflowException(f"Failed to process stock data for {company_code}: {str(e)}")

def flag_low_quality(company_code, **context):
    """Handle low quality data"""
    logger.warning(f"Low quality data detected for {company_code}")
    # In a real scenario, you might want to:
    # - Send notifications
    # - Log to monitoring system
    # - Trigger data cleanup workflows
    return f"Low quality data flagged for {company_code}"

# Create the DAG
dag = DAG(
    'stock_etl_pipeline',
    default_args=default_args,
    description='A DAG for stock data ETL with dynamic tasks and branching',
    schedule_interval=timedelta(days=1),
    catchup=False
)

# Create start and end tasks
start_task = DummyOperator(
    task_id='start_pipeline',
    dag=dag
)

end_task = DummyOperator(
    task_id='end_pipeline',
    dag=dag,
    trigger_rule='none_failed'
)

# Dynamically create tasks for each company
for company_code in COMPANIES:
    # Extract task
    extract_task = PythonOperator(
        task_id=f'extract_stock_data_{company_code}',
        python_callable=extract_stock_data,
        op_kwargs={'company_code': company_code},
        dag=dag,
    )
    
    # Quality check (branching) task
    quality_check_task = BranchPythonOperator(
        task_id=f'check_data_quality_{company_code}',
        python_callable=check_data_quality,
        op_kwargs={'company_code': company_code},
        dag=dag,
    )
    
    # Process task (good quality path)
    process_task = PythonOperator(
        task_id=f'process_stock_data_{company_code}',
        python_callable=process_stock_data,
        op_kwargs={'company_code': company_code},
        dag=dag,
    )
    
    # Flag task (low quality path)
    flag_task = PythonOperator(
        task_id=f'flag_low_quality_{company_code}',
        python_callable=flag_low_quality,
        op_kwargs={'company_code': company_code},
        dag=dag,
    )
    
    # Join paths with dummy operator
    join_task = DummyOperator(
        task_id=f'join_paths_{company_code}',
        dag=dag,
        trigger_rule='none_failed'
    )
    
    # Set task dependencies
    start_task >> extract_task >> quality_check_task
    quality_check_task >> [process_task, flag_task]
    [process_task, flag_task] >> join_task >> end_task
