# Batch Data Ingestion Pipeline

A robust ETL pipeline that extracts data from MySQL, performs complex transformations using PySpark, and loads the results into Amazon S3. The pipeline runs on a distributed Spark cluster managed by Docker Compose.

## Features

- Distributed Spark cluster with master and worker nodes
- Containerized MySQL database
- Extracts data from MySQL tables
- Performs complex inventory analytics using PySpark UDFs
- Calculates business insights including:
  - Inventory scores based on utilization and freshness
  - Customer order patterns and peak hours
  - Sales analytics and metrics
- Stores processed data in S3 in Parquet format

## Prerequisites

- Docker and Docker Compose
- AWS Account with S3 access

## Project Structure

```
batch_data_ingestion/
├── src/
│   ├── __init__.py
│   ├── etl_pipeline.py        # Main ETL pipeline implementation
│   └── advanced_transformations.py  # Complex data transformations
├── init/
│   └── 02_additional_tables.sql     # SQL initialization scripts
├── spark-cluster/            # Spark cluster configuration
│   ├── docker-compose.yml    # Defines Spark master and worker services
│   └── spark-defaults.conf   # Spark configuration parameters
├── docker-compose.yml        # MySQL service configuration
├── download_jars.sh         # Downloads required JARs (MySQL connector, etc.)
├── submit-job.sh            # Script to submit Spark job to the cluster
├── requirements.txt         # Python dependencies
└── .env                     # Environment variables
```

## Spark Cluster Setup

The Spark cluster consists of one master node and two worker nodes, all running in Docker containers. The setup is defined in `spark-cluster/docker-compose.yml`:

```yaml
services:
  spark-master:
    image: bitnami/spark:3.4.1
    environment:
      - SPARK_MODE=master
    ports:
      - "8080:8080"
      - "7077:7077"
    networks:
      - etl_network

  spark-worker-1:
    image: bitnami/spark:3.4.1
    environment:
      - SPARK_MODE=worker
      - SPARK_MASTER_URL=spark://spark-master:7077
    networks:
      - etl_network

  spark-worker-2:
    image: bitnami/spark:3.4.1
    environment:
      - SPARK_MODE=worker
      - SPARK_MASTER_URL=spark://spark-master:7077
    networks:
      - etl_network
```

### Starting the Cluster

1. Start MySQL container:
   ```bash
   docker-compose up -d
   ```

2. Start Spark cluster:
   ```bash
   cd spark-cluster
   docker-compose up -d
   ```

3. Verify cluster status:
   ```bash
   docker ps
   ```
   You should see three containers running: spark-master, spark-worker-1, and spark-worker-2

## Job Submission

The `submit-job.sh` script handles:
1. Downloading required JARs (MySQL connector)
2. Copying files to Spark containers
3. Setting up environment variables
4. Submitting the Spark job

### Configuration

Create a `.env` file with:
```env
MYSQL_HOST=etl_mysql
MYSQL_PORT=3306
MYSQL_DATABASE=ecommerce
MYSQL_USER=etl_user
MYSQL_PASSWORD=etl_password
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=your_aws_region
```

### Running the Job

1. Download required JARs:
   ```bash
   ./download_jars.sh
   ```

2. Submit the Spark job:
   ```bash
   ./submit-job.sh
   ```

The job submission script:
- Copies MySQL connector and other JARs to all Spark nodes
- Copies Python source files to the containers
- Sets up environment variables for MySQL and AWS
- Submits the job with proper memory and configuration settings

### Monitoring

- Spark UI: http://localhost:8080
- View logs:
  ```bash
  docker logs spark-cluster-spark-master-1
  docker logs spark-cluster-spark-worker-1-1
  docker logs spark-cluster-spark-worker-2-1
  ```

## Troubleshooting

### Common Issues

1. MySQL Connection Issues
   - Verify MySQL container is running: `docker ps`
   - Check MySQL logs: `docker logs etl_mysql`
   - Ensure both MySQL and Spark are on `etl_network`:
     ```bash
     docker network inspect etl_network
     ```

2. Spark Job Failures
   - Check Spark master logs:
     ```bash
     docker logs spark-cluster-spark-master-1
     ```
   - Verify JARs are copied:
     ```bash
     docker exec spark-cluster-spark-master-1 ls /opt/bitnami/spark/lib/
     ```
   - Check environment variables:
     ```bash
     docker exec spark-cluster-spark-master-1 env | grep MYSQL
     ```

## Usage

1. Ensure your MySQL database is running and contains the required tables
2. Configure your environment variables in `.env`
3. Run the pipeline:
   ```bash
   python run_pipeline.py
   ```

The pipeline will:
1. Extract data from specified MySQL tables
2. Apply transformations including:
   - Inventory score calculation
   - Order pattern analysis
   - Business insights generation
3. Save processed data to S3 in Parquet format

## Data Transformations

### Inventory Analytics
- Calculates inventory scores based on:
  - Current quantity vs capacity
  - Data freshness (time since last update)
  - Optimal utilization targeting 50% capacity

### Order Analytics
- Analyzes customer order patterns:
  - Total orders and spending
  - Average order value
  - Peak order hours
  - Average days between orders

## Advanced Transformations

The `advanced_transformations.py` module implements complex data analytics using PySpark and Pandas UDFs (User Defined Functions). Here's a detailed breakdown of each transformation:

### 1. Inventory Analytics

#### Inventory Score Calculation
The `calculate_inventory_score` UDF computes a score (0-100) for each inventory item based on:
```python
score = (1 - |utilization_ratio - 0.5| * 2) * 100 - days_since_update * 2
```

Components:
- **Utilization Ratio**: `quantity / capacity`
  - Optimal ratio is 0.5 (50% capacity)
  - Scores decrease as ratio moves away from 0.5
  - Prevents both understocking and overstocking
- **Data Freshness**: `days_since_update * 2`
  - Penalizes old inventory data
  - Each day reduces score by 2 points
  - Encourages regular inventory updates

#### Complex Inventory View
Creates a temporary view combining:
- Basic inventory data (quantity, capacity)
- Warehouse location details
- Calculated inventory scores
- Product information

### 2. Order Analytics

#### Customer Order Patterns
Analyzes customer behavior through SQL aggregations:

1. **Order Frequency**
   - Total orders per customer
   - Average days between orders
   ```sql
   (UNIX_TIMESTAMP(MAX(order_date)) - UNIX_TIMESTAMP(MIN(order_date))) 
   / (86400.0 * GREATEST(COUNT(*) - 1, 1)) as avg_days_between_orders
   ```

2. **Spending Patterns**
   - Total amount spent
   - Average order value
   - Identifies high-value customers

3. **Temporal Analysis**
   - Peak order hours
   - Order distribution across time
   - Helps optimize inventory and staffing

### 3. Business Insights Generation

The `get_business_insights` function combines both analytics to create actionable insights:

1. **Inventory Optimization**
   - Identifies products needing restocking
   - Highlights overstocked items
   - Suggests optimal inventory levels

2. **Customer Segmentation**
   - Groups customers by order frequency
   - Analyzes spending patterns
   - Identifies VIP customers

3. **Operational Efficiency**
   - Warehouse utilization metrics
   - Peak hour analysis
   - Inventory turnover rates

### Implementation Details

1. **Performance Optimization**
   - Uses Pandas UDFs for vectorized operations
   - Leverages Spark SQL for complex aggregations
   - Minimizes data movement between Spark and Python

2. **Data Type Handling**
   - Explicit casting for numeric operations
   - Proper timestamp handling for date calculations
   - Null value management

3. **Error Handling**
   - Graceful handling of missing data
   - Division by zero prevention
   - Data type validation

### Output Format

The transformed data is saved to S3 in Parquet format with the following structure:
```
s3://bucket/
    └── business_insights/
        └── YYYY-MM-DD/
            ├── inventory_analytics/
            │   └── part-*.parquet
            └── order_analytics/
                └── part-*.parquet
```

Each Parquet file contains:
- All calculated metrics and scores
- Temporal information (timestamps)
- Reference data (product, customer, warehouse info)
- Source table linkage information

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License.
