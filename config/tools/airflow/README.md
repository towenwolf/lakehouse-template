# Apache Airflow Configuration

This directory contains configuration templates for Apache Airflow orchestration.

## Files

- `airflow.cfg` - Main Airflow configuration file

## Setup Instructions

### 1. Install Airflow

```bash
# Install Airflow with desired providers
pip install apache-airflow==2.7.0 \
    apache-airflow-providers-apache-spark \
    apache-airflow-providers-postgres

# Or with constraints for reproducibility
AIRFLOW_VERSION=2.7.0
PYTHON_VERSION="$(python --version | cut -d " " -f 2 | cut -d "." -f 1-2)"
CONSTRAINT_URL="https://raw.githubusercontent.com/apache/airflow/constraints-${AIRFLOW_VERSION}/constraints-${PYTHON_VERSION}.txt"
pip install "apache-airflow==${AIRFLOW_VERSION}" --constraint "${CONSTRAINT_URL}"
```

### 2. Set Airflow Home

```bash
export AIRFLOW_HOME=/opt/airflow
mkdir -p $AIRFLOW_HOME
```

### 3. Copy Configuration

```bash
cp config/tools/airflow/airflow.cfg $AIRFLOW_HOME/
```

### 4. Initialize Database

```bash
# Initialize the database
airflow db init

# Create admin user
airflow users create \
    --username admin \
    --firstname Admin \
    --lastname User \
    --role Admin \
    --email admin@example.com
```

### 5. Copy DAGs

```bash
# Create DAGs directory
mkdir -p $AIRFLOW_HOME/dags

# Copy example DAG
cp pipelines/examples/airflow_dag.py $AIRFLOW_HOME/dags/
```

### 6. Start Airflow

```bash
# Start the web server (in one terminal)
airflow webserver --port 8080

# Start the scheduler (in another terminal)
airflow scheduler
```

## Configuration Options

### Executors

The configuration uses `LocalExecutor` by default. For production, consider:

**CeleryExecutor** (distributed):
```ini
[core]
executor = CeleryExecutor

[celery]
broker_url = redis://redis:6379/0
result_backend = db+postgresql://airflow:airflow@postgres/airflow
```

**KubernetesExecutor** (container-native):
```ini
[core]
executor = KubernetesExecutor

[kubernetes]
namespace = airflow
worker_container_repository = apache/airflow
worker_container_tag = 2.7.0
```

### Remote Logging

Enable remote logging to S3, GCS, or Azure:

```ini
[logging]
remote_logging = True
remote_base_log_folder = s3://my-bucket/airflow/logs
remote_log_conn_id = aws_default
```

### Monitoring

Enable metrics export:

```ini
[metrics]
statsd_on = True
statsd_host = localhost
statsd_port = 8125
statsd_prefix = airflow
```

## Docker Deployment

Create `docker-compose.yml`:

```yaml
version: '3'
services:
  postgres:
    image: postgres:13
    environment:
      POSTGRES_USER: airflow
      POSTGRES_PASSWORD: airflow
      POSTGRES_DB: airflow

  redis:
    image: redis:latest

  airflow-webserver:
    image: apache/airflow:2.7.0
    depends_on:
      - postgres
      - redis
    environment:
      AIRFLOW__CORE__EXECUTOR: CeleryExecutor
      AIRFLOW__DATABASE__SQL_ALCHEMY_CONN: postgresql+psycopg2://airflow:airflow@postgres/airflow
      AIRFLOW__CELERY__BROKER_URL: redis://redis:6379/0
    volumes:
      - ./dags:/opt/airflow/dags
      - ./logs:/opt/airflow/logs
      - ./config/tools/airflow/airflow.cfg:/opt/airflow/airflow.cfg
    ports:
      - "8080:8080"
    command: webserver

  airflow-scheduler:
    image: apache/airflow:2.7.0
    depends_on:
      - postgres
      - redis
    environment:
      AIRFLOW__CORE__EXECUTOR: CeleryExecutor
      AIRFLOW__DATABASE__SQL_ALCHEMY_CONN: postgresql+psycopg2://airflow:airflow@postgres/airflow
      AIRFLOW__CELERY__BROKER_URL: redis://redis:6379/0
    volumes:
      - ./dags:/opt/airflow/dags
      - ./logs:/opt/airflow/logs
      - ./config/tools/airflow/airflow.cfg:/opt/airflow/airflow.cfg
    command: scheduler

  airflow-worker:
    image: apache/airflow:2.7.0
    depends_on:
      - postgres
      - redis
    environment:
      AIRFLOW__CORE__EXECUTOR: CeleryExecutor
      AIRFLOW__DATABASE__SQL_ALCHEMY_CONN: postgresql+psycopg2://airflow:airflow@postgres/airflow
      AIRFLOW__CELERY__BROKER_URL: redis://redis:6379/0
    volumes:
      - ./dags:/opt/airflow/dags
      - ./logs:/opt/airflow/logs
      - ./config/tools/airflow/airflow.cfg:/opt/airflow/airflow.cfg
    command: celery worker
```

## Best Practices

1. **Use Connections**: Store credentials in Airflow connections, not in code
2. **Idempotent Tasks**: Design tasks to be safely re-runnable
3. **Task Dependencies**: Use `>>` or `<<` for clear dependency chains
4. **Monitoring**: Enable metrics and set up alerts for failures
5. **Resource Limits**: Set appropriate pool sizes and concurrency limits
6. **Version Control**: Keep DAGs in version control
7. **Testing**: Test DAGs locally before deploying
8. **Documentation**: Document complex DAGs and task logic

## Troubleshooting

**Scheduler not picking up DAGs:**
- Check `dags_folder` path in config
- Verify DAG file has no syntax errors
- Check file permissions

**Tasks stuck in queued state:**
- Increase `parallelism` and `dag_concurrency`
- Check executor capacity (LocalExecutor limited to one host)
- Consider CeleryExecutor for distributed execution

**Web UI slow or unresponsive:**
- Reduce `dag_dir_list_interval`
- Archive old DAG runs
- Optimize database queries

## Resources

- [Airflow Documentation](https://airflow.apache.org/docs/)
- [Best Practices Guide](https://airflow.apache.org/docs/apache-airflow/stable/best-practices.html)
- [Airflow Providers](https://airflow.apache.org/docs/apache-airflow-providers/)
