from kafka import KafkaProducer
from kafka.admin import KafkaAdminClient, NewTopic
from faker import Faker
import json
from datetime import datetime
import time
import logging
from decimal import Decimal
import hashlib

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
TOPIC_NAME = 'orders'
NUM_PARTITIONS = 3
REPLICATION_FACTOR = 1

# Initialize Faker and Kafka Admin
fake = Faker()

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)
        return super(DecimalEncoder, self).default(obj)

def create_topic():
    """Create Kafka topic with multiple partitions if it doesn't exist"""
    try:
        admin_client = KafkaAdminClient(bootstrap_servers=['localhost:9092'])
        
        # Check if topic exists
        existing_topics = admin_client.list_topics()
        if TOPIC_NAME not in existing_topics:
            topic = NewTopic(
                name=TOPIC_NAME,
                num_partitions=NUM_PARTITIONS,
                replication_factor=REPLICATION_FACTOR
            )
            admin_client.create_topics([topic])
            logger.info(f"Created topic {TOPIC_NAME} with {NUM_PARTITIONS} partitions")
        else:
            logger.info(f"Topic {TOPIC_NAME} already exists")
            
    except Exception as e:
        logger.error(f"Error creating topic: {e}")
    finally:
        admin_client.close()

def get_partition_key(order):
    """Generate a partition key based on the product category"""
    # Use product name as the partition key
    return order['product'].encode('utf-8')

# Initialize Kafka Producer with retry settings and partitioner
producer = KafkaProducer(
    bootstrap_servers=['localhost:9092'],
    value_serializer=lambda x: json.dumps(x, cls=DecimalEncoder).encode('utf-8'),
    partitioner=lambda key, all_partitions, available: hash(key) % len(all_partitions),
    retries=5,
    retry_backoff_ms=1000
)

def generate_order():
    """Generate a fake order"""
    # Generate random product category
    product_categories = ['Electronics', 'Clothing', 'Food', 'Books', 'Home']
    category = fake.random_element(product_categories)
    
    return {
        'order_id': fake.uuid4(),
        'customer_name': fake.name(),
        'product': f"{category}_{fake.word()}",
        'category': category,
        'quantity': fake.random_int(min=1, max=100),
        'price': str(Decimal(str(fake.random_number(digits=2) / 100)).quantize(Decimal('0.01'))),
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

def stream_orders():
    """Stream fake orders to Kafka topic"""
    try:
        while True:
            order = generate_order()
            partition_key = get_partition_key(order)
            
            try:
                # Send message with partition key
                future = producer.send(
                    TOPIC_NAME,
                    key=partition_key,
                    value=order
                )
                # Wait for message to be sent
                record_metadata = future.get(timeout=10)
                
                logger.info(f"Sent order to partition {record_metadata.partition}: {order}")
                producer.flush()
                time.sleep(2)  # Stream a new order every 2 seconds
                
            except Exception as e:
                logger.error(f"Error sending message: {e}")
                time.sleep(1)  # Wait before retrying
            
    except KeyboardInterrupt:
        logger.info("Stopping order stream...")
        producer.close()
        
if __name__ == "__main__":
    logger.info("Creating topic with multiple partitions...")
    create_topic()
    
    logger.info("Starting order stream...")
    stream_orders()
