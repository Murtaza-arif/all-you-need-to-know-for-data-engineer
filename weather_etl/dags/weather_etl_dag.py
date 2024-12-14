from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.exceptions import AirflowException
import pandas as pd
import requests
import os
from dotenv import load_dotenv
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Constants
DATA_DIR = '/opt/airflow/data'
RAW_DATA_FILE = 'raw_weather_data.csv'
TRANSFORMED_DATA_FILE = 'transformed_weather_data.csv'
FINAL_DATA_FILE = 'final_weather_data.csv'

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

def extract_weather_data(**context):
    """Extract weather data from API"""
    try:
        logger.info("Starting extract_weather_data task")
        
        # Create data directory if it doesn't exist
        logger.info(f"Creating directory if not exists: {DATA_DIR}")
        os.makedirs(DATA_DIR, exist_ok=True)
        
        # Verify directory exists and has write permissions
        if not os.path.exists(DATA_DIR):
            raise AirflowException(f"Failed to create directory: {DATA_DIR}")
        if not os.access(DATA_DIR, os.W_OK):
            raise AirflowException(f"No write permission for directory: {DATA_DIR}")
            
        # Load environment variables from mounted .env file
        env_path = '/opt/airflow/.env'
        if not os.path.exists(env_path):
            raise AirflowException(f"Environment file not found at {env_path}")
        load_dotenv(env_path)
        
        api_key = os.getenv('WEATHER_API_KEY')
        if not api_key:
            raise AirflowException("Weather API key not found in environment variables")
            
        logger.info(f"Using API key: {api_key[:4]}...")

        # Example cities
        cities = ['London', 'New York', 'Tokyo', 'Sydney', 'Mumbai']
        weather_data = []
        
        for city in cities:
            try:
                url = f'http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric'
                logger.info(f"Fetching weather data for {city}")
                response = requests.get(url)
                response.raise_for_status()
                
                data = response.json()
                weather_data.append({
                    'city': city,
                    'temperature': data['main']['temp'],
                    'humidity': data['main']['humidity'],
                    'pressure': data['main']['pressure'],
                    'weather_desc': data['weather'][0]['description'],
                    'wind_speed': data['wind']['speed'],
                    'timestamp': datetime.utcnow()
                })
                logger.info(f"Successfully fetched data for {city}")
            
            except requests.RequestException as e:
                logger.error(f"Error fetching data for {city}: {str(e)}")
                continue
        
        if not weather_data:
            raise AirflowException("No weather data was collected for any city")
        
        # Save data to CSV
        output_path = get_file_path(RAW_DATA_FILE)
        logger.info(f"Saving raw data to: {output_path}")
        df = pd.DataFrame(weather_data)
        df.to_csv(output_path, index=False)
        
        logger.info(f"Weather data saved to {output_path}")
        logger.info(f"Data preview:\n{df.head()}")
        logger.info(f"Data shape: {df.shape}")
        
        # Verify file was created
        if not os.path.exists(output_path):
            raise AirflowException(f"Failed to create output file: {output_path}")
        
        # Push the file path to XCom
        logger.info(f"Pushing file path to XCom: {output_path}")
        context['task_instance'].xcom_push(key='raw_data_path', value=output_path)
        
        # Verify XCom push
        pushed_value = context['task_instance'].xcom_pull(key='raw_data_path')
        logger.info(f"Verified XCom value: {pushed_value}")
        
        return output_path
    
    except Exception as e:
        logger.error(f"Error in extract_weather_data: {str(e)}")
        raise AirflowException(f"Failed to extract weather data: {str(e)}")

def transform_weather_data(**context):
    """Transform and clean weather data"""
    try:
        logger.info("Starting transform_weather_data task")
        
        # Get input file path from XCom
        task_instance = context['task_instance']
        logger.info("Attempting to pull raw_data_path from XCom")
        input_path = task_instance.xcom_pull(task_ids='extract_weather_data', key='raw_data_path')
        logger.info(f"XCom pull result: {input_path}")
        
        if not input_path:
            logger.error("No input file path received from extract task")
            # Try to list available XCom values
            try:
                all_xcoms = task_instance.xcom_pull(task_ids='extract_weather_data')
                logger.info(f"Available XComs from extract task: {all_xcoms}")
            except Exception as xe:
                logger.error(f"Error checking XComs: {str(xe)}")
            raise AirflowException("No input file path received from extract task")
            
        logger.info(f"Looking for input file at: {input_path}")
        
        if not os.path.exists(input_path):
            raise AirflowException(f"Input file not found at {input_path}")
        
        logger.info(f"Reading data from {input_path}")
        df = pd.read_csv(input_path)
        
        if df.empty:
            raise AirflowException("Input data is empty")
        
        logger.info(f"Input data shape: {df.shape}")
        
        # Convert temperature to Fahrenheit
        df['temperature_f'] = df['temperature'] * 9/5 + 32
        
        # Categorize temperature
        df['temp_category'] = pd.cut(df['temperature'],
                                    bins=[-float('inf'), 0, 15, 25, float('inf')],
                                    labels=['Cold', 'Mild', 'Warm', 'Hot'])
        
        # Clean weather description
        df['weather_desc'] = df['weather_desc'].str.title()
        
        # Calculate wind speed in mph
        df['wind_speed_mph'] = df['wind_speed'] * 2.237
        
        # Add data quality flags
        df['data_quality'] = 'Good'
        df.loc[df['humidity'] > 100, 'data_quality'] = 'Check humidity'
        df.loc[df['pressure'] < 870, 'data_quality'] = 'Check pressure'
        
        # Save transformed data
        output_path = get_file_path(TRANSFORMED_DATA_FILE)
        logger.info(f"Saving transformed data to: {output_path}")
        df.to_csv(output_path, index=False)
        
        logger.info(f"Transformed data saved to {output_path}")
        logger.info(f"Transformed data preview:\n{df.head()}")
        logger.info(f"Transformed data shape: {df.shape}")
        
        # Verify file was created
        if not os.path.exists(output_path):
            raise AirflowException(f"Failed to create output file: {output_path}")
        
        # Push the transformed file path to XCom
        logger.info(f"Pushing transformed file path to XCom: {output_path}")
        task_instance.xcom_push(key='transformed_data_path', value=output_path)
        
        # Verify XCom push
        pushed_value = task_instance.xcom_pull(key='transformed_data_path')
        logger.info(f"Verified XCom value: {pushed_value}")
        
        return output_path
    
    except Exception as e:
        logger.error(f"Error in transform_weather_data: {str(e)}")
        raise AirflowException(f"Failed to transform weather data: {str(e)}")

def load_weather_data(**context):
    """Load transformed data"""
    try:
        logger.info("Starting load_weather_data task")
        
        # Get transformed file path from XCom
        task_instance = context['task_instance']
        logger.info("Attempting to pull transformed_data_path from XCom")
        input_path = task_instance.xcom_pull(task_ids='transform_weather_data', key='transformed_data_path')
        logger.info(f"XCom pull result: {input_path}")
        
        if not input_path:
            logger.error("No input file path received from transform task")
            # Try to list available XCom values
            try:
                all_xcoms = task_instance.xcom_pull(task_ids='transform_weather_data')
                logger.info(f"Available XComs from transform task: {all_xcoms}")
            except Exception as xe:
                logger.error(f"Error checking XComs: {str(xe)}")
            raise AirflowException("No input file path received from transform task")
            
        logger.info(f"Looking for input file at: {input_path}")
        
        if not os.path.exists(input_path):
            raise AirflowException(f"Input file not found at {input_path}")
        
        logger.info(f"Reading transformed data from {input_path}")
        df = pd.read_csv(input_path)
        
        if df.empty:
            raise AirflowException("Transformed data is empty")
        
        # Save final data
        output_path = get_file_path(FINAL_DATA_FILE)
        logger.info(f"Saving final data to: {output_path}")
        df.to_csv(output_path, index=False)
        
        logger.info(f"Final data saved to {output_path}")
        logger.info(f"Final data shape: {df.shape}")
        
        # Verify file was created
        if not os.path.exists(output_path):
            raise AirflowException(f"Failed to create output file: {output_path}")
        
        return output_path
    
    except Exception as e:
        logger.error(f"Error in load_weather_data: {str(e)}")
        raise AirflowException(f"Failed to load weather data: {str(e)}")

# Create the DAG
dag = DAG(
    'weather_etl_pipeline',
    default_args=default_args,
    description='A DAG for weather data ETL pipeline',
    schedule_interval=timedelta(hours=1),
    catchup=False
)

# Define the tasks
extract_task = PythonOperator(
    task_id='extract_weather_data',
    python_callable=extract_weather_data,
    dag=dag,
)

transform_task = PythonOperator(
    task_id='transform_weather_data',
    python_callable=transform_weather_data,
    dag=dag,
)

load_task = PythonOperator(
    task_id='load_weather_data',
    python_callable=load_weather_data,
    dag=dag,
)

# Set task dependencies
extract_task >> transform_task >> load_task
