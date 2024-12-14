from setuptools import setup, find_packages

setup(
    name="batch_data_ingestion",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "pyspark>=3.5.0",
        "pandas>=1.5.3",
        "mysql-connector-python>=8.2.0",
        "boto3>=1.34.1",
        "python-dotenv>=1.0.0",
        "setuptools>=65.5.1"
    ]
)
