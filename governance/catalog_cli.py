#!/usr/bin/env python3
"""
Unity Catalog CLI - Command-line interface for catalog management
Provides tools to inspect, query, and manage the Unity Catalog
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from governance.unity_catalog import UnityCatalog


def list_tables_command(catalog: UnityCatalog, layer: str):
    """List all tables in a layer"""
    print(f"\nTables in {layer} layer:")
    print("-" * 70)
    
    tables = catalog.list_tables(layer)
    
    if not tables:
        print("No tables found")
        return
    
    for table in tables:
        print(f"\n{table['table_name']}")
        print(f"  Type: {table['table_type']}")
        print(f"  Location: {table['location']}")
        print(f"  Rows: {table.get('row_count', 'N/A')}")
        print(f"  Size: {table.get('size_bytes', 'N/A')} bytes")
        print(f"  Updated: {table['updated_at']}")


def describe_table_command(catalog: UnityCatalog, layer: str, table_name: str):
    """Describe a table in detail"""
    metadata = catalog.get_table_info(layer, table_name)
    
    if not metadata:
        print(f"Table {layer}.{table_name} not found")
        return
    
    print(f"\nTable: lakehouse.{layer}.{table_name}")
    print("=" * 70)
    print(f"Type: {metadata['table_type']}")
    print(f"Description: {metadata.get('description', 'N/A')}")
    print(f"Location: {metadata['location']}")
    print(f"Format: {metadata['format']}")
    print(f"Owner: {metadata.get('owner', 'N/A')}")
    print(f"Created: {metadata['created_at']}")
    print(f"Updated: {metadata['updated_at']}")
    print(f"Rows: {metadata.get('row_count', 'N/A')}")
    print(f"Size: {metadata.get('size_bytes', 'N/A')} bytes")
    
    if metadata.get('properties'):
        print(f"\nProperties:")
        props = json.loads(metadata['properties']) if isinstance(metadata['properties'], str) else metadata['properties']
        for key, value in props.items():
            print(f"  {key}: {value}")
    
    if metadata.get('columns'):
        print(f"\nColumns ({len(metadata['columns'])}):")
        print("-" * 70)
        for col in metadata['columns']:
            nullable = "NULL" if col['nullable'] else "NOT NULL"
            desc = f" - {col.get('description', '')}" if col.get('description') else ""
            print(f"  {col['column_name']:<30} {col['data_type']:<15} {nullable}{desc}")


def show_lineage_command(catalog: UnityCatalog, layer: str, table_name: str, direction: str = "both"):
    """Show lineage for a table"""
    lineage = catalog.get_table_lineage(layer, table_name)
    
    print(f"\nLineage for lakehouse.{layer}.{table_name}")
    print("=" * 70)
    
    if direction in ["both", "upstream"] and lineage['upstream']:
        print(f"\nUpstream Sources ({len(lineage['upstream'])}):")
        print("-" * 70)
        for dep in lineage['upstream']:
            print(f"  {dep['source_table']}")
            print(f"    → Transformation: {dep['transformation_type']}")
            if dep.get('pipeline_name'):
                print(f"    → Pipeline: {dep['pipeline_name']}")
            print(f"    → Registered: {dep['created_at']}")
            print()
    elif direction in ["both", "upstream"]:
        print("\nNo upstream sources found")
    
    if direction in ["both", "downstream"] and lineage['downstream']:
        print(f"\nDownstream Consumers ({len(lineage['downstream'])}):")
        print("-" * 70)
        for dep in lineage['downstream']:
            print(f"  {dep['target_table']}")
            print(f"    → Transformation: {dep['transformation_type']}")
            if dep.get('pipeline_name'):
                print(f"    → Pipeline: {dep['pipeline_name']}")
            print(f"    → Registered: {dep['created_at']}")
            print()
    elif direction in ["both", "downstream"]:
        print("\nNo downstream consumers found")


def show_access_history_command(catalog: UnityCatalog, layer: str, table_name: str, limit: int = 20):
    """Show access history for a table"""
    history = catalog.get_table_access_history(layer, table_name, limit)
    
    print(f"\nAccess History for lakehouse.{layer}.{table_name} (last {limit})")
    print("=" * 70)
    
    if not history:
        print("No access history found")
        return
    
    for access in history:
        rows = f"{access.get('rows_affected', 'N/A')} rows" if access.get('rows_affected') else ""
        duration = f"({access.get('duration_ms', 'N/A')}ms)" if access.get('duration_ms') else ""
        print(f"{access['timestamp']} - {access['user']:10} {access['access_type']:10} {rows:15} {duration}")


def show_quality_history_command(catalog: UnityCatalog, layer: str, table_name: str, limit: int = 20):
    """Show quality check history for a table"""
    history = catalog.get_table_quality_history(layer, table_name, limit)
    
    print(f"\nQuality Check History for lakehouse.{layer}.{table_name} (last {limit})")
    print("=" * 70)
    
    if not history:
        print("No quality check history found")
        return
    
    for check in history:
        status_symbol = "✓" if check['status'] == "passed" else "✗" if check['status'] == "failed" else "⚠"
        error_rate = f"error rate: {check['error_rate']:.1%}" if check['error_rate'] else ""
        print(f"{check['timestamp']} {status_symbol} {check['check_name']:25} "
              f"({check['check_type']}) {error_rate}")
        if check.get('passed_count') is not None:
            print(f"  → Passed: {check['passed_count']}, Failed: {check['failed_count']}")


def show_summary_command(catalog: UnityCatalog):
    """Show governance summary"""
    summary = catalog.get_governance_summary()
    
    print("\nUnity Catalog Summary")
    print("=" * 70)
    print(f"Catalog: {summary['catalog']}")
    print(f"Total Tables: {summary['total_tables']}")
    print(f"Total Records: {summary['total_records']}")
    print()
    
    for layer, info in summary['layers'].items():
        print(f"{layer.upper()} Layer:")
        print(f"  Tables: {info['table_count']}")
        print(f"  Records: {info['total_records']}")
        if info['tables']:
            print(f"  Table Names: {', '.join(info['tables'])}")
        print()


def export_catalog_command(catalog: UnityCatalog, output_path: str):
    """Export catalog to JSON"""
    catalog.export_catalog(output_path)
    print(f"\nCatalog exported to {output_path}")


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Unity Catalog CLI - Manage and inspect the lakehouse catalog",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Show summary of all tables
  python3 governance/catalog_cli.py summary
  
  # List tables in a layer
  python3 governance/catalog_cli.py list bronze
  
  # Describe a specific table
  python3 governance/catalog_cli.py describe silver customers
  
  # Show lineage for a table
  python3 governance/catalog_cli.py lineage gold customers_by_region
  
  # Show access history
  python3 governance/catalog_cli.py access silver customers --limit 10
  
  # Show quality check history
  python3 governance/catalog_cli.py quality silver customers
  
  # Export catalog metadata
  python3 governance/catalog_cli.py export catalog_export.json
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Summary command
    subparsers.add_parser('summary', help='Show governance summary')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List tables in a layer')
    list_parser.add_argument('layer', choices=['bronze', 'silver', 'gold'], help='Layer name')
    
    # Describe command
    desc_parser = subparsers.add_parser('describe', help='Describe a table')
    desc_parser.add_argument('layer', choices=['bronze', 'silver', 'gold'], help='Layer name')
    desc_parser.add_argument('table', help='Table name')
    
    # Lineage command
    lineage_parser = subparsers.add_parser('lineage', help='Show table lineage')
    lineage_parser.add_argument('layer', choices=['bronze', 'silver', 'gold'], help='Layer name')
    lineage_parser.add_argument('table', help='Table name')
    lineage_parser.add_argument('--direction', choices=['upstream', 'downstream', 'both'],
                               default='both', help='Lineage direction')
    
    # Access history command
    access_parser = subparsers.add_parser('access', help='Show access history')
    access_parser.add_argument('layer', choices=['bronze', 'silver', 'gold'], help='Layer name')
    access_parser.add_argument('table', help='Table name')
    access_parser.add_argument('--limit', type=int, default=20, help='Number of records to show')
    
    # Quality history command
    quality_parser = subparsers.add_parser('quality', help='Show quality check history')
    quality_parser.add_argument('layer', choices=['bronze', 'silver', 'gold'], help='Layer name')
    quality_parser.add_argument('table', help='Table name')
    quality_parser.add_argument('--limit', type=int, default=20, help='Number of records to show')
    
    # Export command
    export_parser = subparsers.add_parser('export', help='Export catalog to JSON')
    export_parser.add_argument('output', help='Output file path')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Initialize catalog
    catalog = UnityCatalog()
    
    try:
        # Execute command
        if args.command == 'summary':
            show_summary_command(catalog)
        elif args.command == 'list':
            list_tables_command(catalog, args.layer)
        elif args.command == 'describe':
            describe_table_command(catalog, args.layer, args.table)
        elif args.command == 'lineage':
            show_lineage_command(catalog, args.layer, args.table, args.direction)
        elif args.command == 'access':
            show_access_history_command(catalog, args.layer, args.table, args.limit)
        elif args.command == 'quality':
            show_quality_history_command(catalog, args.layer, args.table, args.limit)
        elif args.command == 'export':
            export_catalog_command(catalog, args.output)
        
        return 0
        
    finally:
        catalog.close()


if __name__ == "__main__":
    sys.exit(main())
