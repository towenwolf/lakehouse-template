# Unity Catalog - Governance Module

This module provides end-to-end governance capabilities for the lakehouse template.

## Overview

Unity Catalog is a unified governance solution that captures:
- **Metadata**: Complete catalog of tables, schemas, and columns
- **Lineage**: Data flow tracking through Bronze → Silver → Gold
- **Audit**: Access logging and compliance tracking
- **Quality**: Data quality metrics and monitoring

## Components

### `unity_catalog.py`
Main interface for governance operations. Coordinates metadata management, lineage tracking, and audit logging.

**Key Features:**
- Register tables with full metadata
- Track data transformations
- Log access and quality checks
- Query lineage and history
- Export catalog metadata

**Example:**
```python
from governance.unity_catalog import UnityCatalog

with UnityCatalog(user="admin") as catalog:
    # Register a table
    catalog.register_table(
        layer="bronze",
        table_name="customers",
        location="data/bronze/customers.json",
        columns=[{'name': 'id', 'type': 'integer'}],
        row_count=1000
    )
    
    # Get table info
    info = catalog.get_table_info("bronze", "customers")
```

### `metadata_store.py`
SQLite-based storage for catalog metadata.

**Tables:**
- `catalogs`: Top-level namespaces
- `schemas`: Databases (bronze, silver, gold)
- `tables`: Table definitions and statistics
- `columns`: Column-level metadata

**Example:**
```python
from governance.metadata_store import MetadataStore

with MetadataStore() as store:
    # Create catalog
    store.create_catalog("lakehouse", "Main catalog")
    
    # Create schema
    store.create_schema("lakehouse", "bronze", "/data/bronze")
    
    # Register table
    store.register_table(
        "lakehouse", "bronze", "events",
        "raw", "/data/bronze/events.json", "json"
    )
```

### `lineage_tracker.py`
Tracks data lineage and pipeline execution.

**Tables:**
- `lineage`: Table-to-table relationships
- `pipeline_runs`: Pipeline execution tracking
- `data_flows`: Actual data movement metrics

**Example:**
```python
from governance.lineage_tracker import LineageTracker

with LineageTracker() as tracker:
    # Register lineage
    tracker.register_lineage(
        "lakehouse.bronze.source",
        "lakehouse.silver.target",
        "cleaning",
        "my_pipeline"
    )
    
    # Track pipeline run
    run_id = tracker.start_pipeline_run("my_pipeline")
    # ... do work ...
    tracker.complete_pipeline_run(run_id, "success")
    
    # Query lineage
    upstream = tracker.get_upstream_lineage("lakehouse.silver.target")
```

### `audit_logger.py`
Comprehensive audit logging for compliance.

**Tables:**
- `audit_log`: General catalog operations
- `data_access_log`: Table access tracking
- `quality_log`: Data quality checks

**Example:**
```python
from governance.audit_logger import AuditLogger

with AuditLogger() as logger:
    # Log data access
    logger.log_data_access(
        user="admin",
        table_name="lakehouse.silver.customers",
        access_type="select",
        rows_affected=100
    )
    
    # Log quality check
    logger.log_quality_check(
        table_name="lakehouse.silver.customers",
        check_name="deduplication",
        check_type="uniqueness",
        status="passed",
        passed_count=990,
        failed_count=10
    )
```

### `catalog_cli.py`
Command-line interface for catalog management.

**Commands:**
- `summary`: Show governance summary
- `list`: List tables in a layer
- `describe`: Describe table details
- `lineage`: Show table lineage
- `access`: Show access history
- `quality`: Show quality checks
- `export`: Export catalog to JSON

**Example:**
```bash
# Show summary
python3 governance/catalog_cli.py summary

# Describe a table
python3 governance/catalog_cli.py describe silver customers

# Show lineage
python3 governance/catalog_cli.py lineage gold customers_by_region
```

## Database Schema

The catalog uses a SQLite database (`catalog.db`) with the following structure:

```sql
-- Catalogs
CREATE TABLE catalogs (
    catalog_id INTEGER PRIMARY KEY,
    catalog_name TEXT UNIQUE,
    description TEXT,
    owner TEXT,
    created_at TEXT,
    updated_at TEXT,
    properties TEXT
);

-- Schemas
CREATE TABLE schemas (
    schema_id INTEGER PRIMARY KEY,
    catalog_id INTEGER,
    schema_name TEXT,
    description TEXT,
    location TEXT,
    owner TEXT,
    created_at TEXT,
    updated_at TEXT,
    properties TEXT,
    FOREIGN KEY (catalog_id) REFERENCES catalogs(catalog_id)
);

-- Tables
CREATE TABLE tables (
    table_id INTEGER PRIMARY KEY,
    schema_id INTEGER,
    table_name TEXT,
    table_type TEXT,
    description TEXT,
    location TEXT,
    format TEXT,
    owner TEXT,
    created_at TEXT,
    updated_at TEXT,
    row_count INTEGER,
    size_bytes INTEGER,
    properties TEXT,
    FOREIGN KEY (schema_id) REFERENCES schemas(schema_id)
);

-- Columns
CREATE TABLE columns (
    column_id INTEGER PRIMARY KEY,
    table_id INTEGER,
    column_name TEXT,
    data_type TEXT,
    nullable BOOLEAN,
    description TEXT,
    position INTEGER,
    properties TEXT,
    FOREIGN KEY (table_id) REFERENCES tables(table_id)
);

-- Lineage
CREATE TABLE lineage (
    lineage_id INTEGER PRIMARY KEY,
    source_table TEXT,
    target_table TEXT,
    transformation_type TEXT,
    pipeline_name TEXT,
    created_at TEXT,
    metadata TEXT
);

-- Pipeline Runs
CREATE TABLE pipeline_runs (
    run_id INTEGER PRIMARY KEY,
    pipeline_name TEXT,
    run_type TEXT,
    status TEXT,
    started_at TEXT,
    completed_at TEXT,
    error_message TEXT,
    metadata TEXT
);

-- Data Flows
CREATE TABLE data_flows (
    flow_id INTEGER PRIMARY KEY,
    run_id INTEGER,
    source_table TEXT,
    target_table TEXT,
    records_read INTEGER,
    records_written INTEGER,
    bytes_read INTEGER,
    bytes_written INTEGER,
    duration_seconds REAL,
    timestamp TEXT,
    FOREIGN KEY (run_id) REFERENCES pipeline_runs(run_id)
);

-- Audit Log
CREATE TABLE audit_log (
    audit_id INTEGER PRIMARY KEY,
    timestamp TEXT,
    user TEXT,
    action TEXT,
    resource_type TEXT,
    resource_name TEXT,
    status TEXT,
    ip_address TEXT,
    session_id TEXT,
    details TEXT
);

-- Data Access Log
CREATE TABLE data_access_log (
    access_id INTEGER PRIMARY KEY,
    timestamp TEXT,
    user TEXT,
    table_name TEXT,
    access_type TEXT,
    rows_affected INTEGER,
    query TEXT,
    status TEXT,
    duration_ms INTEGER,
    details TEXT
);

-- Quality Log
CREATE TABLE quality_log (
    quality_id INTEGER PRIMARY KEY,
    timestamp TEXT,
    table_name TEXT,
    check_name TEXT,
    check_type TEXT,
    status TEXT,
    passed_count INTEGER,
    failed_count INTEGER,
    error_rate REAL,
    details TEXT
);
```

## Quick Start

### 1. Basic Usage

```python
from governance.unity_catalog import UnityCatalog

# Initialize catalog
catalog = UnityCatalog(user="admin")

# Register a table
catalog.register_table(
    layer="bronze",
    table_name="events",
    location="data/bronze/events.json",
    columns=[
        {'name': 'id', 'type': 'string', 'nullable': False},
        {'name': 'timestamp', 'type': 'timestamp', 'nullable': False}
    ]
)

# Get governance summary
summary = catalog.get_governance_summary()
print(f"Total tables: {summary['total_tables']}")

# Close connections
catalog.close()
```

### 2. With Context Manager

```python
from governance.unity_catalog import UnityCatalog

with UnityCatalog(user="admin") as catalog:
    # All operations here
    catalog.register_table(...)
# Automatically closed
```

### 3. Using Governed Pipeline

```python
from pipelines.governed_pipeline import GovernedLakehousePipeline

with GovernedLakehousePipeline(user="admin") as pipeline:
    # Governance is automatic
    result = pipeline.run_full_pipeline(
        source_file="data/sample.csv",
        dataset_name="sample",
        group_by_field="category"
    )
```

## Testing

Run the test suite:

```bash
python3 tests/test_unity_catalog.py
```

Tests cover:
- Metadata store operations
- Lineage tracking
- Audit logging
- Unity Catalog integration
- End-to-end governed pipeline

## Configuration

### Database Location

Default: `governance/catalog.db`

To use a custom location:

```python
catalog = UnityCatalog(db_path="custom/path/catalog.db")
```

### User Context

Set the current user for audit logging:

```python
catalog = UnityCatalog(user="john.doe")
```

## Best Practices

1. **Always close connections**: Use context managers or call `.close()`
2. **Descriptive metadata**: Include descriptions and properties
3. **Log quality checks**: Track data quality over time
4. **Track pipeline runs**: Wrap executions with run tracking
5. **Regular backups**: Export catalog metadata periodically

## Integration

### With Spark

```python
from pyspark.sql import SparkSession
from governance.unity_catalog import UnityCatalog

spark = SparkSession.builder.getOrCreate()
catalog = UnityCatalog(user="spark")

df = spark.read.json("data/bronze/events.json")
catalog.register_table(
    layer="bronze",
    table_name="events",
    location="data/bronze/events.json",
    row_count=df.count()
)
```

### With Airflow

```python
from airflow.operators.python import PythonOperator
from governance.unity_catalog import UnityCatalog

def task_with_governance(**context):
    catalog = UnityCatalog(user="airflow")
    run_id = catalog.start_pipeline_run(context['dag'].dag_id)
    try:
        # Do work
        catalog.complete_pipeline_run(run_id, "success")
    except Exception as e:
        catalog.complete_pipeline_run(run_id, "failed", str(e))
        raise
```

## Documentation

For detailed documentation, see [UNITY_CATALOG.md](../docs/UNITY_CATALOG.md)

## License

This module is part of the lakehouse-template project.
