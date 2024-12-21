# Data Engineering Monitoring Demo

This project demonstrates monitoring of a data engineering pipeline using Prometheus and Evidently, with real-time stock data as an example.

## Components

1. **Stock Data Pipeline**: Fetches real-time stock data and processes it
2. **Prometheus Monitoring**: Tracks operational metrics
3. **Grafana**: Visualization of metrics
4. **AlertManager**: Handles alerting based on metric conditions
5. **Evidently Integration**: Monitors data drift

## Setup

1. Set up the Python virtual environment:
```bash
# Make the setup script executable
chmod +x setup.sh

# Run the setup script
./setup.sh

# Activate the virtual environment
source venv/bin/activate
```

2. Start the monitoring stack using Docker Compose:
```bash
docker compose up -d
```

3. Start the stock data pipeline:
```bash
python stock_pipeline.py
```

## Development

When working on the project, always ensure the virtual environment is activated:
```bash
source venv/bin/activate
```

To deactivate the virtual environment when you're done:
```bash
deactivate
```

## Accessing Services

- Prometheus UI: http://localhost:9090
- Grafana UI: http://localhost:3000 (admin/admin)
- AlertManager UI: http://localhost:9093
- Raw metrics endpoint: http://localhost:8000

## Monitored Metrics

- `stock_data_fetch_total`: Total number of stock data fetches
- `stock_data_fetch_errors_total`: Number of fetch errors
- `stock_data_processing_seconds`: Processing time histogram
- `stock_current_price`: Current stock price by symbol
- `data_drift_detected_total`: Number of times data drift was detected

## Alerts Configuration

The system is configured with the following alerts:
- High Error Rate: Triggers when error rate exceeds 10% over 5 minutes
- Data Drift Detection: Triggers when data drift is detected
- Slow Processing: Triggers when 95th percentile processing time exceeds 5 seconds

## Data Drift Detection

The system uses Evidently to detect data drift by comparing current stock data patterns with a 30-day historical reference period. Alerts are generated when significant drift is detected.
