"""
Example Airflow DAG for Lakehouse Data Product
This demonstrates orchestrating a lakehouse pipeline with monitoring
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
from airflow.utils.dates import days_ago
import logging

# Configure logging
logger = logging.getLogger('lakehouse.airflow_dag')

# Default arguments
default_args = {
    'owner': 'data-engineering',
    'depends_on_past': False,
    'email': ['alerts@example.com'],
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
    'execution_timeout': timedelta(hours=2),
}


def validate_data_quality(**context):
    """Data quality validation task"""
    logger.info("Running data quality checks")
    
    # Example quality checks
    quality_score = 0.95  # Replace with actual calculation
    
    if quality_score < 0.85:
        raise ValueError(f"Data quality score {quality_score} below threshold 0.85")
    
    logger.info(f"Data quality passed: {quality_score}")
    return quality_score


def send_metrics(**context):
    """Send metrics to monitoring system"""
    logger.info("Sending metrics to monitoring system")
    
    # Example: Send to Prometheus pushgateway
    # from prometheus_client import CollectorRegistry, Gauge, push_to_gateway
    # registry = CollectorRegistry()
    # g = Gauge('lakehouse_pipeline_completion', 'Pipeline completion', registry=registry)
    # g.set(1)
    # push_to_gateway('localhost:9091', job='airflow-dag', registry=registry)
    
    logger.info("Metrics sent successfully")


def notify_completion(**context):
    """Send completion notification"""
    logger.info("Pipeline completed successfully")
    # Add notification logic (Slack, email, etc.)


# Define the DAG
with DAG(
    'lakehouse_data_product_pipeline',
    default_args=default_args,
    description='Lakehouse data product pipeline - Bronze/Silver/Gold layers',
    schedule_interval='0 2 * * *',  # Run daily at 2 AM
    start_date=days_ago(1),
    catchup=False,
    tags=['lakehouse', 'data-product', 'etl'],
) as dag:
    
    # Task 1: Ingest to Bronze Layer
    ingest_bronze = SparkSubmitOperator(
        task_id='ingest_to_bronze',
        application='pipelines/examples/spark_pipeline.py',
        name='bronze-ingestion',
        conf={
            'spark.sql.extensions': 'io.delta.sql.DeltaSparkSessionExtension',
            'spark.sql.catalog.spark_catalog': 'org.apache.spark.sql.delta.catalog.DeltaCatalog',
        },
        application_args=[
            '--layer', 'bronze',
            '--source', 'crm',
            '--date', '{{ ds }}',
        ],
        verbose=True,
    )
    
    # Task 2: Transform to Silver Layer
    transform_silver = SparkSubmitOperator(
        task_id='transform_to_silver',
        application='pipelines/examples/spark_pipeline.py',
        name='silver-transformation',
        conf={
            'spark.sql.extensions': 'io.delta.sql.DeltaSparkSessionExtension',
            'spark.sql.catalog.spark_catalog': 'org.apache.spark.sql.delta.catalog.DeltaCatalog',
        },
        application_args=[
            '--layer', 'silver',
            '--date', '{{ ds }}',
        ],
        verbose=True,
    )
    
    # Task 3: Data Quality Validation
    quality_check = PythonOperator(
        task_id='validate_data_quality',
        python_callable=validate_data_quality,
        provide_context=True,
    )
    
    # Task 4: Aggregate to Gold Layer
    aggregate_gold = SparkSubmitOperator(
        task_id='aggregate_to_gold',
        application='pipelines/examples/spark_pipeline.py',
        name='gold-aggregation',
        conf={
            'spark.sql.extensions': 'io.delta.sql.DeltaSparkSessionExtension',
            'spark.sql.catalog.spark_catalog': 'org.apache.spark.sql.delta.catalog.DeltaCatalog',
        },
        application_args=[
            '--layer', 'gold',
            '--date', '{{ ds }}',
        ],
        verbose=True,
    )
    
    # Task 5: Send Metrics
    send_metrics_task = PythonOperator(
        task_id='send_metrics',
        python_callable=send_metrics,
        provide_context=True,
    )
    
    # Task 6: Notify Completion
    notify = PythonOperator(
        task_id='notify_completion',
        python_callable=notify_completion,
        provide_context=True,
        trigger_rule='all_success',
    )
    
    # Define task dependencies
    ingest_bronze >> transform_silver >> quality_check >> aggregate_gold >> send_metrics_task >> notify
