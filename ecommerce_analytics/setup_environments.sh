#!/bin/bash

# Create Airflow environment
echo "Creating Airflow environment..."
conda create -n ecommerce_airflow python=3.10 -y
conda activate ecommerce_airflow
pip install -r requirements-airflow.txt

# Create shared environment for other tools
echo "Creating shared environment..."
conda create -n ecommerce_shared python=3.10 -y
conda activate ecommerce_shared
pip install -r requirements.txt

echo "Environments created successfully!"
echo "To activate environments:"
echo "conda activate ecommerce_airflow  # For Airflow"
echo "conda activate ecommerce_shared   # For shared tools"
