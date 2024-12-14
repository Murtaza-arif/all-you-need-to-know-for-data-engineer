import os
from datetime import datetime
from dotenv import load_dotenv
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
import boto3
import atexit
from .advanced_transformations import create_complex_inventory_view, get_business_insights

# Load environment variables
load_dotenv()

class ETLPipeline:
    def __init__(self):
        self.spark = None
        self._initialize_spark()
        # Register cleanup on program exit
        atexit.register(self.cleanup)

    def _initialize_spark(self):
        """Initialize Spark session with configurations"""
        # Get the project root directory (parent of src directory)
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Initialize Spark session with local mode configuration
        jars = [
            os.path.join(project_root, "lib/mysql-connector-j-8.0.33.jar"),
            os.path.join(project_root, "lib/hadoop-aws-3.3.4.jar"),
            os.path.join(project_root, "lib/aws-java-sdk-bundle-1.12.262.jar"),
            os.path.join(project_root, "lib/hadoop-common-3.3.4.jar"),
            os.path.join(project_root, "lib/woodstox-core-6.4.0.jar"),
            os.path.join(project_root, "lib/stax2-api-4.2.1.jar"),
            os.path.join(project_root, "lib/commons-configuration2-2.9.0.jar"),
            os.path.join(project_root, "lib/commons-lang3-3.12.0.jar"),
            os.path.join(project_root, "lib/re2j-1.7.jar")
        ]
        
        os.environ['SPARK_LOCAL_IP'] = '127.0.0.1'  # Set Spark to bind to localhost
        
        try:
            self.spark = SparkSession.builder \
                .master("local[*]") \
                .appName("MySQL to S3 ETL") \
                .config("spark.jars", ",".join(jars)) \
                .config("spark.driver.extraClassPath", ":".join(jars)) \
                .config("spark.executor.extraClassPath", ":".join(jars)) \
                .config("spark.hadoop.fs.s3a.aws.credentials.provider", "org.apache.hadoop.fs.s3a.SimpleAWSCredentialsProvider") \
                .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
                .config("spark.hadoop.fs.s3a.endpoint", f"s3.{os.getenv('AWS_REGION')}.amazonaws.com") \
                .config("spark.hadoop.fs.s3a.access.key", os.getenv("AWS_ACCESS_KEY_ID")) \
                .config("spark.hadoop.fs.s3a.secret.key", os.getenv("AWS_SECRET_ACCESS_KEY")) \
                .config("spark.sql.execution.arrow.pyspark.enabled", "true") \
                .config("spark.sql.execution.arrow.maxRecordsPerBatch", "10000") \
                .getOrCreate()
        except Exception as e:
            print(f"Failed to initialize Spark session: {str(e)}")
            self.cleanup()
            raise

        # MySQL connection properties
        self.mysql_properties = {
            "driver": "com.mysql.cj.jdbc.Driver",
            "url": f"jdbc:mysql://{os.getenv('MYSQL_HOST')}:{os.getenv('MYSQL_PORT')}/{os.getenv('MYSQL_DATABASE')}",
            "user": os.getenv("MYSQL_USER"),
            "password": os.getenv("MYSQL_PASSWORD")
        }

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.cleanup()

    def cleanup(self):
        """Clean up resources"""
        if self.spark:
            try:
                self.spark.stop()
                print("Spark session stopped successfully")
            except Exception as e:
                print(f"Error stopping Spark session: {str(e)}")
            finally:
                self.spark = None

    def extract_from_mysql(self, table_name):
        """Extract data from MySQL table"""
        print(f"Extracting data from {table_name}...")
        return self.spark.read \
            .format("jdbc") \
            .options(**self.mysql_properties) \
            .option("dbtable", table_name) \
            .load()

    def transform_data(self, df, table_name):
        """Apply any necessary transformations"""
        print(f"Transforming data for {table_name}...")
        # Add timestamp column for tracking
        df = df.withColumn("etl_timestamp", F.current_timestamp())
        return df

    def load_to_s3(self, df, table_name):
        """Load DataFrame to S3 and local storage"""
        try:
            current_date = datetime.now().strftime('%Y-%m-%d')
            
            # Save to S3
            s3_path = f"s3a://{os.getenv('S3_BUCKET')}/data/{table_name}/{current_date}"
            df.write \
                .mode("overwrite") \
                .parquet(s3_path)
            
            # Save locally
            local_path = f"data/{table_name}/{current_date}"
            os.makedirs(local_path, exist_ok=True)
            df.write \
                .mode("overwrite") \
                .parquet(local_path)
            
            print(f"Data successfully loaded to {s3_path} and {local_path}")
            
        except Exception as e:
            print(f"Error loading data to storage: {str(e)}")
            raise

    def process_data(self):
        """Process data from MySQL and create complex analytics views"""
        try:
            # Create complex views using Arrow-optimized UDFs
            create_complex_inventory_view(self.spark)
            
            # Get business insights using the complex views
            insights_df = get_business_insights(self.spark)
            
            current_date = datetime.now().strftime('%Y-%m-%d')
            
            # Save insights to S3
            s3_path = f"s3a://{os.getenv('S3_BUCKET')}/business_insights/{current_date}"
            insights_df.write \
                .mode("overwrite") \
                .parquet(s3_path)
            
            # Save insights locally
            local_path = f"data/business_insights/{current_date}"
            os.makedirs(local_path, exist_ok=True)
            insights_df.write \
                .mode("overwrite") \
                .parquet(local_path)
            
            print(f"Successfully processed data and saved insights to {s3_path} and {local_path}")
            
        except Exception as e:
            print(f"Error processing data: {str(e)}")
            raise

    def run_pipeline(self, tables):
        """Run the complete ETL pipeline for specified tables"""
        try:
            # First load all tables to S3
            for table in tables:
                # Extract
                df = self.extract_from_mysql(table)
                
                # Transform
                df_transformed = self.transform_data(df, table)
                
                # Load
                self.load_to_s3(df_transformed, table)
            
            # Then process the data to generate insights
            self.process_data()
                
            print("ETL pipeline completed successfully!")
            
        except Exception as e:
            print(f"Error in ETL pipeline: {str(e)}")
            raise

if __name__ == "__main__":
    # List of tables to process
    tables_to_process = [
        "customers",
        "orders",
        "products"
    ]
    
    # Initialize and run pipeline using context manager
    try:
        with ETLPipeline() as pipeline:
            pipeline.run_pipeline(tables_to_process)
    except Exception as e:
        print(f"Pipeline failed: {str(e)}")
        exit(1)
