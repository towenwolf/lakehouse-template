#!/usr/bin/env python3
"""
Unity Catalog Demo
Demonstrates the key features of Unity Catalog governance
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from governance.unity_catalog import UnityCatalog
from pipelines.governed_pipeline import GovernedLakehousePipeline


def demo_basic_governance():
    """Demonstrate basic governance features"""
    print("\n" + "=" * 70)
    print("DEMO 1: Basic Governance Features")
    print("=" * 70)
    
    with UnityCatalog(user="demo_user") as catalog:
        # Register a table manually
        print("\n1. Registering a table in the catalog...")
        catalog.register_table(
            layer="bronze",
            table_name="demo_events",
            location="data/bronze/demo_events.json",
            columns=[
                {'name': 'event_id', 'type': 'string', 'nullable': False},
                {'name': 'timestamp', 'type': 'timestamp', 'nullable': False},
                {'name': 'user_id', 'type': 'string', 'nullable': True},
                {'name': 'event_type', 'type': 'string', 'nullable': False}
            ],
            description="Demo event data",
            row_count=1000,
            size_bytes=50000,
            properties={
                "data_owner": "analytics_team",
                "refresh_frequency": "daily",
                "contains_pii": False
            }
        )
        print("✓ Table registered successfully")
        
        # Get table information
        print("\n2. Retrieving table information...")
        info = catalog.get_table_info("bronze", "demo_events")
        print(f"   Table: {info['table_name']}")
        print(f"   Type: {info['table_type']}")
        print(f"   Location: {info['location']}")
        print(f"   Rows: {info['row_count']}")
        print(f"   Columns: {len(info['columns'])}")
        
        # Register a transformation
        print("\n3. Registering a transformation...")
        catalog.register_transformation(
            source_layer="bronze",
            source_table="demo_events",
            target_layer="silver",
            target_table="demo_events_clean",
            transformation_type="deduplication_and_enrichment",
            pipeline_name="event_processing"
        )
        print("✓ Transformation registered")
        
        # Get governance summary
        print("\n4. Getting governance summary...")
        summary = catalog.get_governance_summary()
        print(f"   Total Tables: {summary['total_tables']}")
        print(f"   Total Records: {summary['total_records']}")
        for layer, info in summary['layers'].items():
            print(f"   {layer.upper()}: {info['table_count']} tables, {info['total_records']} records")


def demo_pipeline_with_governance():
    """Demonstrate governed pipeline"""
    print("\n" + "=" * 70)
    print("DEMO 2: Governed Pipeline with Automatic Governance")
    print("=" * 70)
    
    with GovernedLakehousePipeline(user="demo_user") as pipeline:
        print("\nRunning governed pipeline...")
        print("(Governance tracking happens automatically)")
        print()
        
        result = pipeline.run_full_pipeline(
            source_file="data/sample_customers.csv",
            dataset_name="demo_customers",
            group_by_field="region"
        )
        
        print("\n" + "-" * 70)
        print("What was tracked automatically:")
        print("-" * 70)
        print("✓ All tables registered with metadata")
        print("✓ Data lineage captured (Bronze → Silver → Gold)")
        print("✓ Data access logged for compliance")
        print("✓ Quality checks recorded")
        print("✓ Pipeline run tracked with timing")
        
        # Show lineage
        print("\n" + "-" * 70)
        print("Lineage Information:")
        print("-" * 70)
        
        lineage = pipeline.catalog.get_table_lineage("gold", "demo_customers_by_region")
        print(f"\nUpstream sources for gold.demo_customers_by_region:")
        for dep in lineage['upstream']:
            print(f"  ← {dep['source_table']}")
            print(f"    via {dep['transformation_type']}")
        
        # Show quality checks
        print("\n" + "-" * 70)
        print("Quality Checks:")
        print("-" * 70)
        
        quality = pipeline.catalog.get_table_quality_history("silver", "demo_customers", limit=5)
        print(f"\nQuality checks for silver.demo_customers:")
        for check in quality:
            status_symbol = "✓" if check['status'] == "passed" else "✗"
            print(f"  {status_symbol} {check['check_name']}: {check['status']}")
            print(f"    Error rate: {check['error_rate']:.1%}")


def demo_cli_tools():
    """Demonstrate CLI tools"""
    print("\n" + "=" * 70)
    print("DEMO 3: CLI Tools")
    print("=" * 70)
    print("\nThe catalog CLI provides easy access to governance data:")
    print()
    print("# Show summary")
    print("$ python3 governance/catalog_cli.py summary")
    print()
    print("# List tables")
    print("$ python3 governance/catalog_cli.py list bronze")
    print()
    print("# Describe table")
    print("$ python3 governance/catalog_cli.py describe silver customers")
    print()
    print("# Show lineage")
    print("$ python3 governance/catalog_cli.py lineage gold customers_by_region")
    print()
    print("# View access history")
    print("$ python3 governance/catalog_cli.py access silver customers --limit 10")
    print()
    print("# View quality checks")
    print("$ python3 governance/catalog_cli.py quality silver customers")
    print()
    print("# Export catalog")
    print("$ python3 governance/catalog_cli.py export catalog_backup.json")


def main():
    """Run all demos"""
    print("\n" + "=" * 70)
    print("Unity Catalog Demo")
    print("Comprehensive Data Governance for Lakehouse")
    print("=" * 70)
    
    demos = [
        ("Basic Governance", demo_basic_governance),
        ("Governed Pipeline", demo_pipeline_with_governance),
        ("CLI Tools", demo_cli_tools)
    ]
    
    for name, demo_func in demos:
        try:
            demo_func()
        except Exception as e:
            print(f"\n✗ Demo '{name}' encountered an error: {str(e)}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 70)
    print("Demo Complete!")
    print("=" * 70)
    print("\nKey Takeaways:")
    print("1. Unity Catalog automatically tracks metadata, lineage, and access")
    print("2. Use GovernedLakehousePipeline for automatic governance")
    print("3. CLI tools make it easy to explore and manage the catalog")
    print("4. All governance data is stored in governance/catalog.db")
    print("5. Comprehensive audit trail for compliance requirements")
    print()
    print("Next Steps:")
    print("- Review docs/UNITY_CATALOG.md for detailed documentation")
    print("- Try the CLI: python3 governance/catalog_cli.py summary")
    print("- Integrate governance into your own pipelines")
    print()


if __name__ == "__main__":
    main()
