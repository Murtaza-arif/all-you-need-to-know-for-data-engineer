#!/bin/bash

# Load environment variables
source .env

# Get the absolute path of the current directory
CURRENT_DIR=$(pwd)

# Download JARs locally if they don't exist
if [ ! -d "lib" ] || [ -z "$(ls -A lib)" ]; then
    echo "Downloading JARs locally..."
    chmod +x download_jars.sh
    ./download_jars.sh
fi

# Copy JARs to containers
echo "Copying JARs to containers..."
for container in spark-cluster-spark-master-1 spark-cluster-spark-worker-1-1 spark-cluster-spark-worker-2-1; do
    echo "Copying JARs to $container..."
    # Create the directories if they don't exist
    docker exec $container mkdir -p /opt/bitnami/spark/lib
    docker exec $container mkdir -p /opt/spark-apps/src
    docker exec $container mkdir -p /opt/spark/jars
    
    # Copy MySQL connector JAR specifically
    docker cp lib/mysql-connector-java-8.0.30.jar $container:/opt/bitnami/spark/lib/
    docker cp lib/* $container:/opt/spark/jars/
    
    # Copy Python files
    docker cp src/* $container:/opt/spark-apps/src/
    docker cp run_pipeline.py $container:/opt/spark-apps/
    
    # Install Python dependencies
    docker exec $container pip install python-dotenv boto3 mysql-connector-python pandas numpy pyspark packaging pyarrow>=4.0.0
done

# Submit the Spark job
docker exec \
    -e "MYSQL_HOST=etl_mysql" \
    -e "MYSQL_PORT=3306" \
    -e "MYSQL_DATABASE=ecommerce" \
    -e "MYSQL_USER=etl_user" \
    -e "MYSQL_PASSWORD=etl_password" \
    -e "AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}" \
    -e "AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}" \
    -e "AWS_REGION=${AWS_REGION}" \
    spark-cluster-spark-master-1 spark-submit \
    --master spark://spark-master:7077 \
    --driver-memory 4g \
    --executor-memory 4g \
    --driver-class-path "/opt/bitnami/spark/lib/mysql-connector-java-8.0.30.jar" \
    --jars "/opt/spark/jars/*" \
    --conf "spark.executor.extraClassPath=/opt/bitnami/spark/lib/mysql-connector-java-8.0.30.jar" \
    --conf "spark.driver.extraClassPath=/opt/bitnami/spark/lib/mysql-connector-java-8.0.30.jar" \
    /opt/spark-apps/run_pipeline.py
