# Lakehouse Template

A comprehensive, tool-agnostic template for building modern lakehouse data products with integrated logging and monitoring.

## 🎯 Overview

This template provides a production-ready foundation for implementing a lakehouse architecture using the **Medallion Architecture** pattern (Bronze-Silver-Gold layers). It's designed to be tool-agnostic, allowing you to choose the best tools for your specific requirements.

## ✨ Features

- **🏗️ Medallion Architecture**: Implements Bronze (raw), Silver (cleaned), and Gold (aggregated) data layers
- **🔧 Tool Agnostic**: Support for multiple data processing frameworks (Spark, dbt, etc.)
- **📊 Monitoring Ready**: Pre-configured Prometheus metrics and Grafana dashboards
- **📝 Logging Integrated**: Structured logging configurations for Python and JVM-based tools
- **🎭 Orchestration Options**: Example configurations for Airflow, Prefect, and Dagster
- **📚 Comprehensive Documentation**: Architecture guides and best practices
- **🔐 Security Focused**: Built-in considerations for data security and governance
- **📈 Scalable Design**: Patterns for horizontal and vertical scaling
- **🗂️ Unity Catalog**: Local governance solution with metadata management, lineage tracking, and audit logging

## 🚀 Quick Start

### 0. Test Drive (Tracer Bullet)

Start with a minimal end-to-end test to see the lakehouse architecture in action:

```bash
# Run the simple end-to-end test (no dependencies required)
bash scripts/run-e2e-test.sh

# Or run directly with Python
python3 tests/test_end_to_end.py

# Or run the pipeline standalone
python3 pipelines/simple_pipeline.py
```

This validates the Bronze → Silver → Gold flow using only Python standard library and local file storage. See [End-to-End Test Guide](docs/END_TO_END_TEST.md) for details.

### 0.1. Try Unity Catalog Governance

Experience end-to-end data governance with Unity Catalog:

```bash
# Run the governed pipeline with full governance tracking
python3 pipelines/governed_pipeline.py

# Explore the catalog using CLI
python3 governance/catalog_cli.py summary
python3 governance/catalog_cli.py describe silver customers
python3 governance/catalog_cli.py lineage gold customers_by_region
```

This demonstrates metadata management, lineage tracking, audit logging, and data quality monitoring. See [Unity Catalog Guide](docs/UNITY_CATALOG.md) for details.

### 1. Use This Template

Click the "Use this template" button on GitHub to create a new repository from this template.

### 2. Choose Your Tools

Select the tools that best fit your requirements:

| Category | Options |
|----------|---------|
| **Processing** | Apache Spark, dbt, Apache Flink |
| **Orchestration** | Apache Airflow, Prefect, Dagster |
| **Storage** | Delta Lake, Apache Iceberg, Apache Hudi |
| **Monitoring** | Prometheus + Grafana, Datadog, CloudWatch |

### 3. Configure

Update the configuration files in `config/tools/` for your chosen stack:

```bash
# Example: Configure for Spark + Airflow + Delta Lake
cp config/tools/spark/spark-defaults.conf /opt/spark/conf/
cp config/tools/airflow/airflow.cfg $AIRFLOW_HOME/
```

### 4. Customize

Modify the example pipelines in `pipelines/examples/` to match your data sources and business logic.

## 📁 Repository Structure

```
lakehouse-template/
├── config/                          # Configuration files
│   ├── logging/                     # Logging configurations
│   │   ├── logging.yaml            # Python logging config
│   │   ├── log4j.properties        # JVM logging config
│   │   └── README.md
│   ├── monitoring/                  # Monitoring configurations
│   │   ├── prometheus.yaml         # Prometheus scrape config
│   │   ├── grafana-dashboard.json  # Pre-built dashboard
│   │   ├── alerts.yaml             # Alert rules
│   │   └── README.md
│   └── tools/                       # Tool-specific configs
│       ├── spark/                   # Apache Spark configs
│       ├── dbt/                     # dbt project configs
│       ├── airflow/                 # Airflow configs
│       ├── prefect/                 # Prefect configs
│       └── dagster/                 # Dagster configs
├── data/                            # Data storage (local dev)
│   ├── bronze/                      # Raw data layer
│   ├── silver/                      # Cleaned data layer
│   └── gold/                        # Aggregated data layer
├── governance/                      # Unity Catalog governance module
│   ├── unity_catalog.py            # Main governance interface
│   ├── metadata_store.py           # Metadata management
│   ├── lineage_tracker.py          # Lineage tracking
│   ├── audit_logger.py             # Audit logging
│   ├── catalog_cli.py              # CLI tool
│   └── README.md                    # Governance documentation
├── pipelines/                       # Pipeline implementations
│   ├── simple_pipeline.py          # Basic pipeline
│   ├── governed_pipeline.py        # Pipeline with governance
│   └── examples/                    # Example pipelines
│       ├── spark_pipeline.py       # Spark example
│       ├── airflow_dag.py          # Airflow DAG example
│       └── dbt_example_model.sql   # dbt model example
├── docs/                            # Documentation
│   ├── ARCHITECTURE.md             # Architecture overview
│   └── UNITY_CATALOG.md            # Unity Catalog guide
└── README.md                        # This file
```

## 🏗️ Architecture

This template implements a **Medallion Architecture** with three layers:

```
Sources → Bronze (Raw) → Silver (Cleaned) → Gold (Aggregated) → Analytics
```

- **Bronze Layer**: Raw data as ingested from source systems
- **Silver Layer**: Cleaned, validated, and conformed data
- **Gold Layer**: Business-ready aggregates and metrics

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for detailed architecture documentation.

## 🔧 Tool Options

### Data Processing

#### Apache Spark
```bash
# Configure Spark with Delta Lake
spark-submit --conf spark.sql.extensions=io.delta.sql.DeltaSparkSessionExtension \
             --conf spark.sql.catalog.spark_catalog=org.apache.spark.sql.delta.catalog.DeltaCatalog \
             pipelines/examples/spark_pipeline.py
```

#### dbt
```bash
# Initialize dbt project
cd config/tools/dbt
dbt init
dbt run --models bronze silver gold
```

### Orchestration

#### Apache Airflow
```python
# See pipelines/examples/airflow_dag.py for complete example
from airflow import DAG
from airflow.operators.python import PythonOperator

with DAG('lakehouse_pipeline', ...) as dag:
    bronze = PythonOperator(task_id='bronze', ...)
    silver = PythonOperator(task_id='silver', ...)
    gold = PythonOperator(task_id='gold', ...)
    bronze >> silver >> gold
```

#### Prefect
```python
from prefect import flow, task

@task
def bronze_ingestion():
    ...

@task
def silver_transformation():
    ...

@flow
def lakehouse_pipeline():
    bronze_data = bronze_ingestion()
    silver_transformation(bronze_data)
```

#### Dagster
```python
from dagster import asset

@asset
def bronze_customers():
    ...

@asset
def silver_customers(bronze_customers):
    ...
```

### Storage Formats

#### Delta Lake
```python
# Write Delta table
df.write.format("delta").mode("overwrite").save("data/silver/customers")

# Read Delta table
df = spark.read.format("delta").load("data/silver/customers")
```

#### Apache Iceberg
```python
# Write Iceberg table
df.writeTo("catalog.db.table").using("iceberg").create()

# Read Iceberg table
df = spark.table("catalog.db.table")
```

## 📊 Monitoring & Observability

### Logging

Configure logging using the templates in `config/logging/`:

```python
import logging.config
import yaml

with open('config/logging/logging.yaml') as f:
    config = yaml.safe_load(f)
    logging.config.dictConfig(config)

logger = logging.getLogger('lakehouse')
logger.info('Pipeline started')
```

### Metrics

Expose metrics for Prometheus:

```python
from prometheus_client import Counter, Histogram

records_ingested = Counter('lakehouse_ingestion_records_total', 
                          'Records ingested', ['layer'])
processing_time = Histogram('lakehouse_processing_duration_seconds',
                           'Processing time', ['layer'])

records_ingested.labels(layer='bronze').inc(1000)
```

### Dashboards

Import the pre-built Grafana dashboard:

1. Open Grafana
2. Go to Dashboards → Import
3. Upload `config/monitoring/grafana-dashboard.json`

## 🔐 Security Best Practices

1. **Never commit secrets**: Use environment variables or secret managers
2. **Encrypt data**: At rest and in transit
3. **Implement RBAC**: Role-based access control for each layer
4. **Audit access**: Log all data access for compliance (see Unity Catalog)
5. **Data masking**: Mask PII in non-production environments

## 🗂️ Data Governance with Unity Catalog

Unity Catalog provides comprehensive governance for your lakehouse:

### Features

- **Metadata Management**: Centralized catalog of all tables, schemas, and columns
- **Lineage Tracking**: Automatic tracking of data flow through Bronze → Silver → Gold
- **Audit Logging**: Complete audit trail of all data access and operations
- **Data Quality**: Track quality checks and metrics over time

### Quick Example

```python
from pipelines.governed_pipeline import GovernedLakehousePipeline

# Use governed pipeline for automatic governance
with GovernedLakehousePipeline(user="admin") as pipeline:
    result = pipeline.run_full_pipeline(
        source_file="data/sample_customers.csv",
        dataset_name="customers",
        group_by_field="region"
    )
    
    # Show detailed governance information
    pipeline.show_table_info("silver", "customers")
```

### CLI Tools

```bash
# View governance summary
python3 governance/catalog_cli.py summary

# Describe a table
python3 governance/catalog_cli.py describe silver customers

# View lineage
python3 governance/catalog_cli.py lineage gold customers_by_region

# Check access history
python3 governance/catalog_cli.py access silver customers

# View quality checks
python3 governance/catalog_cli.py quality silver customers
```

See the **[Unity Catalog Guide](docs/UNITY_CATALOG.md)** for complete documentation.

## 📚 Documentation

- **[Unity Catalog Guide](docs/UNITY_CATALOG.md)** - Complete governance documentation
- **[End-to-End Test Guide](docs/END_TO_END_TEST.md)** - Tracer bullet implementation and usage
- [Quick Reference](docs/QUICK_REFERENCE.md) - Condensed cheat sheet for common tasks
- [Architecture Overview](docs/ARCHITECTURE.md) - Detailed architecture documentation
- [Getting Started](docs/GETTING_STARTED.md) - Step-by-step setup guide
- [Tool Comparison](docs/TOOL_COMPARISON.md) - Compare and choose the right tools
- [Logging Configuration](config/logging/README.md) - Logging setup guide
- [Monitoring Configuration](config/monitoring/README.md) - Monitoring setup guide

## 🛠️ Customization

### Adding a New Data Source

1. Create ingestion logic in `pipelines/`
2. Configure source connection in `config/`
3. Add logging for the new source
4. Update monitoring dashboards
5. Document the integration

### Adding a New Tool

1. Create configuration directory in `config/tools/[tool-name]/`
2. Add configuration templates
3. Create example pipeline in `pipelines/examples/`
4. Update README with usage instructions

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📝 License

This template is provided as-is for use in your projects.

## 🙏 Acknowledgments

This template is inspired by best practices from:
- Databricks Medallion Architecture
- Data Build Tool (dbt) patterns
- Cloud-native data platform architectures

## 📞 Support

For questions or issues:
1. Check the documentation in `docs/`
2. Review example implementations in `pipelines/examples/`
3. Open an issue on GitHub

## 🗺️ Roadmap

- [ ] Add more tool examples (Flink, Trino)
- [ ] Include data quality framework templates
- [ ] Add CI/CD pipeline examples
- [ ] Provide Terraform infrastructure templates
- [ ] Add real-time streaming examples
- [ ] Include ML feature store patterns

---

**Happy Data Engineering!** 🚀
