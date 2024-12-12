# Data Formats and Storage

This section demonstrates handling various data formats commonly used in data engineering and shows how to convert between different formats.

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
