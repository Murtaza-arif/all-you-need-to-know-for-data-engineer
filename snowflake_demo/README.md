# Snowflake Query Optimization Demo

This project demonstrates various data management and query optimization techniques in Snowflake, showing how proper data organization and materialized views can significantly improve query performance.

## Overview

The demo includes several comparison scenarios that highlight the importance of:
- Table clustering
- Data partitioning
- Materialized views
- Efficient query patterns

## Project Structure

- `setup_snowflake_data.py`: Creates and populates test tables with sample data
- `snowflake_query_comparison.py`: Contains pairs of queries demonstrating optimized vs non-optimized approaches
- `.env`: Configuration file for Snowflake connection parameters
- `requirements.txt`: Python package dependencies

## Setup Instructions

1. Install required packages:
```bash
pip install -r requirements.txt
```

2. Configure Snowflake connection:
Create a `.env` file with the following parameters:
```env
SNOWFLAKE_USER=your_username
SNOWFLAKE_PASSWORD=your_password
SNOWFLAKE_ACCOUNT=your_account
SNOWFLAKE_WAREHOUSE=your_warehouse
SNOWFLAKE_DATABASE=your_database
SNOWFLAKE_SCHEMA=your_schema
```

3. Run the setup script:
```bash
python setup_snowflake_data.py
```

4. Run the comparison queries:
```bash
python snowflake_query_comparison.py
```

## Query Comparisons

### 1. Clustered vs Non-Clustered Tables
- **Optimized**: Uses clustering key on date column
- **Non-optimized**: Standard table without clustering
- **Benefit**: Faster date-range queries

### 2. Partitioned vs Non-Partitioned Tables
- **Optimized**: Partitioned by year and month
- **Non-optimized**: No partitioning
- **Benefit**: Efficient data pruning for time-based queries

### 3. Materialized Views vs Direct Queries
- **Optimized**: Pre-computed aggregations using materialized view
- **Non-optimized**: Computing aggregations on-the-fly
- **Benefit**: Faster access to frequently used aggregations

## Sample Data

The demo uses a sales dataset with:
- 100,000 sample records
- Date range: 2023-01-01 to 2023-12-31
- Fields:
  - Transaction date
  - Order amount
  - Customer ID
  - Region
  - Product category

## Query Metrics

The comparison queries measure:
- Execution time
- Data scanned
- Performance impact of different optimization techniques

## Best Practices Demonstrated

1. **Data Organization**
   - Proper clustering keys
   - Strategic partitioning
   - Materialized view usage

2. **Query Optimization**
   - Efficient filtering
   - Pre-computed aggregations
   - Optimized join patterns

3. **Performance Monitoring**
   - Execution time tracking
   - Query result comparison
   - Data distribution analysis

## Results Analysis

The queries demonstrate performance improvements through:
1. Reduced data scanning
2. Faster data retrieval
3. Efficient use of pre-computed results
4. Better query plan optimization

## Contributing

Feel free to submit issues, fork the repository, and create pull requests for any improvements.
