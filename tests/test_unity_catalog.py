"""
Test Unity Catalog Governance Features
Tests metadata management, lineage tracking, and audit logging
"""

import json
import os
import sys
import tempfile
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from governance.unity_catalog import UnityCatalog
from governance.metadata_store import MetadataStore
from governance.lineage_tracker import LineageTracker
from governance.audit_logger import AuditLogger
from pipelines.governed_pipeline import GovernedLakehousePipeline


def test_metadata_store():
    """Test metadata store functionality"""
    print("\n" + "=" * 70)
    print("Test 1: Metadata Store")
    print("=" * 70)
    
    # Create temporary database
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        temp_db = f.name
    
    try:
        with MetadataStore(temp_db) as store:
            # Create catalog
            catalog_id = store.create_catalog("test_catalog", "Test catalog")
            assert catalog_id > 0, "Catalog creation failed"
            print("✓ Created catalog")
            
            # Create schema
            schema_id = store.create_schema("test_catalog", "test_schema", "/data/test")
            assert schema_id > 0, "Schema creation failed"
            print("✓ Created schema")
            
            # Register table
            table_id = store.register_table(
                "test_catalog", "test_schema", "test_table",
                "managed", "/data/test/table", "json",
                row_count=100, size_bytes=1024
            )
            assert table_id > 0, "Table registration failed"
            print("✓ Registered table")
            
            # Register columns
            columns = [
                {'name': 'id', 'type': 'integer', 'nullable': False},
                {'name': 'name', 'type': 'string', 'nullable': True}
            ]
            store.register_columns("test_catalog", "test_schema", "test_table", columns)
            print("✓ Registered columns")
            
            # Get table metadata
            metadata = store.get_table_metadata("test_catalog", "test_schema", "test_table")
            assert metadata is not None, "Failed to retrieve metadata"
            assert metadata['table_name'] == "test_table"
            assert len(metadata['columns']) == 2
            print("✓ Retrieved table metadata")
            
            # List tables
            tables = store.list_tables("test_catalog", "test_schema")
            assert len(tables) == 1
            print("✓ Listed tables")
            
            print("\n✓ All metadata store tests passed!")
            return True
            
    finally:
        if os.path.exists(temp_db):
            os.unlink(temp_db)


def test_lineage_tracker():
    """Test lineage tracking functionality"""
    print("\n" + "=" * 70)
    print("Test 2: Lineage Tracker")
    print("=" * 70)
    
    # Create temporary database
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        temp_db = f.name
    
    try:
        with LineageTracker(temp_db) as tracker:
            # Register lineage
            tracker.register_lineage(
                "catalog.bronze.source",
                "catalog.silver.target",
                "transformation",
                "test_pipeline"
            )
            print("✓ Registered lineage relationship")
            
            # Start pipeline run
            run_id = tracker.start_pipeline_run("test_pipeline", "full")
            assert run_id > 0
            print(f"✓ Started pipeline run {run_id}")
            
            # Record data flow
            tracker.record_data_flow(
                run_id, "catalog.bronze.source", "catalog.silver.target",
                records_read=100, records_written=90,
                duration_seconds=1.5
            )
            print("✓ Recorded data flow")
            
            # Complete pipeline run
            tracker.complete_pipeline_run(run_id, "success")
            print("✓ Completed pipeline run")
            
            # Get upstream lineage
            upstream = tracker.get_upstream_lineage("catalog.silver.target")
            assert len(upstream) > 0
            print(f"✓ Retrieved upstream lineage ({len(upstream)} sources)")
            
            # Get downstream lineage
            downstream = tracker.get_downstream_lineage("catalog.bronze.source")
            assert len(downstream) > 0
            print(f"✓ Retrieved downstream lineage ({len(downstream)} consumers)")
            
            # Get pipeline history
            history = tracker.get_pipeline_history("test_pipeline")
            assert len(history) > 0
            print(f"✓ Retrieved pipeline history ({len(history)} runs)")
            
            print("\n✓ All lineage tracker tests passed!")
            return True
            
    finally:
        if os.path.exists(temp_db):
            os.unlink(temp_db)


def test_audit_logger():
    """Test audit logging functionality"""
    print("\n" + "=" * 70)
    print("Test 3: Audit Logger")
    print("=" * 70)
    
    # Create temporary database
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        temp_db = f.name
    
    try:
        with AuditLogger(temp_db) as logger:
            # Log action
            logger.log_action(
                "test_user", "create_table", "table",
                "catalog.schema.table", "success"
            )
            print("✓ Logged action")
            
            # Log data access
            logger.log_data_access(
                "test_user", "catalog.schema.table", "select",
                rows_affected=100, status="success"
            )
            print("✓ Logged data access")
            
            # Log quality check
            logger.log_quality_check(
                "catalog.schema.table", "completeness_check", "completeness",
                "passed", passed_count=95, failed_count=5
            )
            print("✓ Logged quality check")
            
            # Get audit trail
            audit = logger.get_audit_trail(limit=10)
            assert len(audit) > 0
            print(f"✓ Retrieved audit trail ({len(audit)} entries)")
            
            # Get data access history
            access = logger.get_data_access_history(limit=10)
            assert len(access) > 0
            print(f"✓ Retrieved access history ({len(access)} entries)")
            
            # Get quality history
            quality = logger.get_quality_history(limit=10)
            assert len(quality) > 0
            print(f"✓ Retrieved quality history ({len(quality)} checks)")
            
            print("\n✓ All audit logger tests passed!")
            return True
            
    finally:
        if os.path.exists(temp_db):
            os.unlink(temp_db)


def test_unity_catalog_integration():
    """Test Unity Catalog end-to-end integration"""
    print("\n" + "=" * 70)
    print("Test 4: Unity Catalog Integration")
    print("=" * 70)
    
    # Create temporary database
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        temp_db = f.name
    
    try:
        with UnityCatalog(temp_db, user="test_user") as catalog:
            # Register a table
            table_id = catalog.register_table(
                layer="bronze",
                table_name="test_table",
                location="/data/bronze/test_table.json",
                columns=[
                    {'name': 'id', 'type': 'integer', 'nullable': False},
                    {'name': 'value', 'type': 'string', 'nullable': True}
                ],
                row_count=100,
                size_bytes=2048
            )
            assert table_id > 0
            print("✓ Registered table in catalog")
            
            # Register transformation
            catalog.register_transformation(
                "bronze", "test_table",
                "silver", "test_table_clean",
                "cleaning", "test_pipeline"
            )
            print("✓ Registered transformation")
            
            # Start pipeline run
            run_id = catalog.start_pipeline_run("test_pipeline")
            assert run_id > 0
            print(f"✓ Started pipeline run {run_id}")
            
            # Record data flow
            catalog.record_data_flow(
                run_id, "bronze", "test_table",
                "silver", "test_table_clean",
                records_read=100, records_written=95
            )
            print("✓ Recorded data flow")
            
            # Log quality check
            catalog.log_quality_check(
                "silver", "test_table_clean",
                "deduplication", "uniqueness",
                "passed", passed_count=95, failed_count=5
            )
            print("✓ Logged quality check")
            
            # Complete pipeline run
            catalog.complete_pipeline_run(run_id, "success")
            print("✓ Completed pipeline run")
            
            # Get table info
            info = catalog.get_table_info("bronze", "test_table")
            assert info is not None
            assert info['table_name'] == "test_table"
            print("✓ Retrieved table info")
            
            # Get governance summary
            summary = catalog.get_governance_summary()
            assert summary['total_tables'] > 0
            print(f"✓ Retrieved governance summary ({summary['total_tables']} tables)")
            
            print("\n✓ All Unity Catalog integration tests passed!")
            return True
            
    finally:
        if os.path.exists(temp_db):
            os.unlink(temp_db)


def test_governed_pipeline():
    """Test governed pipeline with real data"""
    print("\n" + "=" * 70)
    print("Test 5: Governed Pipeline End-to-End")
    print("=" * 70)
    
    # Clean up any existing governance database
    gov_db = Path("governance/catalog.db")
    if gov_db.exists():
        gov_db.unlink()
    
    try:
        with GovernedLakehousePipeline(user="test_user") as pipeline:
            # Run pipeline
            result = pipeline.run_full_pipeline(
                source_file="data/sample_customers.csv",
                dataset_name="test_customers",
                group_by_field="region"
            )
            
            assert result['bronze'], "Bronze file not created"
            assert result['silver'], "Silver file not created"
            assert result['gold'], "Gold file not created"
            assert result['run_id'], "Run ID not returned"
            print("✓ Pipeline completed successfully")
            
            # Verify files exist
            assert Path(result['bronze']).exists()
            assert Path(result['silver']).exists()
            assert Path(result['gold']).exists()
            print("✓ All output files exist")
            
            # Verify catalog has metadata
            bronze_info = pipeline.catalog.get_table_info("bronze", "test_customers")
            assert bronze_info is not None
            assert bronze_info['row_count'] > 0
            print(f"✓ Bronze table has {bronze_info['row_count']} rows")
            
            silver_info = pipeline.catalog.get_table_info("silver", "test_customers")
            assert silver_info is not None
            assert silver_info['row_count'] > 0
            print(f"✓ Silver table has {silver_info['row_count']} rows")
            
            gold_info = pipeline.catalog.get_table_info("gold", "test_customers_by_region")
            assert gold_info is not None
            assert gold_info['row_count'] > 0
            print(f"✓ Gold table has {gold_info['row_count']} aggregates")
            
            # Verify lineage
            lineage = pipeline.catalog.get_table_lineage("silver", "test_customers")
            assert len(lineage['upstream']) > 0
            assert len(lineage['downstream']) > 0
            print(f"✓ Lineage tracked: {len(lineage['upstream'])} upstream, "
                  f"{len(lineage['downstream'])} downstream")
            
            # Verify quality checks
            quality = pipeline.catalog.get_table_quality_history("silver", "test_customers")
            assert len(quality) >= 2  # Should have at least 2 checks
            print(f"✓ Quality checks recorded: {len(quality)} checks")
            
            # Verify audit log
            access = pipeline.catalog.get_table_access_history("bronze", "test_customers")
            assert len(access) > 0
            print(f"✓ Audit log recorded: {len(access)} accesses")
            
            print("\n✓ All governed pipeline tests passed!")
            return True
            
    finally:
        # Cleanup test data
        test_files = [
            "data/bronze/test_customers.json",
            "data/silver/test_customers.json",
            "data/gold/test_customers_by_region.json"
        ]
        for file in test_files:
            path = Path(file)
            if path.exists():
                path.unlink()


def main():
    """Run all tests"""
    print("\n" + "=" * 70)
    print("Unity Catalog Test Suite")
    print("=" * 70)
    
    tests = [
        ("Metadata Store", test_metadata_store),
        ("Lineage Tracker", test_lineage_tracker),
        ("Audit Logger", test_audit_logger),
        ("Unity Catalog Integration", test_unity_catalog_integration),
        ("Governed Pipeline", test_governed_pipeline)
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
                print(f"\n✗ {name} test failed")
        except Exception as e:
            failed += 1
            print(f"\n✗ {name} test failed with exception: {str(e)}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)
    print(f"Total: {passed + failed}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    
    if failed == 0:
        print("\n✓ ALL TESTS PASSED!")
        return 0
    else:
        print(f"\n✗ {failed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
