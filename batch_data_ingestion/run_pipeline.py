import os
import sys

# Add the src directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.etl_pipeline import ETLPipeline

if __name__ == "__main__":
    # List of tables to process
    tables_to_process = [
        "customers",
        "products",
        "orders",
        "order_items",
        "inventory_locations",
        "product_inventory"
    ]
    
    # Run the ETL pipeline
    with ETLPipeline() as pipeline:
        pipeline.run_pipeline(tables_to_process)
