from airflow.models import DAG
from airflow.operators.python import PythonOperator
from airflow.exceptions import AirflowException
import pandas as pd
import numpy as np
import logging
import os
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

def process_market_data(parent_dag_id, child_dag_id, crypto_symbol, **context):
    """Process market data for a specific cryptocurrency"""
    try:
        # Get raw data from parent DAG's XCom
        task_instance = context['task_instance']
        raw_data = task_instance.xcom_pull(
            dag_id=parent_dag_id,
            task_ids=f'stream_market_data_{crypto_symbol}',
            key=f'market_data_{crypto_symbol}'
        )
        
        if not raw_data:
            raise AirflowException(f"No raw data found for {crypto_symbol}")
        
        df = pd.DataFrame(raw_data)
        
        # Calculate technical indicators
        df['price'] = df['price'].astype(float)
        df['volume'] = df['volume'].astype(float)
        
        # VWAP (Volume Weighted Average Price)
        df['vwap'] = (df['price'] * df['volume']).cumsum() / df['volume'].cumsum()
        
        # Price momentum
        df['price_momentum'] = df['price'].pct_change()
        
        # Volatility (Rolling standard deviation)
        df['volatility'] = df['price_momentum'].rolling(window=10).std()
        
        # Volume trend
        df['volume_ma'] = df['volume'].rolling(window=5).mean()
        df['volume_trend'] = df['volume'] / df['volume_ma']
        
        # Push processed data back to XCom
        processed_data = df.to_dict('records')
        task_instance.xcom_push(
            key=f'processed_data_{crypto_symbol}',
            value=processed_data
        )
        
        logger.info(f"Processed {len(processed_data)} records for {crypto_symbol}")
        return processed_data
    
    except Exception as e:
        logger.error(f"Error processing data for {crypto_symbol}: {str(e)}")
        raise AirflowException(f"Failed to process market data for {crypto_symbol}: {str(e)}")

def analyze_market_signals(parent_dag_id, child_dag_id, crypto_symbol, **context):
    """Analyze market signals from processed data"""
    try:
        # Get processed data from XCom
        task_instance = context['task_instance']
        processed_data = task_instance.xcom_pull(
            task_ids=f'process_market_data_{crypto_symbol}',
            key=f'processed_data_{crypto_symbol}'
        )
        
        if not processed_data:
            raise AirflowException(f"No processed data found for {crypto_symbol}")
        
        df = pd.DataFrame(processed_data)
        
        # Generate trading signals
        signals = {
            'symbol': crypto_symbol,
            'timestamp': datetime.utcnow().isoformat(),
            'signals': []
        }
        
        # Volume spike signal
        if df['volume_trend'].iloc[-1] > 2.0:
            signals['signals'].append({
                'type': 'VOLUME_SPIKE',
                'strength': 'HIGH',
                'value': float(df['volume_trend'].iloc[-1])
            })
        
        # Volatility signal
        if df['volatility'].iloc[-1] > df['volatility'].mean() + df['volatility'].std():
            signals['signals'].append({
                'type': 'HIGH_VOLATILITY',
                'strength': 'MEDIUM',
                'value': float(df['volatility'].iloc[-1])
            })
        
        # Price momentum signal
        if abs(df['price_momentum'].iloc[-1]) > 0.02:  # 2% price movement
            signal_type = 'BULLISH' if df['price_momentum'].iloc[-1] > 0 else 'BEARISH'
            signals['signals'].append({
                'type': f'MOMENTUM_{signal_type}',
                'strength': 'HIGH',
                'value': float(df['price_momentum'].iloc[-1])
            })
        
        # Push signals to XCom
        task_instance.xcom_push(
            key=f'market_signals_{crypto_symbol}',
            value=signals
        )
        
        logger.info(f"Generated {len(signals['signals'])} signals for {crypto_symbol}")
        return signals
    
    except Exception as e:
        logger.error(f"Error analyzing signals for {crypto_symbol}: {str(e)}")
        raise AirflowException(f"Failed to analyze market signals for {crypto_symbol}: {str(e)}")

def create_processing_subdag(parent_dag_id, child_dag_id, crypto_symbol, args):
    """Create a SubDAG for processing market data"""
    dag = DAG(
        dag_id=f'{parent_dag_id}.{child_dag_id}',
        default_args=args,
        schedule_interval=None,
    )
    
    # Process market data
    process_task = PythonOperator(
        task_id=f'process_market_data_{crypto_symbol}',
        python_callable=process_market_data,
        op_kwargs={
            'parent_dag_id': parent_dag_id,
            'child_dag_id': child_dag_id,
            'crypto_symbol': crypto_symbol
        },
        provide_context=True,
        dag=dag,
    )
    
    # Analyze market signals
    analyze_task = PythonOperator(
        task_id=f'analyze_market_signals_{crypto_symbol}',
        python_callable=analyze_market_signals,
        op_kwargs={
            'parent_dag_id': parent_dag_id,
            'child_dag_id': child_dag_id,
            'crypto_symbol': crypto_symbol
        },
        provide_context=True,
        dag=dag,
    )
    
    process_task >> analyze_task
    
    return dag
