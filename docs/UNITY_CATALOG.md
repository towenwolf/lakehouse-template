# Unity Catalog - Local Governance for Lakehouse

## Overview

Unity Catalog is a unified governance solution for the lakehouse template that provides end-to-end data governance capabilities at a local level. It captures metadata, tracks lineage, logs access, and monitors data quality across all layers of the medallion architecture.

## Key Features

### 🗂️ Metadata Management
- **Catalog Structure**: Hierarchical organization (Catalog → Schema → Table → Columns)
- **Table Registry**: Complete metadata for all tables including schema, location, format, and statistics
- **Column-level Metadata**: Data types, nullability, descriptions
- **Properties**: Extensible key-value properties for custom metadata

### 🔗 Data Lineage Tracking
- **Upstream Lineage**: Track source tables and transformations
- **Downstream Lineage**: Track consumer tables and dependencies
- **Pipeline Tracking**: Monitor pipeline runs with start/end times and status
- **Data Flow Metrics**: Record records read/written, bytes processed, duration

### 📝 Audit Logging
- **Access Logging**: Track all data access operations (read, write, scan)
- **Action Logging**: Log catalog operations (create, update, delete)
- **Quality Logging**: Record data quality check results
- **Compliance**: Full audit trail for regulatory compliance

### ✅ Data Quality Monitoring
- **Quality Checks**: Track completeness, uniqueness, validity checks
- **Error Rates**: Monitor data quality metrics over time
- **Pass/Fail Status**: Record quality check outcomes
- **Historical Trends**: View quality trends across pipeline runs

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      Unity Catalog                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   Metadata   │  │   Lineage    │  │    Audit     │         │
│  │    Store     │  │   Tracker    │  │   Logger     │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│         │                 │                  │                  │
│         └─────────────────┴──────────────────┘                  │
│                           │                                     │
│                    SQLite Database                              │
│                  (governance/catalog.db)                        │
└─────────────────────────────────────────────────────────────────┘
```

## Quick Start

### 1. Using the Governed Pipeline

The governed pipeline automatically integrates Unity Catalog into your data processing:

```python
from pipelines.governed_pipeline import GovernedLakehousePipeline

# Initialize pipeline with governance
with GovernedLakehousePipeline(user="admin") as pipeline:
    # Run pipeline - governance happens automatically
    result = pipeline.run_full_pipeline(
        source_file="data/sample_customers.csv",
        dataset_name="customers",
        group_by_field="region"
    )
    
    # Show detailed table information
    pipeline.show_table_info("silver", "customers")
```

**What happens automatically:**
- ✅ Tables registered in catalog with full metadata
- ✅ Data lineage tracked across Bronze → Silver → Gold
- ✅ Data access logged for compliance
- ✅ Quality checks recorded with pass/fail status
- ✅ Pipeline run tracked with timing and metrics

### 2. Using the CLI

Query and explore the catalog using the command-line interface:

```bash
# Show governance summary
python3 governance/catalog_cli.py summary

# List all tables in a layer
python3 governance/catalog_cli.py list bronze

# Describe a specific table
python3 governance/catalog_cli.py describe silver customers

# Show lineage for a table
python3 governance/catalog_cli.py lineage gold customers_by_region

# View access history
python3 governance/catalog_cli.py access silver customers --limit 20

# View quality check history
python3 governance/catalog_cli.py quality silver customers

# Export catalog metadata
python3 governance/catalog_cli.py export catalog_export.json
```

### 3. Direct API Usage

Use the Unity Catalog API directly in your code:

```python
from governance.unity_catalog import UnityCatalog

# Initialize catalog
with UnityCatalog(user="admin") as catalog:
    # Register a table
    catalog.register_table(
        layer="bronze",
        table_name="events",
        location="data/bronze/events.json",
        columns=[
            {'name': 'event_id', 'type': 'string', 'nullable': False},
            {'name': 'timestamp', 'type': 'timestamp', 'nullable': False},
            {'name': 'user_id', 'type': 'string', 'nullable': True}
        ],
        description="Raw event data",
        row_count=10000,
        size_bytes=2048000
    )
    
    # Register a transformation
    catalog.register_transformation(
        source_layer="bronze",
        source_table="events",
        target_layer="silver",
        target_table="events_clean",
        transformation_type="deduplication",
        pipeline_name="event_processing"
    )
    
    # Get table information
    info = catalog.get_table_info("bronze", "events")
    print(f"Table has {info['row_count']} rows")
    
    # Get lineage
    lineage = catalog.get_table_lineage("silver", "events_clean")
    print(f"Upstream sources: {len(lineage['upstream'])}")
    print(f"Downstream consumers: {len(lineage['downstream'])}")
```

## Components

### MetadataStore

Manages catalog metadata using SQLite database:

- **Catalogs**: Top-level namespaces
- **Schemas**: Databases within catalogs (bronze, silver, gold)
- **Tables**: Datasets with location, format, statistics
- **Columns**: Column definitions with types and constraints

### LineageTracker

Tracks data lineage and pipeline execution:

- **Lineage Relationships**: Source → Target transformations
- **Pipeline Runs**: Execution tracking with status
- **Data Flows**: Record-level metrics for each transformation
- **Lineage Graphs**: Full upstream/downstream dependencies

### AuditLogger

Provides comprehensive audit logging:

- **Action Log**: All catalog operations
- **Access Log**: Table-level data access
- **Quality Log**: Data quality check results
- **Compliance Reports**: Audit trails for regulations

### UnityCatalog

Main interface that coordinates all components:

- **Unified API**: Single interface for all governance operations
- **Automatic Initialization**: Sets up lakehouse catalog structure
- **Integrated Operations**: Coordinates metadata, lineage, and audit
- **Export/Import**: Backup and restore catalog metadata

## Data Catalog Schema

### Catalog Hierarchy

```
lakehouse (catalog)
├── bronze (schema)
│   ├── customers (table)
│   ├── orders (table)
│   └── products (table)
├── silver (schema)
│   ├── customers (table)
│   ├── orders (table)
│   └── products (table)
└── gold (schema)
    ├── customers_by_region (table)
    ├── monthly_sales (table)
    └── product_metrics (table)
```

### Table Metadata

Each table includes:
- **Basic Info**: Name, type, description, owner
- **Location**: File system path
- **Format**: File format (json, parquet, delta, etc.)
- **Statistics**: Row count, size in bytes
- **Timestamps**: Created, updated dates
- **Schema**: Column definitions
- **Properties**: Custom key-value metadata

## Lineage Tracking

### Lineage Levels

1. **Table-level Lineage**: Track relationships between tables
2. **Pipeline-level Lineage**: Track which pipelines create which tables
3. **Run-level Lineage**: Track actual data movement in specific runs

### Example Lineage

```
Source File
    ↓ (ingestion)
bronze.customers
    ↓ (cleaning_and_deduplication)
silver.customers
    ↓ (aggregation)
gold.customers_by_region
```

### Querying Lineage

```python
# Get full lineage graph
lineage = catalog.get_table_lineage("silver", "customers")

# Upstream sources (where the data comes from)
for source in lineage['upstream']:
    print(f"{source['source_table']} → {source['transformation_type']}")

# Downstream consumers (what uses this data)
for consumer in lineage['downstream']:
    print(f"{consumer['transformation_type']} → {consumer['target_table']}")
```

## Audit Trail

### What is Logged

1. **Catalog Operations**
   - Table creation/deletion
   - Schema changes
   - Metadata updates

2. **Data Access**
   - Read operations (which tables, how many rows)
   - Write operations (records written, bytes)
   - Duration and status

3. **Data Quality**
   - Quality check name and type
   - Pass/fail counts
   - Error rates
   - Check timestamps

### Audit Queries

```python
# Get audit trail for a table
audit = catalog.audit.get_audit_trail(
    resource_name="lakehouse.silver.customers",
    start_date="2025-01-01",
    limit=100
)

# Get access history
access = catalog.audit.get_data_access_history(
    table_name="lakehouse.silver.customers",
    user="admin",
    limit=50
)

# Get access summary
summary = catalog.audit.get_access_summary(
    table_name="lakehouse.silver.customers",
    days=30
)
print(f"Total accesses: {summary['total_accesses']}")
print(f"Unique users: {summary['unique_users']}")
```

## Best Practices

### 1. Always Use Governed Pipeline

Use `GovernedLakehousePipeline` instead of `SimpleLakehousePipeline` to automatically capture governance metadata:

```python
# ✅ Good - Automatic governance
from pipelines.governed_pipeline import GovernedLakehousePipeline
pipeline = GovernedLakehousePipeline(user="admin")

# ❌ Avoid - No governance tracking
from pipelines.simple_pipeline import SimpleLakehousePipeline
pipeline = SimpleLakehousePipeline()
```

### 2. Provide Descriptive Metadata

Include descriptions and properties when registering tables:

```python
catalog.register_table(
    layer="silver",
    table_name="customers",
    description="Cleaned customer data with deduplication",
    properties={
        "data_owner": "sales_team",
        "retention_days": 365,
        "pii_fields": ["email", "phone"],
        "quality_sla": 0.95
    }
)
```

### 3. Log Quality Checks

Always log data quality checks:

```python
catalog.log_quality_check(
    layer="silver",
    table_name="customers",
    check_name="email_format",
    check_type="validity",
    status="passed",
    passed_count=950,
    failed_count=50,
    details={"pattern": "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"}
)
```

### 4. Track Pipeline Runs

Wrap pipeline execution with run tracking:

```python
# Start tracking
run_id = catalog.start_pipeline_run("my_pipeline", "full")

try:
    # Execute pipeline
    process_data()
    
    # Record successful completion
    catalog.complete_pipeline_run(run_id, "success")
except Exception as e:
    # Record failure
    catalog.complete_pipeline_run(run_id, "failed", str(e))
    raise
```

### 5. Regular Catalog Backups

Export catalog metadata regularly:

```bash
# Export catalog
python3 governance/catalog_cli.py export backups/catalog_$(date +%Y%m%d).json

# Or programmatically
catalog.export_catalog(f"backups/catalog_{date}.json")
```

## Integration Examples

### With Apache Spark

```python
from pyspark.sql import SparkSession
from governance.unity_catalog import UnityCatalog

spark = SparkSession.builder.appName("governed_spark").getOrCreate()
catalog = UnityCatalog(user="spark_job")

# Read data
df = spark.read.json("data/bronze/events.json")

# Register in catalog
catalog.register_table(
    layer="bronze",
    table_name="events",
    location="data/bronze/events.json",
    format="json",
    row_count=df.count(),
    columns=[
        {'name': field.name, 'type': str(field.dataType), 'nullable': field.nullable}
        for field in df.schema.fields
    ]
)
```

### With dbt

```python
# In your dbt post-hook
from governance.unity_catalog import UnityCatalog

catalog = UnityCatalog(user="dbt")

# After dbt model runs
catalog.register_table(
    layer="silver",
    table_name="{{ this.name }}",
    location="{{ this.location }}",
    description="{{ model.description }}",
    row_count="{{ adapter.get_row_count(this) }}"
)
```

### With Airflow

```python
from airflow import DAG
from airflow.operators.python import PythonOperator
from governance.unity_catalog import UnityCatalog

def process_with_governance(**context):
    catalog = UnityCatalog(user=context['dag_run'].conf.get('user', 'airflow'))
    run_id = catalog.start_pipeline_run(context['dag'].dag_id)
    
    try:
        # Process data
        result = process_data()
        
        # Record flow
        catalog.record_data_flow(
            run_id,
            source_layer="bronze",
            source_table="raw_data",
            target_layer="silver",
            target_table="clean_data",
            records_read=result['input_rows'],
            records_written=result['output_rows']
        )
        
        catalog.complete_pipeline_run(run_id, "success")
    except Exception as e:
        catalog.complete_pipeline_run(run_id, "failed", str(e))
        raise

dag = DAG('governed_pipeline', ...)
task = PythonOperator(
    task_id='process',
    python_callable=process_with_governance,
    dag=dag
)
```

## Storage and Performance

### Database Location

Default: `governance/catalog.db` (SQLite)

To use a different location:

```python
catalog = UnityCatalog(db_path="custom/path/catalog.db")
```

### Performance Considerations

1. **SQLite is suitable for**:
   - Local development
   - Small to medium datasets (<10M tables)
   - Single-user access

2. **For production at scale, consider**:
   - PostgreSQL or MySQL for multi-user access
   - Separate metadata service
   - Distributed catalog (Apache Hive Metastore, AWS Glue)

### Cleanup and Maintenance

```bash
# Compact database
sqlite3 governance/catalog.db "VACUUM;"

# Check database size
du -h governance/catalog.db

# Archive old audit logs
python3 -c "
from governance.audit_logger import AuditLogger
logger = AuditLogger()
# Archive logs older than 90 days
"
```

## Troubleshooting

### Database Locked Error

If you see "database is locked":

```python
# Close all connections properly
catalog.close()

# Or use context manager
with UnityCatalog() as catalog:
    # Operations here
    pass
# Automatically closed
```

### Missing Tables

If tables don't appear in catalog:

```bash
# Check if pipeline used governed version
python3 governance/catalog_cli.py list bronze

# Re-register manually if needed
python3 -c "
from governance.unity_catalog import UnityCatalog
catalog = UnityCatalog()
catalog.register_table(...)
"
```

### Lineage Not Showing

Ensure transformations are registered:

```python
# After each transformation
catalog.register_transformation(
    source_layer="bronze",
    source_table="source",
    target_layer="silver",
    target_table="target",
    transformation_type="cleaning"
)
```

## Future Enhancements

Planned improvements:

- [ ] Data discovery UI
- [ ] Automated data profiling
- [ ] Schema evolution tracking
- [ ] Data retention policies
- [ ] Role-based access control (RBAC)
- [ ] Integration with external catalogs (Hive, Glue, Purview)
- [ ] Automated data lineage from SQL queries
- [ ] Real-time monitoring dashboard
- [ ] Data classification (PII detection)
- [ ] Compliance reporting templates

## Additional Resources

- [Architecture Documentation](ARCHITECTURE.md)
- [Getting Started Guide](GETTING_STARTED.md)
- [API Reference](../governance/README.md)
- [Example Pipelines](../pipelines/examples/)

## Support

For issues or questions:
1. Check this documentation
2. Review example code in `pipelines/governed_pipeline.py`
3. Run tests: `python3 tests/test_unity_catalog.py`
4. Open an issue on GitHub
