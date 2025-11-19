# Monitoring Configuration

This directory contains monitoring configuration templates for lakehouse observability.

## Available Configurations

### prometheus.yaml
Prometheus configuration for metrics collection from various lakehouse components.

**Supports:**
- Apache Spark (native metrics and JMX)
- Python applications (via prometheus_client)
- Apache Airflow
- System metrics (via node_exporter)
- Custom application metrics

**Usage:**
```bash
prometheus --config.file=config/monitoring/prometheus.yaml
```

### grafana-dashboard.json
Pre-built Grafana dashboard for visualizing lakehouse metrics.

**Key Visualizations:**
- Data ingestion rate
- Pipeline success rate
- Data quality scores
- Processing time by layer
- Error rates

**Import:**
1. Open Grafana
2. Go to Dashboards → Import
3. Upload `grafana-dashboard.json`

### alerts.yaml
Prometheus alert rules for proactive monitoring.

**Alert Categories:**
- **HighErrorRate**: Detects unusual error rates
- **PipelineFailure**: Critical pipeline failures
- **DataQualityDegradation**: Data quality below threshold
- **SlowProcessing**: Performance degradation
- **StaleData**: Data freshness issues
- **LowIngestionRate**: Ingestion anomalies
- **HighDiskUsage**: Storage capacity warnings
- **HighMemoryUsage**: Memory pressure

## Key Metrics to Monitor

### Data Ingestion
- `lakehouse_ingestion_records_total`: Total records ingested
- `lakehouse_ingestion_bytes_total`: Total bytes ingested
- `lakehouse_ingestion_duration_seconds`: Ingestion duration

### Data Quality
- `lakehouse_data_quality_score`: Quality score (0-1)
- `lakehouse_validation_failures_total`: Failed validations
- `lakehouse_null_count`: Null value counts

### Pipeline Performance
- `lakehouse_pipeline_status`: Pipeline execution status
- `lakehouse_processing_duration_seconds`: Processing time
- `lakehouse_pipeline_success_total`: Successful pipeline runs
- `lakehouse_pipeline_failure_total`: Failed pipeline runs

### Resource Usage
- `lakehouse_cpu_usage_percent`: CPU utilization
- `lakehouse_memory_usage_percent`: Memory utilization
- `lakehouse_disk_usage_percent`: Disk utilization

### Data Freshness
- `lakehouse_last_update_timestamp`: Last update timestamp
- `lakehouse_record_count`: Current record count by layer

## Tool-Specific Integration

### Apache Spark
```python
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway

registry = CollectorRegistry()
g = Gauge('lakehouse_processing_duration_seconds', 'Processing time', registry=registry)

# Your Spark job
start = time.time()
# ... process data ...
duration = time.time() - start

g.set(duration)
push_to_gateway('localhost:9091', job='spark-job', registry=registry)
```

### Python/Airflow
```python
from prometheus_client import Counter, Histogram
import time

ingestion_counter = Counter('lakehouse_ingestion_records_total', 'Records ingested', ['layer', 'source'])
processing_time = Histogram('lakehouse_processing_duration_seconds', 'Processing time', ['layer'])

@processing_time.labels(layer='bronze').time()
def process_bronze_data():
    # ... processing logic ...
    ingestion_counter.labels(layer='bronze', source='api').inc(1000)
```

### dbt
Use dbt artifacts and exposures to track model execution:
```yaml
# In dbt project
exposures:
  - name: lakehouse_metrics
    type: dashboard
    maturity: high
    url: http://grafana/d/lakehouse
    description: Lakehouse monitoring dashboard
    depends_on:
      - ref('bronze_customers')
      - ref('silver_orders')
```

## Integration with Cloud Providers

### AWS CloudWatch
```python
import boto3

cloudwatch = boto3.client('cloudwatch')
cloudwatch.put_metric_data(
    Namespace='Lakehouse',
    MetricData=[{
        'MetricName': 'IngestionRate',
        'Value': 1000,
        'Unit': 'Count',
        'Dimensions': [{'Name': 'Layer', 'Value': 'Bronze'}]
    }]
)
```

### Google Cloud Monitoring
```python
from google.cloud import monitoring_v3

client = monitoring_v3.MetricServiceClient()
series = monitoring_v3.TimeSeries()
series.metric.type = 'custom.googleapis.com/lakehouse/ingestion_rate'
# ... configure and write metric
```

### Azure Monitor
```python
from azure.monitor.opentelemetry import configure_azure_monitor
from opentelemetry import metrics

configure_azure_monitor()
meter = metrics.get_meter(__name__)
counter = meter.create_counter("lakehouse.ingestion.records")
counter.add(1000, {"layer": "bronze"})
```

## Best Practices

1. **Use labels wisely**: Don't create too many label combinations (cardinality)
2. **Set appropriate retention**: Balance storage and query performance
3. **Define SLOs**: Set Service Level Objectives for critical metrics
4. **Alert on symptoms, not causes**: Focus on user impact
5. **Avoid alert fatigue**: Fine-tune thresholds and use proper severity levels
6. **Document runbooks**: Include remediation steps in alert annotations
7. **Regular review**: Periodically review and update alert rules
8. **Test alerts**: Verify alerts trigger correctly before relying on them

## Additional Tools

Consider integrating with:
- **OpenTelemetry**: Unified observability framework
- **Datadog**: Full-stack monitoring and APM
- **New Relic**: Application performance monitoring
- **ELK Stack**: Elasticsearch, Logstash, Kibana for log analysis
- **Jaeger**: Distributed tracing
- **Sentry**: Error tracking and monitoring
