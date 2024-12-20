# Serverless Data Lake Architecture

This project implements a serverless data lake architecture on AWS, providing a scalable and cost-effective solution for data storage, processing, and analytics.

## Architecture Overview

The data lake is organized into three main layers:
1. **Raw Layer**: Initial landing zone for raw data
2. **Cleaned Layer**: Stores validated and cleaned data
3. **Curated Layer**: Contains transformed, business-ready data

## Resources Created

### Storage
- **S3 Buckets**:
  - Raw data bucket (`{project-name}-raw-{environment}`)
  - Cleaned data bucket (`{project-name}-cleaned-{environment}`)
  - Curated data bucket (`{project-name}-curated-{environment}`)
  - All buckets have versioning enabled for data protection

### Data Processing
- **AWS Lambda**:
  - File processing function triggered by S3 uploads
  - Handles initial data validation and transformation

- **AWS Glue**:
  - Data Catalog for metadata management
  - ETL job for data curation
  - Crawler for schema discovery

### Analytics
- **Amazon Athena**:
  - Custom workgroup for SQL queries
  - Predefined queries for common analytics
  - Query results stored in curated layer

### IAM Roles and Permissions
- Glue service role with S3 access
- Lambda execution role
- Appropriate security policies for each service

## Data Flow

1. **Data Ingestion**:
   - Raw data is uploaded to the raw S3 bucket
   - S3 event triggers Lambda function

2. **Data Processing**:
   - Lambda performs initial validation
   - Validated data is moved to the cleaned layer
   - Glue crawler updates the Data Catalog

3. **Data Transformation**:
   - Glue ETL job processes data from cleaned layer
   - Transformed data is written to curated layer
   - Data Catalog is updated with new schemas

4. **Data Analytics**:
   - Athena queries data directly from curated layer
   - Query results are stored in designated S3 location
   - Predefined queries available for common analytics

## Security Features

- S3 bucket versioning enabled
- IAM roles with least privilege access
- Secure configuration for Athena workgroup
- Encrypted data storage and transmission

## Usage

1. Deploy the infrastructure using Terraform
2. Upload raw data to the raw S3 bucket
3. Monitor the automated processing pipeline
4. Query processed data using Athena

## Prerequisites

- AWS Account
- Terraform installed
- Appropriate AWS credentials configured

## Environment Variables

Set the following variables in your terraform.tfvars file:
- `aws_region`
- `project_name`
- `environment`
