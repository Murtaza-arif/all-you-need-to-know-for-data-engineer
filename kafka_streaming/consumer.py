import gevent.monkey
gevent.monkey.patch_all()

from kafka import KafkaConsumer, TopicPartition
from cassandra.cluster import Cluster, ExecutionProfile, EXEC_PROFILE_DEFAULT
from cassandra.policies import DCAwareRoundRobinPolicy, TokenAwarePolicy
from cassandra.io.geventreactor import GeventConnection
import json
import logging
import time
from datetime import datetime
from decimal import Decimal
from concurrent.futures import ThreadPoolExecutor
import threading

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
TOPIC_NAME = 'orders'
NUM_CONSUMERS = 3  # One consumer per partition

# Initialize Cassandra connection with retry logic
def connect_to_cassandra():
    max_retries = 5
    retry_delay = 5  # seconds
    
    profile = ExecutionProfile(
        load_balancing_policy=TokenAwarePolicy(DCAwareRoundRobinPolicy()),
        request_timeout=60
    )
    
    for i in range(max_retries):
        try:
            # Use GeventConnection for Python 3.12 compatibility
            cluster = Cluster(
                ['localhost'],
                port=9042,
                execution_profiles={EXEC_PROFILE_DEFAULT: profile},
                connection_class=GeventConnection
            )
            session = cluster.connect()
            logger.info("Successfully connected to Cassandra")
            return cluster, session
        except Exception as e:
            if i < max_retries - 1:
                logger.error(f"Failed to connect to Cassandra, retrying in {retry_delay} seconds... Error: {e}")
                time.sleep(retry_delay)
            else:
                logger.error(f"Failed to connect to Cassandra after {max_retries} attempts")
                raise

# Initialize connection
cluster, session = connect_to_cassandra()

# Create keyspace if it doesn't exist
session.execute("""
    CREATE KEYSPACE IF NOT EXISTS order_db
    WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1}
""")

# Use the keyspace
session.set_keyspace('order_db')

# Drop existing table if it exists
session.execute("""
    DROP TABLE IF EXISTS orders
""")

# Create table with updated schema
session.execute("""
    CREATE TABLE orders (
        order_id text,
        partition int,
        customer_name text,
        product text,
        category text,
        quantity int,
        price decimal,
        timestamp timestamp,
        total_amount decimal,
        PRIMARY KEY ((partition), order_id)
    )
""")
logger.info("Created orders table with updated schema")

# Prepare the insert statement
insert_statement = session.prepare("""
    INSERT INTO orders (
        order_id, partition, customer_name, product, category, quantity, 
        price, timestamp, total_amount
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
""")

def process_order(order, partition):
    """Process the order data"""
    try:
        # Convert price to Decimal
        price = Decimal(str(order['price']))
        quantity = int(order['quantity'])
        
        # Calculate total amount
        total_amount = price * quantity
        
        # Update order with processed values
        order['price'] = price
        order['total_amount'] = total_amount
        order['partition'] = partition
        return order
    except Exception as e:
        logger.error(f"Error processing order: {e}")
        logger.error(f"Order data: {order}")
        raise

def store_order(order):
    """Store the processed order in Cassandra"""
    try:
        # Convert timestamp string to datetime object
        timestamp = datetime.strptime(order['timestamp'], '%Y-%m-%d %H:%M:%S')
        
        # Convert price and total_amount to Decimal
        price = Decimal(str(order['price']))
        total_amount = Decimal(str(order['total_amount']))
        
        # Execute the prepared statement
        session.execute(insert_statement, (
            order['order_id'],
            order['partition'],
            order['customer_name'],
            order['product'],
            order['category'],
            order['quantity'],
            price,
            timestamp,
            total_amount
        ))
        logger.info(f"Stored order {order['order_id']} from partition {order['partition']} in Cassandra")
    except Exception as e:
        logger.error(f"Error storing order in Cassandra: {e}")
        logger.error(f"Order data: {order}")

def consume_partition(partition):
    """Consume messages from a specific partition"""
    consumer = KafkaConsumer(
        bootstrap_servers=['localhost:9092'],
        value_deserializer=lambda x: json.loads(x.decode('utf-8')),
        auto_offset_reset='earliest',
        enable_auto_commit=True,
        group_id=f'order_processing_group_{partition}',
        max_poll_interval_ms=300000,  # 5 minutes
        max_poll_records=100
    )
    
    # Assign specific partition to this consumer
    topic_partition = TopicPartition(TOPIC_NAME, partition)
    consumer.assign([topic_partition])
    
    logger.info(f"Started consumer for partition {partition}")
    
    try:
        for message in consumer:
            try:
                order = message.value
                logger.info(f"Received order on partition {partition}: {order}")
                
                # Process the order
                processed_order = process_order(order, partition)
                
                # Store in Cassandra
                store_order(processed_order)
                
            except Exception as e:
                logger.error(f"Error processing message on partition {partition}: {e}")
                logger.error(f"Message value: {message.value}")
                continue
            
    except Exception as e:
        logger.error(f"Error in consumer for partition {partition}: {e}")
    finally:
        consumer.close()

def get_orders_by_partition(partition):
    """Retrieve orders from a specific partition"""
    try:
        query = """
            SELECT * FROM orders 
            WHERE partition = ?
            LIMIT 10
        """
        rows = session.execute(query, [partition])
        for row in rows:
            logger.info(f"Order from partition {partition}: {row}")
    except Exception as e:
        logger.error(f"Error querying partition {partition}: {e}")

def show_partition_stats():
    """Show statistics for each partition"""
    try:
        for partition in range(NUM_CONSUMERS):
            query = "SELECT COUNT(*) FROM orders WHERE partition = ?"
            count = session.execute(query, [partition]).one().count
            logger.info(f"Partition {partition} has {count} orders")
    except Exception as e:
        logger.error(f"Error getting partition stats: {e}")

def start_consumers():
    """Start multiple consumers for different partitions"""
    logger.info("Starting consumers for multiple partitions...")
    
    with ThreadPoolExecutor(max_workers=NUM_CONSUMERS) as executor:
        futures = [executor.submit(consume_partition, i) for i in range(NUM_CONSUMERS)]
        
        try:
            # Wait for all consumers to complete
            for future in futures:
                future.result()
        except KeyboardInterrupt:
            logger.info("Stopping all consumers...")
            # Show final statistics
            show_partition_stats()
            for partition in range(NUM_CONSUMERS):
                get_orders_by_partition(partition)
        except Exception as e:
            logger.error(f"Unexpected error in consumer thread: {e}")
        finally:
            cluster.shutdown()

if __name__ == "__main__":
    start_consumers()
