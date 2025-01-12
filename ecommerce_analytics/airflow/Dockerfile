FROM apache/airflow:2.7.1

USER root
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

USER airflow

# Install Python packages
COPY requirements-airflow.txt /opt/airflow/
RUN pip install --no-cache-dir -r /opt/airflow/requirements-airflow.txt
