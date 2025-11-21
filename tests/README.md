# Lakehouse Template Tests

This directory contains tests for the lakehouse template.

## End-to-End Test (Tracer Bullet)

The `test_end_to_end.py` script implements a "tracer bullet" test following the principle from *The Pragmatic Programmer*. It validates a minimal but complete slice through the entire lakehouse architecture.

### What it Tests

The end-to-end test validates:

1. **Bronze Layer**: Raw data ingestion with metadata
2. **Silver Layer**: Data cleaning, validation, and deduplication
3. **Gold Layer**: Business aggregations
4. **Data Flow Integrity**: Ensures data flows correctly through all layers

### Running the Test

```bash
# From the repository root
python3 tests/test_end_to_end.py
```

### Test Requirements

- Python 3.6+
- No external dependencies (uses only Python standard library)
- Sample data file: `data/sample_customers.csv`

### What Makes This a "Tracer Bullet"

This test demonstrates the tracer bullet principle by:

- **Minimal**: Uses only Python standard library, no complex dependencies
- **Complete**: Touches every layer (Bronze → Silver → Gold)
- **Local**: Runs entirely on local file system
- **Fast**: Executes in seconds
- **Validating**: Includes assertions for each layer

### Expected Output

When successful, you'll see:

```
======================================================================
Running End-to-End Lakehouse Pipeline Test
======================================================================

[Pipeline execution output]

----------------------------------------------------------------------
Validating Results
----------------------------------------------------------------------

Test 1: Validating Bronze Layer...
✓ Bronze layer has X records with metadata

Test 2: Validating Silver Layer...
✓ Silver layer has Y clean, deduplicated records

Test 3: Validating Gold Layer...
✓ Gold layer has Z aggregates

Test 4: Validating Data Flow Integrity...
✓ Data flow integrity verified across all layers

======================================================================
ALL TESTS PASSED! ✓
======================================================================
```

### Extending the Test

This basic test can be extended to:

- Add more complex transformations
- Test error handling and recovery
- Add data quality checks
- Test with different data sources
- Integrate with CI/CD pipelines

## Simple Pipeline

The test uses `pipelines/simple_pipeline.py`, which can also be run standalone:

```bash
python3 pipelines/simple_pipeline.py
```

This pipeline demonstrates the medallion architecture pattern with minimal dependencies, making it easy to understand and extend.
