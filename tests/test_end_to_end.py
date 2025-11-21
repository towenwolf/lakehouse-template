"""
End-to-End Test for Simple Lakehouse Pipeline
Tests the complete Bronze -> Silver -> Gold data flow
"""

import json
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from pipelines.simple_pipeline import SimpleLakehousePipeline


def cleanup_test_data(pipeline):
    """Remove test data files"""
    test_files = [
        pipeline.bronze_path / "test_customers.json",
        pipeline.silver_path / "test_customers.json",
        pipeline.gold_path / "test_customers_by_region.json"
    ]
    
    for file in test_files:
        if file.exists():
            file.unlink()


def test_end_to_end_pipeline():
    """Test the complete pipeline flow"""
    print("\n" + "=" * 70)
    print("Running End-to-End Lakehouse Pipeline Test")
    print("=" * 70 + "\n")
    
    # Setup
    test_passed = True
    pipeline = SimpleLakehousePipeline(base_path="data")
    
    # Cleanup any existing test data
    cleanup_test_data(pipeline)
    
    try:
        # Run the pipeline
        result = pipeline.run_full_pipeline(
            source_file="data/sample_customers.csv",
            dataset_name="test_customers",
            group_by_field="region"
        )
        
        print("\n" + "-" * 70)
        print("Validating Results")
        print("-" * 70 + "\n")
        
        # Test 1: Bronze layer exists and has data
        print("Test 1: Validating Bronze Layer...")
        bronze_file = Path(result['bronze'])
        assert bronze_file.exists(), "Bronze file does not exist"
        
        with open(bronze_file, 'r') as f:
            bronze_data = json.load(f)
        
        assert len(bronze_data) > 0, "Bronze data is empty"
        assert all('_ingestion_timestamp' in record for record in bronze_data), \
            "Bronze records missing ingestion timestamp"
        print(f"✓ Bronze layer has {len(bronze_data)} records with metadata")
        
        # Test 2: Silver layer has cleaned data
        print("\nTest 2: Validating Silver Layer...")
        silver_file = Path(result['silver'])
        assert silver_file.exists(), "Silver file does not exist"
        
        with open(silver_file, 'r') as f:
            silver_data = json.load(f)
        
        assert len(silver_data) > 0, "Silver data is empty"
        assert len(silver_data) < len(bronze_data), \
            "Silver should have fewer records (cleaned/deduplicated)"
        
        # Check for duplicates
        ids = [record['id'] for record in silver_data]
        assert len(ids) == len(set(ids)), "Silver data contains duplicates"
        
        # Check all records have required fields
        assert all(record.get('id') and record.get('id').strip() 
                   for record in silver_data), \
            "Silver records have invalid ids"
        
        print(f"✓ Silver layer has {len(silver_data)} clean, deduplicated records")
        
        # Test 3: Gold layer has aggregations
        print("\nTest 3: Validating Gold Layer...")
        gold_file = Path(result['gold'])
        assert gold_file.exists(), "Gold file does not exist"
        
        with open(gold_file, 'r') as f:
            gold_data = json.load(f)
        
        assert len(gold_data) > 0, "Gold data is empty"
        
        # Verify aggregation structure
        for agg in gold_data:
            assert 'region' in agg, "Aggregate missing region field"
            assert 'count' in agg, "Aggregate missing count field"
            assert 'records' in agg, "Aggregate missing records list"
            assert agg['count'] == len(agg['records']), \
                "Aggregate count doesn't match records list"
        
        # Verify total count matches silver
        total_count = sum(agg['count'] for agg in gold_data)
        assert total_count == len(silver_data), \
            "Gold aggregate count doesn't match silver record count"
        
        print(f"✓ Gold layer has {len(gold_data)} aggregates")
        print(f"  Aggregations by region:")
        for agg in gold_data:
            print(f"    - {agg['region']}: {agg['count']} customers")
        
        # Test 4: Data flow integrity
        print("\nTest 4: Validating Data Flow Integrity...")
        
        # Verify data reduction (bronze > silver due to cleaning)
        assert len(bronze_data) >= len(silver_data), \
            "Silver should have <= records than bronze"
        
        # Verify aggregation covers all silver records
        silver_ids = set(record['id'] for record in silver_data)
        gold_ids = set()
        for agg in gold_data:
            gold_ids.update(agg['records'])
        
        assert silver_ids == gold_ids, \
            "Gold aggregates don't cover all silver records"
        
        print("✓ Data flow integrity verified across all layers")
        
        print("\n" + "=" * 70)
        print("ALL TESTS PASSED! ✓")
        print("=" * 70 + "\n")
        
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {str(e)}\n")
        test_passed = False
    except Exception as e:
        print(f"\n✗ UNEXPECTED ERROR: {str(e)}\n")
        test_passed = False
    finally:
        # Cleanup test data
        print("Cleaning up test data...")
        cleanup_test_data(pipeline)
        print("Cleanup complete.\n")
    
    return test_passed


if __name__ == "__main__":
    success = test_end_to_end_pipeline()
    sys.exit(0 if success else 1)
