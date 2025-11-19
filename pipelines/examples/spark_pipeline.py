"""
Example Spark Pipeline for Lakehouse Data Product
This demonstrates a bronze -> silver -> gold data flow with logging and monitoring
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, current_timestamp, lit
import logging
import time
from prometheus_client import Counter, Histogram, Gauge, push_to_gateway

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('lakehouse.spark_pipeline')

# Metrics
ingestion_counter = Counter('lakehouse_ingestion_records_total', 'Records ingested', ['layer', 'source'])
processing_time = Histogram('lakehouse_processing_duration_seconds', 'Processing time', ['layer'])
quality_score = Gauge('lakehouse_data_quality_score', 'Data quality score', ['dataset'])


class LakehousePipeline:
    """Lakehouse data pipeline with bronze, silver, and gold layers"""
    
    def __init__(self, app_name="lakehouse-pipeline"):
        """Initialize Spark session with Delta Lake support"""
        self.spark = SparkSession.builder \
            .appName(app_name) \
            .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
            .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
            .getOrCreate()
        
        logger.info(f"Initialized Spark session: {app_name}")
    
    def ingest_to_bronze(self, source_path, bronze_path, source_name):
        """
        Ingest raw data to bronze layer
        
        Args:
            source_path: Path to source data
            bronze_path: Path to bronze layer storage
            source_name: Name of the data source
        """
        start_time = time.time()
        logger.info(f"Starting bronze ingestion from {source_name}")
        
        try:
            # Read raw data (example: CSV, adjust for your source)
            df = self.spark.read \
                .option("header", "true") \
                .option("inferSchema", "true") \
                .csv(source_path)
            
            # Add metadata columns
            df_bronze = df \
                .withColumn("ingestion_timestamp", current_timestamp()) \
                .withColumn("source_system", lit(source_name))
            
            # Write to bronze layer (Delta format)
            df_bronze.write \
                .format("delta") \
                .mode("append") \
                .save(bronze_path)
            
            record_count = df_bronze.count()
            ingestion_counter.labels(layer='bronze', source=source_name).inc(record_count)
            
            duration = time.time() - start_time
            processing_time.labels(layer='bronze').observe(duration)
            
            logger.info(f"Bronze ingestion completed: {record_count} records in {duration:.2f}s")
            return df_bronze
            
        except Exception as e:
            logger.error(f"Bronze ingestion failed: {str(e)}")
            raise
    
    def transform_to_silver(self, bronze_path, silver_path):
        """
        Transform bronze data to silver layer with cleaning and validation
        
        Args:
            bronze_path: Path to bronze layer storage
            silver_path: Path to silver layer storage
        """
        start_time = time.time()
        logger.info("Starting silver transformation")
        
        try:
            # Read from bronze
            df_bronze = self.spark.read.format("delta").load(bronze_path)
            
            # Data cleaning and validation
            df_silver = df_bronze \
                .dropDuplicates() \
                .na.drop(subset=["id"]) \
                .withColumn("processed_timestamp", current_timestamp())
            
            # Calculate data quality score
            total_records = df_bronze.count()
            clean_records = df_silver.count()
            quality = clean_records / total_records if total_records > 0 else 0
            quality_score.labels(dataset='silver').set(quality)
            
            # Write to silver layer
            df_silver.write \
                .format("delta") \
                .mode("overwrite") \
                .save(silver_path)
            
            duration = time.time() - start_time
            processing_time.labels(layer='silver').observe(duration)
            
            logger.info(f"Silver transformation completed: {clean_records} records, quality: {quality:.2%}, time: {duration:.2f}s")
            return df_silver
            
        except Exception as e:
            logger.error(f"Silver transformation failed: {str(e)}")
            raise
    
    def aggregate_to_gold(self, silver_path, gold_path, aggregation_key):
        """
        Create business aggregates in gold layer
        
        Args:
            silver_path: Path to silver layer storage
            gold_path: Path to gold layer storage
            aggregation_key: Column to aggregate by
        """
        start_time = time.time()
        logger.info("Starting gold aggregation")
        
        try:
            # Read from silver
            df_silver = self.spark.read.format("delta").load(silver_path)
            
            # Create business aggregates
            df_gold = df_silver \
                .groupBy(aggregation_key) \
                .count() \
                .withColumn("aggregation_timestamp", current_timestamp())
            
            # Write to gold layer
            df_gold.write \
                .format("delta") \
                .mode("overwrite") \
                .save(gold_path)
            
            duration = time.time() - start_time
            processing_time.labels(layer='gold').observe(duration)
            
            agg_count = df_gold.count()
            logger.info(f"Gold aggregation completed: {agg_count} aggregates in {duration:.2f}s")
            return df_gold
            
        except Exception as e:
            logger.error(f"Gold aggregation failed: {str(e)}")
            raise
    
    def run_full_pipeline(self, source_path, bronze_path, silver_path, gold_path, 
                         source_name, aggregation_key):
        """
        Run the complete bronze -> silver -> gold pipeline
        """
        logger.info("=" * 80)
        logger.info("Starting full lakehouse pipeline")
        logger.info("=" * 80)
        
        try:
            # Bronze
            self.ingest_to_bronze(source_path, bronze_path, source_name)
            
            # Silver
            self.transform_to_silver(bronze_path, silver_path)
            
            # Gold
            self.aggregate_to_gold(silver_path, gold_path, aggregation_key)
            
            # Push metrics to Prometheus (optional)
            # push_to_gateway('localhost:9091', job='lakehouse-pipeline', registry=registry)
            
            logger.info("Full pipeline completed successfully")
            
        except Exception as e:
            logger.error(f"Pipeline failed: {str(e)}")
            raise
        finally:
            self.spark.stop()


if __name__ == "__main__":
    # Example usage
    pipeline = LakehousePipeline()
    
    pipeline.run_full_pipeline(
        source_path="data/source/customers.csv",
        bronze_path="data/bronze/customers",
        silver_path="data/silver/customers",
        gold_path="data/gold/customers_by_region",
        source_name="crm",
        aggregation_key="region"
    )
