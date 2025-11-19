# Tool Configurations

This directory contains configuration templates for various data engineering tools that can be used with this lakehouse template.

## Available Tool Configurations

### Data Processing

#### Apache Spark (`spark/`)
Configuration for distributed data processing with Apache Spark.

**Files:**
- `spark-defaults.conf` - Spark configuration with Delta Lake support

**Key Features:**
- Delta Lake integration
- Adaptive query execution
- Dynamic resource allocation
- Prometheus metrics export
- Cloud storage configurations (S3, Azure, GCS)

**Usage:**
```bash
cp spark/spark-defaults.conf $SPARK_HOME/conf/
spark-submit --master yarn your_pipeline.py
```

#### dbt (`dbt/`)
Configuration for SQL-based transformations with dbt.

**Files:**
- `dbt_project.yml` - Project configuration with bronze/silver/gold layers
- `profiles.yml` - Connection profiles for various warehouses

**Supported Warehouses:**
- Snowflake
- Databricks
- BigQuery
- Redshift
- PostgreSQL
- Spark/Hive
- DuckDB

**Usage:**
```bash
cd dbt/
dbt init my_project
dbt run --models bronze silver gold
```

### Orchestration

#### Apache Airflow (`airflow/`)
Configuration for workflow orchestration with Apache Airflow.

**Files:**
- `airflow.cfg` - Airflow configuration

**Key Features:**
- LocalExecutor configuration (change to Celery/Kubernetes for scale)
- PostgreSQL backend
- Metrics export to StatsD
- Logging configuration

**Usage:**
```bash
export AIRFLOW_HOME=/opt/airflow
cp airflow/airflow.cfg $AIRFLOW_HOME/
airflow db init
airflow webserver
```

#### Prefect (`prefect/`)
Configuration for modern Python workflow orchestration.

**Files:**
- `prefect.yaml` - Prefect configuration

**Key Features:**
- Work pool configuration
- Storage backends (local, S3, Azure, GCS)
- Infrastructure options (process, Docker, Kubernetes)
- Logging and notifications

**Usage:**
```bash
export PREFECT_HOME=/opt/prefect
prefect config set PREFECT_API_URL=http://localhost:4200/api
prefect server start
```

#### Dagster (`dagster/`)
Configuration for asset-based orchestration.

**Files:**
- `dagster.yaml` - Dagster instance configuration

**Key Features:**
- Run coordinator for concurrency control
- PostgreSQL storage backend
- Run launcher configuration
- Retention policies

**Usage:**
```bash
export DAGSTER_HOME=/opt/dagster
cp dagster/dagster.yaml $DAGSTER_HOME/
dagster dev
```

## Choosing the Right Tools

### By Use Case

**Analytics-Heavy Workload:**
- Processing: dbt
- Orchestration: Prefect or Dagster
- Best for: SQL-savvy teams, analytics transformations

**Big Data Processing:**
- Processing: Apache Spark
- Orchestration: Apache Airflow
- Best for: Large-scale data (TB-PB), complex transformations

**Real-Time Streaming:**
- Processing: Apache Flink
- Orchestration: Airflow + Kubernetes
- Best for: Low-latency requirements, event processing

**Hybrid Cloud:**
- Processing: Spark or dbt
- Orchestration: Prefect
- Best for: Multi-cloud, hybrid on-prem/cloud deployments

### By Team Size

**Small Team (< 5 people):**
- dbt + Prefect + Prometheus/Grafana
- Easier to learn and maintain
- Lower operational overhead

**Medium Team (5-20 people):**
- Spark + Airflow + Prometheus/Grafana
- More flexibility and power
- Reasonable operational complexity

**Large Team (20+ people):**
- Spark + Airflow + Datadog/Commercial
- Enterprise features and support
- Dedicated platform team

## Configuration Tips

### 1. Environment-Specific Configs

Create separate configurations for each environment:

```bash
config/tools/spark/
├── spark-defaults.conf          # Base configuration
├── spark-defaults-dev.conf      # Development overrides
├── spark-defaults-staging.conf  # Staging overrides
└── spark-defaults-prod.conf     # Production overrides
```

### 2. Use Environment Variables

Replace sensitive values with environment variables:

```properties
# Bad (hardcoded)
spark.hadoop.fs.s3a.access.key=AKIAIOSFODNN7EXAMPLE

# Good (environment variable)
spark.hadoop.fs.s3a.access.key=${AWS_ACCESS_KEY_ID}
```

### 3. Version Control

Always version control your configurations:

```bash
git add config/tools/
git commit -m "Update Spark configuration for new cluster"
```

### 4. Documentation

Document any customizations:

```yaml
# Custom configuration for handling large partitions
# Increased from default 200 to 400 for better parallelism
# See: https://spark.apache.org/docs/latest/sql-performance-tuning.html
spark.sql.shuffle.partitions: 400
```

## Integration Patterns

### Spark + Airflow

```python
# airflow_dag.py
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator

spark_task = SparkSubmitOperator(
    task_id='process_data',
    application='pipelines/spark_pipeline.py',
    conf={'spark.executor.memory': '4g'},
)
```

### dbt + Prefect

```python
# prefect_flow.py
from prefect import flow
from prefect_dbt import DbtCoreOperation

@flow
def dbt_flow():
    DbtCoreOperation(
        commands=["dbt run --models bronze silver gold"],
        project_dir="config/tools/dbt",
    ).run()
```

### Spark + Dagster

```python
# dagster_pipeline.py
from dagster import asset, Definitions
from dagster_pyspark import pyspark_resource

@asset
def bronze_data(pyspark: pyspark_resource):
    return pyspark.spark_session.read.csv("data/source")

defs = Definitions(
    assets=[bronze_data],
    resources={"pyspark": pyspark_resource}
)
```

## Migration Guides

### From Airflow to Prefect

1. Convert DAGs to Flows:
   - `DAG` → `@flow`
   - `PythonOperator` → `@task`
   - `task1 >> task2` → automatic from function calls

2. Update configuration:
   - Move from `airflow.cfg` to `prefect.yaml`
   - Update connection strings
   - Migrate variables and secrets

3. Test incrementally:
   - Run Prefect alongside Airflow
   - Migrate one pipeline at a time
   - Validate results match

### From Spark to dbt

1. Identify SQL-only transformations
2. Convert PySpark to dbt SQL:
   ```python
   # Spark
   df.groupBy("customer_id").count()
   
   # dbt
   select customer_id, count(*) from customers group by customer_id
   ```
3. Keep complex logic in Spark
4. Use dbt for final analytics layers

## Best Practices

1. **Start Simple**: Begin with basic configurations and add complexity as needed
2. **Monitor Everything**: Enable metrics and logging from day one
3. **Automate Testing**: Test configuration changes before deploying
4. **Document Decisions**: Keep a decision log for configuration choices
5. **Review Regularly**: Revisit configurations quarterly to optimize
6. **Security First**: Never commit secrets, use secret managers
7. **Version Everything**: Track all configuration changes in Git

## Common Pitfalls

❌ **Don't:**
- Hardcode credentials in configuration files
- Use production configs in development
- Skip testing after configuration changes
- Ignore resource limits
- Copy configs without understanding them

✅ **Do:**
- Use environment-specific configurations
- Test changes in lower environments first
- Document all customizations
- Monitor resource usage
- Start with recommended defaults

## Getting Help

- Check tool-specific documentation:
  - [Apache Spark Docs](https://spark.apache.org/docs/latest/)
  - [dbt Docs](https://docs.getdbt.com/)
  - [Airflow Docs](https://airflow.apache.org/docs/)
  - [Prefect Docs](https://docs.prefect.io/)
  - [Dagster Docs](https://docs.dagster.io/)

- Review example pipelines in `pipelines/examples/`
- See [TOOL_COMPARISON.md](../../docs/TOOL_COMPARISON.md) for detailed comparisons
- Open an issue on GitHub for template-specific questions

## Contributing

To add a new tool configuration:

1. Create directory: `config/tools/[tool-name]/`
2. Add configuration files with examples
3. Create README in the tool directory
4. Add entry to this README
5. Create example pipeline in `pipelines/examples/`
6. Update main README.md
7. Submit pull request
