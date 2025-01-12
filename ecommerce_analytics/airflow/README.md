# E-commerce Analytics Airflow Setup

## Setup Instructions

1. Create necessary directories:
```bash
mkdir -p data logs plugins config
```

2. Copy the environment template and update with your credentials:
```bash
cp env.template .env
```

3. Start Airflow services:
```bash
docker compose up -d
```

4. Create Snowflake Connection
Run the following command to create the Snowflake connection in Airflow:
```bash
docker compose exec airflow-webserver airflow connections add snowflake_default \
    --conn-type snowflake \
    --conn-login username \
    --conn-password password \
    --conn-schema PUBLIC \
    --conn-extra "{\"account\": \"mlavxhv-kn71607\", \"warehouse\": \"COMPUTE_WH\", \"database\": \"DATAMANAGEMENT\", \"role\": \"ACCOUNTADMIN\"}"
```

## Accessing Airflow UI
- URL: http://localhost:8080
- Default credentials:
  - Username: airflow
  - Password: airflow

## DAG Overview
The e-commerce ETL pipeline consists of the following tasks:
1. Ingest sales data
2. Clean and transform data
3. Load data into Snowflake

## Directory Structure
```
airflow/
├── dags/               # DAG files
├── data/               # Data files
├── logs/               # Airflow logs
├── plugins/            # Custom plugins
├── config/            # Configuration files
├── docker-compose.yaml # Docker compose configuration
├── Dockerfile         # Custom Dockerfile
└── .env               # Environment variables
```
