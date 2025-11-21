# Quick Start: End-to-End Test

The fastest way to see the lakehouse architecture in action!

## Run the Test

```bash
# Option 1: Use the convenience script (recommended)
bash scripts/run-e2e-test.sh

# Option 2: Run the test directly
python3 tests/test_end_to_end.py

# Option 3: Run the pipeline standalone (keeps data files)
python3 pipelines/simple_pipeline.py
```

## What Happens?

1. **Bronze Layer**: Ingests 14 customer records from CSV → JSON
2. **Silver Layer**: Cleans data (removes duplicates and invalid records) → 12 records
3. **Gold Layer**: Aggregates by region → 4 regional summaries

## Expected Output

```
======================================================================
ALL TESTS PASSED! ✓
======================================================================

Bronze: 14 records ingested
Silver: 12 clean records (85.7% quality)
Gold: 4 aggregates by region
  - North: 4 customers
  - South: 3 customers
  - East: 3 customers
  - West: 2 customers
```

## Requirements

- Python 3.6+
- No external dependencies!

## Explore the Data

After running the pipeline (option 3), view the generated files:

```bash
# View bronze data (raw with metadata)
cat data/bronze/customers.json

# View silver data (cleaned and validated)
cat data/silver/customers.json

# View gold data (aggregated by region)
cat data/gold/customers_by_region.json
```

## Learn More

- Full documentation: [docs/END_TO_END_TEST.md](../docs/END_TO_END_TEST.md)
- Test implementation: [test_end_to_end.py](test_end_to_end.py)
- Pipeline code: [../pipelines/simple_pipeline.py](../pipelines/simple_pipeline.py)
- Sample data: [../data/sample_customers.csv](../data/sample_customers.csv)

## Why This Matters

This test demonstrates the **tracer bullet** principle:

- ✅ Minimal: No complex dependencies
- ✅ Complete: All layers working together
- ✅ Fast: Runs in seconds
- ✅ Local: No cloud resources needed
- ✅ Validating: Proves the architecture works

Use this as a foundation to build more complex pipelines!
