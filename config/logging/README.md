# Logging Configuration

This directory contains logging configuration templates for various tools and frameworks.

## Available Configurations

### logging.yaml
Python-based logging configuration compatible with:
- Python's logging module
- Apache Airflow
- Prefect
- Dagster
- Custom Python applications

**Usage:**
```python
import logging.config
import yaml

with open('config/logging/logging.yaml', 'r') as f:
    config = yaml.safe_load(f)
    logging.config.dictConfig(config)

logger = logging.getLogger('lakehouse')
logger.info('Pipeline started')
```

### log4j.properties
Java/Scala-based logging configuration compatible with:
- Apache Spark
- Apache Flink
- Apache Kafka
- Java applications

**Usage:**
For Spark, set the configuration path:
```bash
spark-submit --conf "spark.driver.extraJavaOptions=-Dlog4j.configuration=file:config/logging/log4j.properties" your_app.py
```

## Log Levels

- **DEBUG**: Detailed information for diagnosing problems
- **INFO**: General informational messages
- **WARNING**: Indication that something unexpected happened
- **ERROR**: Serious problem that prevented a function from executing
- **CRITICAL**: Very serious error that may cause the application to abort

## Log Structure

Logs are organized by component:
- `lakehouse.ingestion`: Data ingestion operations
- `lakehouse.transformation`: Data transformation operations
- `lakehouse.quality`: Data quality checks and validation

## Best Practices

1. **Use appropriate log levels**: Don't log everything at DEBUG in production
2. **Include context**: Add relevant metadata (job_id, batch_id, etc.)
3. **Rotate logs**: Configure log rotation to prevent disk space issues
4. **Structure your logs**: Use JSON format for easier parsing and analysis
5. **Monitor log volumes**: Excessive logging can impact performance
6. **Sanitize sensitive data**: Never log passwords, API keys, or PII

## Integration with Monitoring

Logs can be shipped to various monitoring systems:
- Elasticsearch/OpenSearch (via Filebeat or Logstash)
- Splunk
- CloudWatch (AWS)
- Stackdriver (GCP)
- Azure Monitor
- Datadog
- New Relic

See the `config/monitoring` directory for monitoring integration examples.
