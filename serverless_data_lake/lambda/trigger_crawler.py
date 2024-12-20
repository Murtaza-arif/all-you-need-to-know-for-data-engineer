import os
import boto3
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event, context):
    """
    Lambda function to trigger Glue crawler
    """
    crawler_name = os.environ['CRAWLER_NAME']
    glue_client = boto3.client('glue')
    
    try:
        # Start the crawler
        response = glue_client.start_crawler(Name=crawler_name)
        logger.info(f"Successfully started crawler {crawler_name}")
        return {
            'statusCode': 200,
            'body': f"Started crawler {crawler_name}"
        }
    except glue_client.exceptions.CrawlerRunningException:
        logger.info(f"Crawler {crawler_name} is already running")
        return {
            'statusCode': 200,
            'body': f"Crawler {crawler_name} is already running"
        }
    except Exception as e:
        logger.error(f"Error starting crawler {crawler_name}: {str(e)}")
        raise
