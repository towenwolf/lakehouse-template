# Quick Reference Guide

A condensed reference for common tasks in the lakehouse template.

## Installation & Setup

```bash
# 1. Use this template on GitHub or clone
git clone https://github.com/your-username/my-lakehouse

# 2. Set up environment
cp config/environment-example.env .env
# Edit .env with your values

# 3. Validate template structure
chmod +x scripts/validate-template.sh
./scripts/validate-template.sh

# 4. Start local development environment (optional)
docker-compose -f docker-compose.example.yml up -d
```

## Common Commands

### Spark

```bash
# Local development
spark-submit pipelines/examples/spark_pipeline.py

# With Delta Lake
spark-submit \
  --conf spark.sql.extensions=io.delta.sql.DeltaSparkSessionExtension \
  --conf spark.sql.catalog.spark_catalog=org.apache.spark.sql.delta.catalog.DeltaCatalog \
  your_pipeline.py

# Production cluster
spark-submit --master yarn --deploy-mode cluster your_pipeline.py
```

### dbt

```bash
# Initialize project
cd config/tools/dbt
dbt init my_project

# Run models
dbt run --models bronze silver gold

# Test
dbt test

# Generate documentation
dbt docs generate
dbt docs serve
```

### Airflow

```bash
# Initialize
export AIRFLOW_HOME=/opt/airflow
airflow db init

# Start
airflow webserver --port 8080  # Terminal 1
airflow scheduler               # Terminal 2

# Trigger DAG
airflow dags trigger lakehouse_data_product_pipeline
```

### Prefect

```bash
# Start server
prefect server start

# Deploy flow
python your_flow.py

# Run flow
prefect deployment run 'your-flow/your-deployment'
```

### Dagster

```bash
# Start
dagster dev

# Run pipeline
dagster job execute -j your_job_name
```

## Directory Structure Quick View

```
lakehouse-template/
├── config/           # All configurations
│   ├── logging/     # Logging configs
│   ├── monitoring/  # Prometheus, Grafana
│   └── tools/       # Tool-specific configs
├── data/            # Data layers
│   ├── bronze/     # Raw data
│   ├── silver/     # Cleaned data
│   └── gold/       # Aggregated data
├── pipelines/       # Pipeline code
│   └── examples/   # Example implementations
├── docs/           # Documentation
└── scripts/        # Utility scripts
```

## Configuration Files Quick Reference

| File | Purpose |
|------|---------|
| `config/logging/logging.yaml` | Python logging |
| `config/logging/log4j.properties` | JVM logging |
| `config/monitoring/prometheus.yaml` | Metrics collection |
| `config/monitoring/alerts.yaml` | Alert rules |
| `config/tools/spark/spark-defaults.conf` | Spark settings |
| `config/tools/dbt/dbt_project.yml` | dbt project |
| `config/tools/airflow/airflow.cfg` | Airflow settings |
| `.env` | Environment variables |

## Environment Variables

```bash
# Core settings
export ENVIRONMENT=development
export LOG_LEVEL=INFO

# Spark
export SPARK_MASTER=local[*]
export SPARK_EXECUTOR_MEMORY=4g

# Database
export POSTGRES_HOST=localhost
export POSTGRES_USER=lakehouse
export POSTGRES_PASSWORD=your_password

# Cloud storage (AWS example)
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
export AWS_DEFAULT_REGION=us-east-1
```

## Logging Examples

### Python

```python
import logging
logger = logging.getLogger('lakehouse.ingestion')
logger.info('Starting ingestion')
logger.error('Error occurred', exc_info=True)
```

### Spark

```python
from pyspark.sql import SparkSession
spark = SparkSession.builder.appName("MyApp").getOrCreate()
spark.sparkContext.setLogLevel("INFO")
```

## Monitoring Examples

### Prometheus Metrics

```python
from prometheus_client import Counter, Histogram

# Define metrics
records = Counter('records_processed', 'Records processed', ['layer'])
duration = Histogram('processing_duration_seconds', 'Duration', ['layer'])

# Use metrics
records.labels(layer='bronze').inc(1000)
with duration.labels(layer='silver').time():
    process_data()
```

### Push to Gateway

```python
from prometheus_client import push_to_gateway
push_to_gateway('localhost:9091', job='batch_job', registry=registry)
```

## Data Quality Checks

```python
# Example quality check
def check_data_quality(df):
    total = df.count()
    nulls = df.filter(df.id.isNull()).count()
    null_rate = nulls / total
    
    if null_rate > 0.05:
        raise ValueError(f"High null rate: {null_rate}")
    
    return null_rate
```

## Common Patterns

### Incremental Load

```python
# Load only new data
df = spark.read.format("delta").load(bronze_path) \
    .filter(f"date >= '{last_processed_date}'")
```

### Deduplication

```python
from pyspark.sql.window import Window
from pyspark.sql.functions import row_number

window = Window.partitionBy("id").orderBy(col("timestamp").desc())
df_dedup = df.withColumn("row_num", row_number().over(window)) \
    .filter(col("row_num") == 1) \
    .drop("row_num")
```

### Error Handling

```python
try:
    result = process_data(df)
    logger.info(f"Processed {result.count()} records")
except Exception as e:
    logger.error(f"Processing failed: {str(e)}", exc_info=True)
    # Send alert
    raise
```

## Testing

### Local Test

```bash
# Test with small dataset
python pipelines/examples/spark_pipeline.py \
  --source-path data/test/sample.csv \
  --bronze-path data/test/bronze \
  --silver-path data/test/silver
```

### Data Validation

```bash
# Validate record counts
spark.read.format("delta").load("data/silver").count()

# Check schema
spark.read.format("delta").load("data/silver").printSchema()
```

## Troubleshooting

### Check Logs

```bash
# Application logs
tail -f logs/lakehouse.log

# Spark logs
tail -f $SPARK_HOME/logs/spark-*.log

# Airflow logs
tail -f $AIRFLOW_HOME/logs/scheduler/*.log
```

### Debug Mode

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
python your_pipeline.py
```

### Spark UI

```bash
# Access Spark UI
# http://localhost:4040 (when Spark is running)
```

### Common Issues

**Out of Memory:**
```bash
# Increase executor memory
export SPARK_EXECUTOR_MEMORY=8g
```

**Connection Timeout:**
```bash
# Check connectivity
nc -zv hostname port

# Check credentials
echo $DB_PASSWORD | wc -c  # Ensure not empty
```

**Slow Queries:**
```bash
# Check partition count
df.rdd.getNumPartitions()

# Repartition
df = df.repartition(200)
```

## Monitoring Dashboards

### Grafana

```bash
# Access Grafana
# http://localhost:3000
# Default: admin/admin

# Import dashboard
# Upload config/monitoring/grafana-dashboard.json
```

### Prometheus

```bash
# Access Prometheus
# http://localhost:9090

# Query examples
rate(lakehouse_ingestion_records_total[5m])
histogram_quantile(0.95, lakehouse_processing_duration_seconds_bucket)
```

## Production Checklist

- [ ] Environment variables externalized
- [ ] Secrets in secret manager (not in code)
- [ ] Logging configured and tested
- [ ] Monitoring dashboards created
- [ ] Alerts configured
- [ ] Backup procedures documented
- [ ] Access controls implemented
- [ ] Data quality checks in place
- [ ] Documentation updated
- [ ] Team trained

## Quick Links

- [Full Documentation](../README.md)
- [Architecture Guide](ARCHITECTURE.md)
- [Getting Started](GETTING_STARTED.md)
- [Tool Comparison](TOOL_COMPARISON.md)
- [Contributing](../CONTRIBUTING.md)

## Support

- GitHub Issues: Report bugs or request features
- Documentation: Check docs/ directory
- Examples: See pipelines/examples/
