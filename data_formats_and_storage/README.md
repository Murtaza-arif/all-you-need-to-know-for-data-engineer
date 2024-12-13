# Data Formats and Storage

This directory contains examples and case studies of different data formats and storage patterns commonly used in data engineering.

## Contents

1. Data Format Examples
   - CSV (Comma-Separated Values)
   - JSON (JavaScript Object Notation)
   - Parquet
   - Avro
   - ORC (Optimized Row Columnar)

2. Format Conversion Examples
   - CSV to Parquet
   - JSON to CSV
   - CSV to Avro
   - JSON to Parquet

3. E-commerce Database Schema Case Study

## E-commerce Database Schema Case Study

This case study demonstrates the implementation of both Star and Snowflake schemas for an e-commerce platform, showcasing different approaches to data warehouse design.

### Files Structure

- [`ecommerce_snowflake_schema.dbml`](./ecommerce_snowflake_schema.dbml): Snowflake schema implementation
- [`ecommerce_star_schema.dbml`](./ecommerce_star_schema.dbml): Star schema implementation
- [`schema_comparison.md`](./schema_comparison.md): Detailed comparison between both schemas

### Schema Visualizations

- [Snowflake Schema Diagram](https://dbdocs.io/Murtaza-arif/snowflake_ecommerce_schema?view=relationships)
- [Star Schema Diagram](https://dbdocs.io/Murtaza-arif/star_ecommerce_schema?view=relationships)

### Key Features

1. **Snowflake Schema**
   - Highly normalized dimension tables
   - Better data integrity
   - Reduced data redundancy
   - Suitable for OLTP workloads
   - Complex queries with multiple joins

2. **Star Schema**
   - Denormalized dimension tables
   - Optimized for analytics
   - Faster query performance
   - Suitable for OLAP workloads
   - Simpler queries with fewer joins

### Implementation Details

Both schemas are implemented using DBML (Database Markup Language) and include:

1. **Fact Tables**
   - Sales/Orders tracking
   - Inventory management

2. **Dimension Tables**
   - Product information
   - Customer data
   - Location/Geography
   - Time dimension
   - Additional reference data

3. **Best Practices**
   - Proper indexing strategies
   - Referential integrity
   - Audit columns
   - Comprehensive documentation

### Use Cases

The case study demonstrates how to model common e-commerce scenarios:

1. **Sales Analysis**
   - Revenue tracking
   - Product performance
   - Customer behavior

2. **Inventory Management**
   - Stock levels
   - Reorder points
   - Warehouse operations

3. **Customer Analytics**
   - Segmentation
   - Purchase patterns
   - Geographic distribution

### Learning Outcomes

Through this case study, you'll learn:

1. **Schema Design**
   - When to use Star vs Snowflake schemas
   - Trade-offs between normalization and performance
   - Best practices for data warehouse design

2. **Data Modeling**
   - Fact table design
   - Dimension table modeling
   - Handling hierarchies

3. **Performance Optimization**
   - Indexing strategies
   - Query optimization
   - Storage efficiency

### Tools Used

- DBML for schema definition
- dbdiagram.io for visualization
- PostgreSQL as the target database

## Requirements
pandas
pyarrow
fastparquet
fastavro

## Setup
1. Make sure you have activated the virtual environment from the root directory:
```bash
# From project root
source venv/bin/activate  # On macOS/Linux
# OR
.\venv\Scripts\activate   # On Windows
```

2. Install dependencies if you haven't already:
```bash
pip install -r ../requirements.txt
```

## Usage
Each example is contained in its own Python script. Check the individual scripts for detailed comments and usage instructions.

1. Run format examples:
```bash
python format_examples.py
```

2. Run format conversions:
```bash
python format_conversions.py
```

## Getting Started

1. Review the schema files (`.dbml` files)
2. Check the visual representations using the provided links
3. Read the detailed comparison in `schema_comparison.md`
4. Understand the trade-offs and best practices

## Additional Resources

- [DBML Documentation](https://dbml.dbdiagram.io/docs/)
- [Data Warehouse Design Best Practices](https://docs.microsoft.com/en-us/azure/architecture/data-guide/relational-data/data-warehousing)
- [Star Schema vs Snowflake Schema](https://www.vertabelo.com/blog/data-warehouse-modeling-star-schema-vs-snowflake-schema/)
