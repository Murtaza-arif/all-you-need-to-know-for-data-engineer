from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.dummy import DummyOperator
from airflow.operators.subdag import SubDagOperator
from airflow.exceptions import AirflowException
from airflow.utils.task_group import TaskGroup
from crypto_processing_subdag import create_processing_subdag
import websocket
import json
import logging
import threading
import queue
import time
from collections import defaultdict

# Configure logging
logger = logging.getLogger(__name__)

# Constants
CRYPTO_SYMBOLS = ['btcusdt', 'ethusdt', 'bnbusdt']
BINANCE_WS_URL = "wss://stream.binance.com:9443/ws"
DATA_COLLECTION_TIME = 60  # Collect data for 60 seconds
MIN_DATA_POINTS = 5  # Minimum number of data points required

class CryptoDataCollector:
    def __init__(self, symbol):
        self.symbol = symbol
        self.data_queue = queue.Queue()
        self.ws = None
        self.should_stop = False
        self.connected = threading.Event()
        
    def on_message(self, ws, message):
        """Handle incoming WebSocket messages"""
        try:
            data = json.loads(message)
            if data.get('e') == 'trade':
                symbol = data['s'].lower()
                if symbol == self.symbol:
                    trade_data = {
                        'symbol': symbol,
                        'price': float(data['p']),
                        'volume': float(data['q']),
                        'timestamp': datetime.fromtimestamp(data['T']/1000.0).isoformat()
                    }
                    self.data_queue.put(trade_data)
                    logger.debug(f"Received trade data for {symbol}")
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
    
    def on_error(self, ws, error):
        """Handle WebSocket errors"""
        logger.error(f"WebSocket error: {str(error)}")
        self.connected.clear()
    
    def on_close(self, ws, close_status_code, close_msg):
        """Handle WebSocket connection close"""
        logger.info(f"WebSocket connection closed: {close_status_code} - {close_msg}")
        self.connected.clear()
    
    def on_open(self, ws):
        """Handle WebSocket connection open"""
        logger.info(f"WebSocket connection opened for {self.symbol}")
        # Subscribe to trade stream
        subscribe_message = {
            "method": "SUBSCRIBE",
            "params": [f"{self.symbol}@trade"],
            "id": 1
        }
        ws.send(json.dumps(subscribe_message))
        self.connected.set()
    
    def connect(self):
        """Establish WebSocket connection"""
        websocket.enableTrace(True)
        self.ws = websocket.WebSocketApp(
            BINANCE_WS_URL,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close,
            on_open=self.on_open
        )
    
    def collect_data(self, duration=DATA_COLLECTION_TIME):
        """Collect data for specified duration"""
        try:
            logger.info(f"Starting data collection for {self.symbol}")
            
            # Start WebSocket connection
            self.connect()
            
            # Run WebSocket in a separate thread
            ws_thread = threading.Thread(target=self.ws.run_forever)
            ws_thread.daemon = True
            ws_thread.start()
            
            # Wait for connection to establish
            if not self.connected.wait(timeout=10):
                raise AirflowException(f"Timeout waiting for WebSocket connection for {self.symbol}")
            
            # Collect data
            collected_data = []
            start_time = time.time()
            last_data_time = start_time
            
            while time.time() - start_time < duration:
                try:
                    data = self.data_queue.get(timeout=1)
                    collected_data.append(data)
                    last_data_time = time.time()
                    
                    # Check for data timeout
                    if time.time() - last_data_time > 10:
                        logger.warning(f"No data received for {self.symbol} in the last 10 seconds")
                except queue.Empty:
                    continue
            
            # Clean up
            self.should_stop = True
            if self.ws:
                self.ws.close()
            
            # Verify data
            if len(collected_data) < MIN_DATA_POINTS:
                raise AirflowException(
                    f"Insufficient data points for {self.symbol}: {len(collected_data)} < {MIN_DATA_POINTS}"
                )
            
            logger.info(f"Successfully collected {len(collected_data)} data points for {self.symbol}")
            return collected_data
            
        except Exception as e:
            logger.error(f"Error collecting data for {self.symbol}: {str(e)}")
            if self.ws:
                self.ws.close()
            raise AirflowException(f"Failed to collect data for {self.symbol}: {str(e)}")

def collect_crypto_data(symbol, **context):
    """Task function to collect crypto data"""
    try:
        collector = CryptoDataCollector(symbol)
        data = collector.collect_data()
        
        # Store data in XCom
        context['task_instance'].xcom_push(
            key=f'market_data_{symbol}',
            value=data
        )
        
        return f"Collected {len(data)} data points for {symbol}"
    
    except Exception as e:
        logger.error(f"Error in collect_crypto_data for {symbol}: {str(e)}")
        raise AirflowException(f"Failed to collect data for {symbol}: {str(e)}")

# Default arguments for the DAG
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 12, 14),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=1),
}

# Create the DAG
dag = DAG(
    'crypto_realtime_pipeline',
    default_args=default_args,
    description='A DAG for real-time cryptocurrency data processing with SubDAGs',
    schedule_interval=timedelta(minutes=5),
    catchup=False
)

# Start task
start_task = DummyOperator(
    task_id='start_pipeline',
    dag=dag
)

# Create tasks for each symbol
for symbol in CRYPTO_SYMBOLS:
    collect_task = PythonOperator(
        task_id=f'collect_market_data_{symbol}',
        python_callable=collect_crypto_data,
        op_kwargs={'symbol': symbol},
        dag=dag
    )
    
    process_task = SubDagOperator(
        task_id=f'process_market_data_{symbol}',
        subdag=create_processing_subdag(
            parent_dag_id='crypto_realtime_pipeline',
            child_dag_id=f'process_market_data_{symbol}',
            crypto_symbol=symbol,
            args=default_args
        ),
        dag=dag
    )
    
    # Set task dependencies
    start_task >> collect_task >> process_task

# End task
end_task = DummyOperator(
    task_id='end_pipeline',
    dag=dag
)

# Connect all symbol groups to end task
for symbol in CRYPTO_SYMBOLS:
    dag.get_task(f'process_market_data_{symbol}') >> end_task
