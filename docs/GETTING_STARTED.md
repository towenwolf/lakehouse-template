# Getting Started Guide

This guide will help you get started with the lakehouse template.

## Prerequisites

Before you begin, ensure you have:

- [ ] Git installed
- [ ] Python 3.8+ (for Python-based tools)
- [ ] JVM 11+ (for JVM-based tools like Spark)
- [ ] Docker (optional, for containerized deployments)
- [ ] Cloud account (AWS/Azure/GCP) or local storage setup

## Step-by-Step Setup

### 1. Create Your Repository

Use this template to create a new repository:

```bash
# Option A: Using GitHub UI
# Click "Use this template" button on GitHub

# Option B: Using GitHub CLI
gh repo create my-lakehouse --template towenwolf/lakehouse-template --public

# Clone your new repository
git clone https://github.com/your-username/my-lakehouse
cd my-lakehouse
```

### 2. Choose Your Tool Stack

Based on your requirements, select tools from each category:

**Processing:** Spark, dbt, or Flink  
**Orchestration:** Airflow, Prefect, or Dagster  
**Storage:** Delta Lake, Iceberg, or Hudi  
**Monitoring:** Prometheus, Datadog, or Cloud-native

See [TOOL_COMPARISON.md](TOOL_COMPARISON.md) for detailed comparisons.

### 3. Set Up Development Environment

#### Option A: Local Development (Python + dbt)

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install dbt-core dbt-postgres pyspark delta-spark prometheus-client

# Install dbt
cd config/tools/dbt
dbt init my_lakehouse
```

#### Option B: Local Development (Spark)

```bash
# Download and setup Spark
wget https://archive.apache.org/dist/spark/spark-3.5.0/spark-3.5.0-bin-hadoop3.tgz
tar -xvf spark-3.5.0-bin-hadoop3.tgz
export SPARK_HOME=$PWD/spark-3.5.0-bin-hadoop3
export PATH=$SPARK_HOME/bin:$PATH

# Copy Spark configuration
cp config/tools/spark/spark-defaults.conf $SPARK_HOME/conf/
```

#### Option C: Docker-based Development

```bash
# Create docker-compose.yml (example provided below)
docker-compose up -d
```

### 4. Configure Storage

#### Local Development (File System)

```bash
# Data directories already created
# data/bronze/
# data/silver/
# data/gold/

# Ensure permissions
chmod -R 755 data/
```

#### Cloud Storage (AWS S3)

```bash
# Configure AWS credentials
aws configure

# Create S3 buckets
aws s3 mb s3://my-lakehouse-bronze
aws s3 mb s3://my-lakehouse-silver
aws s3 mb s3://my-lakehouse-gold

# Update paths in your pipeline code
# bronze_path = "s3://my-lakehouse-bronze/"
# silver_path = "s3://my-lakehouse-silver/"
# gold_path = "s3://my-lakehouse-gold/"
```

#### Cloud Storage (Azure Blob)

```bash
# Create storage account and containers
az storage account create --name mylakehouse --resource-group mygroup
az storage container create --name bronze --account-name mylakehouse
az storage container create --name silver --account-name mylakehouse
az storage container create --name gold --account-name mylakehouse
```

#### Cloud Storage (GCP)

```bash
# Create GCS buckets
gsutil mb gs://my-lakehouse-bronze
gsutil mb gs://my-lakehouse-silver
gsutil mb gs://my-lakehouse-gold
```

### 5. Set Up Logging

```bash
# Create logs directory
mkdir -p logs

# Configure Python logging
python << EOF
import logging.config
import yaml

with open('config/logging/logging.yaml') as f:
    config = yaml.safe_load(f)
    logging.config.dictConfig(config)

logger = logging.getLogger('lakehouse')
logger.info('Logging configured successfully!')
EOF
```

### 6. Set Up Monitoring (Optional)

#### Using Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./config/monitoring/prometheus.yaml:/etc/prometheus/prometheus.yml
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
  
  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - ./config/monitoring/grafana-dashboard.json:/var/lib/grafana/dashboards/lakehouse.json
```

```bash
# Start monitoring stack
docker-compose up -d

# Access Grafana at http://localhost:3000
# Default credentials: admin/admin
```

### 7. Run Your First Pipeline

#### Example 1: Spark Pipeline

```bash
# Create sample data
cat > data/source/customers.csv << EOF
id,name,email,region
1,John Doe,john@example.com,US
2,Jane Smith,jane@example.com,EU
3,Bob Johnson,bob@example.com,US
EOF

# Run the pipeline
python pipelines/examples/spark_pipeline.py
```

#### Example 2: dbt Pipeline

```bash
# Configure dbt connection
cat > ~/.dbt/profiles.yml << EOF
lakehouse:
  target: dev
  outputs:
    dev:
      type: postgres
      host: localhost
      user: postgres
      password: password
      port: 5432
      dbname: lakehouse
      schema: public
      threads: 4
EOF

# Run dbt models
cd config/tools/dbt
dbt run --models bronze silver gold
```

### 8. Verify Setup

```bash
# Check data was created
ls -R data/bronze/
ls -R data/silver/
ls -R data/gold/

# Check logs
tail -f logs/lakehouse.log

# Check metrics (if Prometheus is running)
curl http://localhost:9090/api/v1/query?query=lakehouse_ingestion_records_total
```

## Common Development Workflows

### Daily Development

```bash
# 1. Pull latest changes
git pull origin main

# 2. Create feature branch
git checkout -b feature/new-pipeline

# 3. Make changes to pipeline
vim pipelines/my_new_pipeline.py

# 4. Test locally
python pipelines/my_new_pipeline.py

# 5. Run quality checks
# (add linting, testing as needed)

# 6. Commit and push
git add pipelines/my_new_pipeline.py
git commit -m "Add new pipeline for X"
git push origin feature/new-pipeline

# 7. Create pull request
```

### Testing Changes

```bash
# Test with sample data
python pipelines/examples/spark_pipeline.py \
  --source-path data/test/sample.csv \
  --bronze-path data/test/bronze \
  --silver-path data/test/silver \
  --gold-path data/test/gold

# Validate data quality
python << EOF
from pyspark.sql import SparkSession
spark = SparkSession.builder.getOrCreate()
df = spark.read.format("delta").load("data/test/silver")
print(f"Record count: {df.count()}")
print(f"Schema: {df.schema}")
EOF
```

### Debugging

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Run pipeline with verbose output
python pipelines/examples/spark_pipeline.py --verbose

# Check Spark UI (when running)
# http://localhost:4040

# Check application logs
tail -f logs/lakehouse.log | grep ERROR
```

## Environment Setup

### Development Environment

```bash
# .env.development
LOG_LEVEL=DEBUG
SPARK_MASTER=local[*]
DATA_PATH=/local/data
MONITORING_ENABLED=false
```

### Production Environment

```bash
# .env.production
LOG_LEVEL=INFO
SPARK_MASTER=yarn
DATA_PATH=s3://my-lakehouse-prod
MONITORING_ENABLED=true
PROMETHEUS_GATEWAY=monitoring.example.com:9091
```

## Next Steps

1. **Customize the Template**
   - Modify pipeline examples for your data sources
   - Adjust configuration for your infrastructure
   - Add data quality checks specific to your domain

2. **Set Up CI/CD**
   - Add GitHub Actions or GitLab CI
   - Implement automated testing
   - Deploy to staging/production environments

3. **Implement Governance**
   - Set up data catalog (AWS Glue, Azure Purview)
   - Implement access controls
   - Add data lineage tracking

4. **Scale Up**
   - Move to managed services (Databricks, EMR, etc.)
   - Implement auto-scaling
   - Optimize for cost and performance

5. **Add Advanced Features**
   - Real-time streaming pipelines
   - Machine learning feature store
   - Data quality monitoring
   - Automated alerting

## Troubleshooting

### Common Issues

**Issue: Spark job fails with OutOfMemory**
```bash
# Solution: Increase executor memory
export SPARK_EXECUTOR_MEMORY=8g
# Or update spark-defaults.conf
```

**Issue: Permission denied on data directories**
```bash
# Solution: Fix permissions
chmod -R 755 data/
```

**Issue: Delta Lake version conflicts**
```bash
# Solution: Ensure consistent versions
pip install delta-spark==2.4.0  # Match with Spark version
```

**Issue: Logs not appearing**
```bash
# Solution: Create logs directory and check permissions
mkdir -p logs
chmod 755 logs
```

## Resources

- [Architecture Documentation](ARCHITECTURE.md)
- [Tool Comparison Guide](TOOL_COMPARISON.md)
- [Configuration README](../config/logging/README.md)
- [Monitoring README](../config/monitoring/README.md)

## Getting Help

- Review example pipelines in `pipelines/examples/`
- Check tool-specific documentation in `config/tools/`
- Open an issue on GitHub
- Consult the [Architecture Guide](ARCHITECTURE.md)

## Checklist

Before moving to production, ensure:

- [ ] All configurations are externalized (no hardcoded values)
- [ ] Secrets are stored securely (not in Git)
- [ ] Logging is configured and tested
- [ ] Monitoring dashboards are set up
- [ ] Data quality checks are in place
- [ ] Backup and recovery procedures are documented
- [ ] Access controls are implemented
- [ ] Documentation is up to date
- [ ] CI/CD pipeline is configured
- [ ] Team is trained on the system
