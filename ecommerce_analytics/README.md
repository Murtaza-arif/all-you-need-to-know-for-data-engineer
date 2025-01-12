# E-commerce Analytics Pipeline

This project implements an end-to-end data pipeline for e-commerce analytics using Apache Airflow, Snowflake, and Apache Superset.

## Architecture

1. Data Ingestion: Apache Airflow DAG ingests sales data
2. Data Cleaning: Automated data cleaning and transformation
3. Data Storage: Snowflake data warehouse
4. Data Visualization: Apache Superset dashboards

## Project Structure
```
ecommerce_analytics/
├── airflow/
│   ├── dags/
│   │   └── ecommerce_etl_dag.py
│   ├── data/
│   ├── logs/
│   ├── docker-compose.yaml
│   └── .env
└── superset/
    ├── docker-compose.yaml
    └── superset_home/
```

## Setup Instructions

### 1. Environment Configuration

Create `.env` files with the following variables:

```bash
# airflow/.env
SNOWFLAKE_USER=your_username
SNOWFLAKE_PASSWORD=your_password
SNOWFLAKE_ACCOUNT=your_account_identifier
SNOWFLAKE_WAREHOUSE=COMPUTE_WH
SNOWFLAKE_DATABASE=DATAMANAGEMENT
SNOWFLAKE_SCHEMA=PUBLIC
```

### 2. Airflow Setup

1. Navigate to the Airflow directory:
```bash
cd airflow
```

2. Start Airflow services:
```bash
docker compose up -d
```

3. Access Airflow UI:
- URL: http://localhost:8080
- Username: airflow
- Password: airflow

4. Create Snowflake connection in Airflow:
```bash
docker compose exec airflow-webserver airflow connections add 'snowflake_default' \
    --conn-type 'snowflake' \
    --conn-login '$SNOWFLAKE_USER' \
    --conn-password '$SNOWFLAKE_PASSWORD' \
    --conn-schema '$SNOWFLAKE_SCHEMA' \
    --conn-extra '{
        "account": "$SNOWFLAKE_ACCOUNT",
        "warehouse": "$SNOWFLAKE_WAREHOUSE",
        "database": "$SNOWFLAKE_DATABASE"
    }'
```

### 3. Superset Setup

1. Navigate to the Superset directory:
```bash
cd ../superset
```

2. Start Superset:
```bash
docker compose up -d
```

3. Access Superset UI:
- URL: http://localhost:8088
- Username: admin
- Password: admin

4. Configure Database Connection:
   - Go to "Data" → "Databases"
   - Add new database
   - Select SQLite
   - Use connection string: `sqlite:////data/sales.db`

5. Create Dataset:
   - Go to "Data" → "Datasets"
   - Click "+ Dataset"
   - Select your SQLite database
   - Choose "sales_data" table

6. Create Dashboard:
   - Go to "Dashboards"
   - Click "+ Dashboard"
   - Add visualizations:
     - Daily Sales Amount (Line Chart)
     - Top Products by Quantity (Bar Chart)
     - Customer Purchase Distribution (Pie Chart)
     - Sales Metrics Summary (Big Number)

## Creating Superset Dashboards

### 1. Setting up the Database Connection

1. Navigate to "Data" → "Databases" → "+ Database"
2. Select "SQLite" as the database type
3. Configure the connection:
   - Display Name: `Sales Database`
   - SQLAlchemy URI: `sqlite:////data/sales.db`
4. Click "Advanced" tab and enable:
   - ✓ Allow file uploads to database
   - ✓ Allow CSV Upload
5. Test the connection and save

Note: Enabling file uploads allows you to directly upload CSV files through the Superset interface.

### 2. Creating Datasets

1. Go to "Data" → "Datasets" → "+ Dataset"
2. Select the "Sales Database"
3. Choose "sales_data" table
4. Click "Add"
5. Configure columns:
   - `order_date`: Set type to `DATETIME`
   - `amount`: Set type to `DECIMAL`
   - `quantity`: Set type to `INTEGER`

### 3. Creating Charts

#### Daily Sales Chart
1. Go to "Charts" → "+ Chart"
2. Select "Line Chart"
3. Configure:
   - Dataset: sales_data
   - Time Column: order_date
   - Metrics: SUM(amount)
   - Time Grain: Day
4. Click "Update Chart"

#### Top Products Chart
1. Create new chart, select "Bar Chart"
2. Configure:
   - Dataset: sales_data
   - Metrics: SUM(quantity)
   - Group by: product_id
   - Row Limit: 10
   - Sort by: SUM(quantity) descending

#### Customer Distribution Chart
1. Create new chart, select "Pie Chart"
2. Configure:
   - Dataset: sales_data
   - Metrics: COUNT(*)
   - Group by: customer_id
   - Sort by: COUNT(*) descending

#### Sales Summary Metrics
1. Create new chart, select "Big Number with Trendline"
2. Configure:
   - Dataset: sales_data
   - Metric: SUM(amount)
   - Time Column: order_date
   - Time Grain: Day

### 4. Creating the Dashboard

1. Go to "Dashboards" → "+ Dashboard"
2. Name it "E-commerce Sales Analytics"
3. Add charts:
   - Click "Edit Dashboard"
   - Drag charts from the left sidebar
   - Arrange in a grid layout:
     - Top: Sales Summary Metrics (full width)
     - Middle Left: Daily Sales Chart
     - Middle Right: Top Products Chart
     - Bottom: Customer Distribution Chart
4. Add text elements:
   - Click "+ Component" → "Text"
   - Add headers and descriptions
5. Configure refresh:
   - Click "..." → "Edit Dashboard"
   - Set auto-refresh interval (e.g., 10 minutes)

### 5. Dashboard Customization

#### Color Schemes
1. Edit individual charts
2. Under "Customize", select:
   - Color Scheme: Category 10 for bar/pie charts
   - Line Style: Solid for line charts
   - Label Colors: Adjust for readability

#### Filters
1. Click "Edit Dashboard"
2. Add Filter Box:
   - Date Range for order_date
   - Multi-select for product_id
   - Value Range for amount
3. Set filter scopes:
   - Apply to all charts
   - Or customize per chart

#### Layout Tips
- Use consistent spacing
- Align charts properly
- Group related metrics
- Use clear titles and descriptions
- Add context with markdown text

### 6. Sharing and Export

1. Share Dashboard:
   - Click "..." → "Share"
   - Copy dashboard URL
   - Set permissions if needed

2. Export Options:
   - Download as PDF
   - Export to CSV
   - Schedule regular email reports

### 7. Maintenance

1. Regular Updates:
   - Verify data freshness
   - Check for broken charts
   - Update filters as needed

2. Performance:
   - Monitor query times
   - Optimize slow charts
   - Add caching if needed

## Data Pipeline

The pipeline consists of the following steps:

1. Data Ingestion: Sample sales data is generated and saved as CSV
2. Data Cleaning: Basic data cleaning and transformation
3. Snowflake Loading: Data is loaded into Snowflake through a staging process
4. Visualization: Data is visualized in Superset dashboards

## Monitoring

- Airflow tasks can be monitored through the Airflow UI
- Data quality can be monitored through Superset dashboards
- Logs are available in the `airflow/logs` directory

## Troubleshooting

1. If Airflow tasks fail:
   - Check Airflow task logs in the UI
   - Verify Snowflake connection details
   - Ensure data files exist in the correct location

2. If Superset visualizations don't update:
   - Verify the SQLite database is being updated
   - Refresh the dashboard
   - Check database connection in Superset

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## Usage

1. Access Airflow UI at http://localhost:8080
2. Access Superset at http://localhost:8088
3. Monitor DAG runs in Airflow
4. Create visualizations in Superset using Snowflake data
