# End-to-End Test Guide

## Overview

This guide explains the end-to-end test implementation that demonstrates the lakehouse architecture using the "tracer bullet" principle from *The Pragmatic Programmer*.

## What is a Tracer Bullet?

A tracer bullet is a complete but minimal implementation that:

- Goes through all layers of the system
- Is small and quick to implement
- Provides immediate feedback
- Can be incrementally enhanced
- Validates the architecture end-to-end

## Our Tracer Bullet Implementation

The lakehouse template includes a minimal but complete implementation that demonstrates the Bronze → Silver → Gold data flow using only Python standard library and local file system storage.

### Architecture

```
Source CSV → Bronze (JSON) → Silver (JSON) → Gold (JSON)
             Raw Data         Cleaned Data     Aggregated Data
```

### Components

#### 1. Simple Pipeline (`pipelines/simple_pipeline.py`)

A lightweight lakehouse pipeline with:

- **Bronze Layer**: Ingests CSV data, adds metadata, stores as JSON
- **Silver Layer**: Cleans, validates, and deduplicates data
- **Gold Layer**: Creates business aggregations

**Key Features:**
- No external dependencies (Python stdlib only)
- Local file system storage
- Clear logging for each step
- Metadata tracking (timestamps, source info)

#### 2. Sample Data (`data/sample_customers.csv`)

A small customer dataset with:
- Valid records
- Duplicate records (tests deduplication)
- Invalid records (tests data quality)

#### 3. End-to-End Test (`tests/test_end_to_end.py`)

Automated test that:
- Runs the full pipeline
- Validates data in each layer
- Checks data flow integrity
- Cleans up test artifacts

## Running the Test

### Prerequisites

- Python 3.6 or higher
- No additional packages required

### Quick Start

```bash
# Clone the repository and navigate to it
cd lakehouse-template

# Run the end-to-end test
python3 tests/test_end_to_end.py
```

### Run the Pipeline Standalone

```bash
# Run the simple pipeline directly
python3 pipelines/simple_pipeline.py
```

This will:
1. Ingest `data/sample_customers.csv` to bronze layer
2. Clean and transform to silver layer
3. Aggregate by region to gold layer
4. Display results

### Inspect the Results

After running the pipeline:

```bash
# View bronze data (raw ingestion)
cat data/bronze/customers.json

# View silver data (cleaned)
cat data/silver/customers.json

# View gold data (aggregated by region)
cat data/gold/customers_by_region.json
```

## What the Test Validates

### 1. Bronze Layer Validation

- File exists and contains data
- All records have ingestion timestamp
- Source file metadata is present
- Raw data is preserved

### 2. Silver Layer Validation

- Data cleaning removed invalid records
- Duplicate records are removed
- All records have required fields
- Data quality score is calculated

### 3. Gold Layer Validation

- Aggregations are created correctly
- Aggregate counts match detail records
- All silver records are included
- Aggregation metadata is present

### 4. Data Flow Integrity

- Bronze contains all source records
- Silver has fewer or equal records (due to cleaning)
- Gold aggregates cover all silver records
- No data is lost or duplicated incorrectly

## Expected Output

Successful test run:

```
======================================================================
Running End-to-End Lakehouse Pipeline Test
======================================================================

[BRONZE] Ingesting data from data/sample_customers.csv
[BRONZE] Ingested 14 records to data/bronze/test_customers.json
[SILVER] Transforming test_customers
[SILVER] Processed 12 clean records (quality: 85.7%) to data/silver/test_customers.json
[GOLD] Aggregating test_customers by region
[GOLD] Created 4 aggregates in data/gold/test_customers_by_region.json

----------------------------------------------------------------------
Validating Results
----------------------------------------------------------------------

Test 1: Validating Bronze Layer...
✓ Bronze layer has 14 records with metadata

Test 2: Validating Silver Layer...
✓ Silver layer has 12 clean, deduplicated records

Test 3: Validating Gold Layer...
✓ Gold layer has 4 aggregates
  Aggregations by region:
    - North: 4 customers
    - South: 3 customers
    - East: 3 customers
    - West: 2 customers

Test 4: Validating Data Flow Integrity...
✓ Data flow integrity verified across all layers

======================================================================
ALL TESTS PASSED! ✓
======================================================================
```

## Extending the Implementation

This tracer bullet can be extended to:

### 1. Add More Data Sources

```python
pipeline.ingest_to_bronze(
    source_file="data/transactions.csv",
    dataset_name="transactions"
)
```

### 2. Customize Transformations

Modify `transform_to_silver()` to add:
- Data type conversions
- Business rules validation
- PII masking
- Data enrichment

### 3. Create Different Aggregations

Modify `aggregate_to_gold()` to:
- Group by different fields
- Calculate metrics (sum, average, etc.)
- Create time-based aggregations
- Join multiple datasets

### 4. Add Error Handling

```python
try:
    pipeline.run_full_pipeline(...)
except DataQualityError as e:
    logger.error(f"Data quality check failed: {e}")
    # Send alert, retry, etc.
```

### 5. Integrate with CI/CD

```yaml
# .github/workflows/test.yml
- name: Run end-to-end test
  run: python3 tests/test_end_to_end.py
```

## Next Steps

Once the tracer bullet is working, you can:

1. **Scale Up**: Replace simple implementations with production tools
   - Use Apache Spark for large-scale processing
   - Use Delta Lake for ACID transactions
   - Use Airflow for orchestration

2. **Add Features**: Enhance the pipeline with
   - Data quality framework
   - Monitoring and alerting
   - Data lineage tracking
   - Schema evolution

3. **Deploy**: Move to production environment
   - Cloud storage (S3, ADLS, GCS)
   - Distributed compute (EMR, Databricks, Dataproc)
   - Orchestration (Airflow, Prefect, Dagster)

## Benefits of This Approach

1. **Quick Validation**: Verify the architecture works before investing in complex infrastructure
2. **Easy Debugging**: Simple code is easier to understand and troubleshoot
3. **Low Cost**: Runs locally with no cloud resources
4. **Great for Learning**: Clear demonstration of lakehouse concepts
5. **Foundation**: Provides a template for more complex implementations

## Troubleshooting

### Test Fails

- Check Python version: `python3 --version` (needs 3.6+)
- Verify sample data exists: `ls data/sample_customers.csv`
- Check permissions: `ls -la data/`

### Pipeline Doesn't Run

- Ensure you're in the repository root
- Check file paths are correct
- Verify data directories exist

### Data Not Generated

- Check for error messages in output
- Verify write permissions in `data/` directories
- Ensure no other process is locking the files

## Related Documentation

- [Architecture Overview](ARCHITECTURE.md)
- [Getting Started Guide](GETTING_STARTED.md)
- [Test README](../tests/README.md)

## References

- *The Pragmatic Programmer* by Andrew Hunt and David Thomas
- Databricks Medallion Architecture
- Data Engineering Best Practices
