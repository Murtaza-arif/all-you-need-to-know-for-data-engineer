# Weather Data ETL Pipeline

This project implements a data transformation and cleaning pipeline for real-time weather data using Apache Airflow. The pipeline fetches weather data from OpenWeatherMap API, transforms it, and prepares it for further analysis.

## Features

- Hourly weather data collection from multiple cities
- Data cleaning and transformation
- Temperature conversion (Celsius to Fahrenheit)
- Weather categorization
- Data quality checks
- Wind speed conversion
- Automated pipeline using Apache Airflow

## Project Structure

```
weather_etl/
├── dags/
│   └── weather_etl_dag.py
├── requirements.txt
└── README.md
```

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
Create a `.env` file in the project root with:
```
WEATHER_API_KEY=your_openweathermap_api_key
```

3. Configure Airflow:
- Set AIRFLOW_HOME to your project directory
- Initialize the Airflow database
- Start the Airflow webserver and scheduler

## Pipeline Steps

1. **Extract**: Fetches weather data from OpenWeatherMap API for multiple cities
2. **Transform**: 
   - Converts temperature to Fahrenheit
   - Categorizes temperature
   - Cleans weather descriptions
   - Converts wind speed to MPH
   - Adds data quality flags
3. **Load**: Saves the transformed data (can be modified to load into a database)

## Schedule

The pipeline runs every hour to collect and process the latest weather data.

## Data Quality Checks

- Humidity validation (should not exceed 100%)
- Pressure validation (should be within reasonable range)
- Data completeness checks

## Notes

- The pipeline is configured to process data for London, New York, Tokyo, Sydney, and Mumbai
- All timestamps are in UTC
- Temporary files are stored in /tmp directory
