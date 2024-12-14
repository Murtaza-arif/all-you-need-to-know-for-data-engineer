# Real-Time Data Streaming Pipeline

This project demonstrates a scalable real-time data streaming pipeline using Apache Kafka and Apache Cassandra. It generates fake order data, streams it through multiple Kafka partitions, processes it in parallel, and stores it in Cassandra.

## Architecture

### Producer
- Generates fake order data with product categories
- Uses partition keys based on product categories
- Distributes messages across 3 Kafka partitions
- Includes retry logic and error handling

### Consumer
- Parallel processing with multiple consumers (one per partition)
- Thread-based consumer groups
- Efficient data processing and storage
- Built-in monitoring and statistics

## Prerequisites

- Docker and Docker Compose
- Python 3.7+
- libev (for Cassandra driver)

## Setup

1. Start the Docker containers for Kafka and Cassandra:
   ```bash
   docker-compose up -d
   ```

2. Wait for the services to be ready:
   - Kafka will be available on localhost:9092
   - Cassandra will be available on localhost:9042
   - Check status with:
     ```bash
     docker-compose ps
     ```

3. Set up the Python environment:
   ```bash
   # Make the setup script executable
   chmod +x setup.sh
   
   # Run the setup script
   ./setup.sh
   
   # Activate the virtual environment
   source venv/bin/activate
   ```

## Running the Pipeline

1. Start the producer to create the topic and begin sending messages:
   ```bash
   python producer.py
   ```

2. In another terminal, activate the environment and start the consumer:
   ```bash
   source venv/bin/activate
   python consumer.py
   ```

## Components

- `docker-compose.yml`: Defines the Kafka and Cassandra infrastructure
- `producer.py`: Generates and sends order data with partition keys
- `consumer.py`: Parallel processing of orders from multiple partitions
- `requirements.txt`: Python dependencies
- `setup.sh`: Environment setup script

## Data Flow

1. Producer generates fake orders with product categories
2. Orders are distributed across 3 Kafka partitions based on product
3. Multiple consumers process messages in parallel
4. Processed data is stored in Cassandra with partition information
5. Statistics are collected and displayed for monitoring

## Cassandra Schema

```sql
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
```

### Schema Design
- Partition key: partition (for even distribution)
- Clustering key: order_id (for uniqueness)
- Optimized for queries by partition

## Monitoring

The consumer provides real-time monitoring:
- Order processing status per partition
- Partition statistics (order counts)
- Sample orders from each partition
- Error logging and tracking

## Stopping the Pipeline

1. Stop the consumer first (Ctrl+C):
   - This will display final partition statistics
   - Shows sample orders from each partition

2. Stop the producer (Ctrl+C)

3. Stop the Docker containers:
   ```bash
   docker-compose down
   ```

## Troubleshooting

1. If Kafka is not accessible:
   - Check container status: `docker-compose ps`
   - View Kafka logs: `docker-compose logs broker`
   - Ensure topic creation was successful

2. If Cassandra is not accessible:
   - Check Cassandra logs: `docker-compose logs cassandra`
   - Wait for Cassandra to fully initialize
   - Verify schema creation

3. If consumers are not processing:
   - Check consumer group assignments
   - Verify partition distribution
   - Review error logs

## Performance Considerations

- Each partition is processed by a dedicated consumer
- Cassandra table is partitioned for optimal read/write performance
- Batch processing can be enabled for higher throughput
- Connection pooling is used for better resource utilization

## Future Improvements

1. Add monitoring dashboard
2. Implement back-pressure handling
3. Add data validation and schema evolution
4. Implement exactly-once processing
5. Add metrics collection and alerting
