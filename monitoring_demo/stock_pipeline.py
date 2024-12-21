import yfinance as yf
import pandas as pd
import time
from prometheus_client import start_http_server, Counter, Gauge, Histogram
from evidently.metrics import ColumnDriftMetric, DatasetDriftMetric, DatasetMissingValuesMetric
from evidently.report import Report
import numpy as np
import logging
import pytz
from datetime import datetime, timedelta
import warnings

# Suppress specific warnings
warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore', category=RuntimeWarning)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Prometheus metrics
FETCH_ERRORS = Counter('stock_data_fetch_errors_total', 'Number of errors fetching stock data')
PROCESSING_TIME = Histogram('stock_data_processing_seconds', 'Time spent processing stock data')
CURRENT_PRICE = Gauge('stock_current_price', 'Current stock price', ['symbol'])

# Data Drift Metrics
DRIFT_DETECTED = Counter('data_drift_detected_total', 'Number of times data drift was detected', ['column'])
MISSING_VALUES = Gauge('missing_values_ratio', 'Ratio of missing values', ['column'])
COLUMN_MEAN = Gauge('column_mean', 'Mean value of column', ['column'])
COLUMN_STD = Gauge('column_std', 'Standard deviation of column', ['column'])
COLUMN_DRIFT_SCORE = Gauge('column_drift_score', 'Drift score for column', ['column'])

class StockDataPipeline:
    def __init__(self, symbols=['AAPL', 'GOOGL', 'MSFT']):
        self.symbols = symbols
        self.reference_data = {}
        self.timezone = pytz.timezone('America/New_York')  # NYSE timezone
        self.initialize_reference_data()

    def preprocess_data(self, df):
        """Preprocess the dataframe to handle timezones and columns"""
        if df.empty:
            return df

        # Convert index to NY timezone
        if df.index.tz is None:
            df.index = df.index.tz_localize('UTC').tz_convert(self.timezone)
        elif df.index.tz != self.timezone:
            df.index = df.index.tz_convert(self.timezone)

        # Flatten multi-level columns if they exist
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [f"{col[0]}_{col[1]}" if isinstance(col, tuple) else col for col in df.columns]

        # Ensure numeric columns are float
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        for col in numeric_columns:
            df[col] = df[col].astype(float)

        return df

    def initialize_reference_data(self):
        """Initialize reference data for drift detection"""
        try:
            for symbol in self.symbols:
                # Get 5 days of historical data
                hist = yf.Ticker(symbol).history(period='5d')
                if not hist.empty:
                    hist = self.preprocess_data(hist)
                    # Store first 3 days as reference
                    self.reference_data[symbol] = hist.iloc[:3].copy()
                    logger.info(f"Initialized reference data for {symbol} with shape {hist.shape}")
        except Exception as e:
            logger.error(f"Error initializing reference data: {e}")
            FETCH_ERRORS.inc()

    def get_current_data(self):
        """Fetch current stock data"""
        current_data = {}
        try:
            for symbol in self.symbols:
                # Get 1 day of data
                data = yf.Ticker(symbol).history(period='1d')
                if not data.empty:
                    data = self.preprocess_data(data)
                    current_data[symbol] = data
                    CURRENT_PRICE.labels(symbol=symbol).set(data['Close'].iloc[-1])
                    logger.info(f"Fetched current data for {symbol} with shape {data.shape}")
        except Exception as e:
            logger.error(f"Error fetching current data: {e}")
            FETCH_ERRORS.inc()
        return current_data

    def calculate_statistics(self, data, symbol, prefix=''):
        """Calculate and record statistics for numerical columns"""
        if data.empty:
            return

        numerical_columns = data.select_dtypes(include=[np.number]).columns
        for col in numerical_columns:
            column_name = f"{prefix}{col}"
            try:
                # Handle potential NaN values
                clean_data = data[col].fillna(method='ffill').fillna(method='bfill')
                if clean_data.empty:
                    continue

                # Calculate and record basic statistics
                mean_val = clean_data.mean()
                std_val = clean_data.std()
                missing_ratio = data[col].isna().mean()

                COLUMN_MEAN.labels(column=f"{symbol}_{column_name}").set(mean_val)
                COLUMN_STD.labels(column=f"{symbol}_{column_name}").set(std_val)
                MISSING_VALUES.labels(column=f"{symbol}_{column_name}").set(missing_ratio)

                logger.debug(f"Statistics for {symbol}_{column_name}: mean={mean_val:.2f}, std={std_val:.2f}, missing={missing_ratio:.2%}")
            except Exception as e:
                logger.error(f"Error calculating statistics for {symbol}_{column_name}: {e}")

    def check_data_drift(self, current_data):
        """Check for data drift using Evidently"""
        for symbol, current_df in current_data.items():
            if symbol not in self.reference_data or current_df.empty:
                continue

            reference_df = self.reference_data[symbol]
            
            # Calculate statistics for both datasets
            self.calculate_statistics(reference_df, symbol, 'reference_')
            self.calculate_statistics(current_df, symbol, 'current_')

            try:
                # Create metrics for each numerical column
                numerical_columns = current_df.select_dtypes(include=[np.number]).columns
                
                for column in numerical_columns:
                    # Skip columns with insufficient data
                    if len(current_df[column].dropna()) < 2 or len(reference_df[column].dropna()) < 2:
                        logger.warning(f"Insufficient data for drift detection in {symbol} {column}")
                        continue

                    # Create a report with column drift metric
                    report = Report(metrics=[
                        ColumnDriftMetric(column_name=column)
                    ])
                    
                    report.run(reference_data=reference_df, current_data=current_df)
                    result = report.as_dict()
                    
                    # Check if drift was detected
                    if result['metrics'][0]['result']['drift_detected']:
                        DRIFT_DETECTED.labels(column=f"{symbol}_{column}").inc()
                        drift_score = result['metrics'][0]['result'].get('drift_score', 0)
                        COLUMN_DRIFT_SCORE.labels(column=f"{symbol}_{column}").set(drift_score)
                        logger.warning(f"Drift detected in {symbol} {column} with score {drift_score}")

                # Additional dataset-level metrics
                dataset_report = Report(metrics=[
                    DatasetDriftMetric(),
                    DatasetMissingValuesMetric()
                ])
                dataset_report.run(reference_data=reference_df, current_data=current_df)
                dataset_result = dataset_report.as_dict()
                
                # Log dataset-level results
                if dataset_result['metrics'][0]['result']['dataset_drift']:
                    logger.warning(f"Dataset-level drift detected for {symbol}")
                    
            except Exception as e:
                logger.error(f"Error checking drift for {symbol}: {e}")
                FETCH_ERRORS.inc()

    def run(self):
        """Main pipeline loop"""
        start_http_server(8000)
        logger.info("Started Prometheus metrics server on port 8000")

        while True:
            with PROCESSING_TIME.time():
                current_data = self.get_current_data()
                self.check_data_drift(current_data)
            time.sleep(300)  # Wait for 5 minutes before next iteration

if __name__ == "__main__":
    pipeline = StockDataPipeline()
    pipeline.run()
