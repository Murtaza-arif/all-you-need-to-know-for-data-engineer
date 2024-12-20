import json
import os
import boto3
from datetime import datetime

def handler(event, context):
    """
    Lambda function to process files uploaded to the raw S3 bucket
    """
    s3_client = boto3.client('s3')
    
    # Get the source bucket and key
    source_bucket = event['Records'][0]['s3']['bucket']['name']
    source_key = event['Records'][0]['s3']['object']['key']
    
    # Get the target bucket from environment variables
    target_bucket = os.environ['CLEANED_BUCKET']
    
    try:
        # Get the object from the source bucket
        response = s3_client.get_object(Bucket=source_bucket, Key=source_key)
        content = response['Body'].read().decode('utf-8')
        
        # Add processing timestamp
        metadata = {
            'processed_timestamp': datetime.utcnow().isoformat(),
            'source_bucket': source_bucket,
            'source_key': source_key
        }
        
        # Upload to cleaned bucket with metadata
        s3_client.put_object(
            Bucket=target_bucket,
            Key=f"processed/{source_key}",
            Body=content,
            Metadata=metadata
        )
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'File processed successfully',
                'source': f"{source_bucket}/{source_key}",
                'destination': f"{target_bucket}/processed/{source_key}"
            })
        }
        
    except Exception as e:
        print(f"Error processing file {source_key}: {str(e)}")
        raise
