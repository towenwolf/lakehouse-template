"""
Governed Lakehouse Pipeline - Pipeline with Unity Catalog Integration
Extends SimpleLakehousePipeline with full governance capabilities
"""

import json
import csv
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from pipelines.simple_pipeline import SimpleLakehousePipeline
from governance.unity_catalog import UnityCatalog


class GovernedLakehousePipeline(SimpleLakehousePipeline):
    """
    Lakehouse pipeline with Unity Catalog governance
    
    Adds comprehensive governance features:
    - Metadata management
    - Lineage tracking
    - Audit logging
    - Data quality monitoring
    """
    
    def __init__(self, base_path="data", user="system"):
        """
        Initialize governed pipeline
        
        Args:
            base_path: Base path for data storage
            user: Current user for audit logging
        """
        super().__init__(base_path)
        self.catalog = UnityCatalog(user=user)
        self.current_run_id = None
    
    def ingest_to_bronze(self, source_file, dataset_name):
        """
        Ingest raw CSV data to bronze layer with governance
        
        Args:
            source_file: Path to source CSV file
            dataset_name: Name of the dataset
            
        Returns:
            Path to bronze data file
        """
        print(f"[BRONZE] Ingesting data from {source_file}")
        start_time = time.time()
        
        # Read CSV data
        records = []
        columns_detected = None
        
        with open(source_file, 'r') as f:
            reader = csv.DictReader(f)
            columns_detected = reader.fieldnames
            
            for row in reader:
                # Add metadata
                row['_ingestion_timestamp'] = datetime.now().isoformat()
                row['_source_file'] = str(source_file)
                records.append(row)
        
        # Write to bronze as JSON
        bronze_file = self.bronze_path / f"{dataset_name}.json"
        with open(bronze_file, 'w') as f:
            json.dump(records, f, indent=2)
        
        duration = time.time() - start_time
        file_size = os.path.getsize(bronze_file)
        
        # Register in catalog
        columns = [
            {'name': col, 'type': 'string', 'nullable': True}
            for col in columns_detected
        ] if columns_detected else []
        
        # Add metadata columns
        columns.extend([
            {'name': '_ingestion_timestamp', 'type': 'timestamp', 'nullable': False},
            {'name': '_source_file', 'type': 'string', 'nullable': False}
        ])
        
        self.catalog.register_table(
            layer="bronze",
            table_name=dataset_name,
            location=str(bronze_file),
            columns=columns,
            description=f"Raw data ingested from {source_file}",
            format="json",
            row_count=len(records),
            size_bytes=file_size,
            properties={"source": str(source_file), "ingestion_type": "batch"}
        )
        
        # Record data flow if part of a pipeline run
        if self.current_run_id:
            self.catalog.record_data_flow(
                run_id=self.current_run_id,
                source_layer="external",
                source_table=Path(source_file).stem,
                target_layer="bronze",
                target_table=dataset_name,
                records_read=len(records),
                records_written=len(records),
                bytes_read=os.path.getsize(source_file),
                bytes_written=file_size,
                duration_seconds=duration
            )
        
        print(f"[BRONZE] Ingested {len(records)} records to {bronze_file}")
        print(f"[GOVERNANCE] Registered table in catalog: bronze.{dataset_name}")
        
        return bronze_file
    
    def transform_to_silver(self, dataset_name):
        """
        Transform bronze data to silver layer with quality checks and governance
        
        Args:
            dataset_name: Name of the dataset
            
        Returns:
            Path to silver data file
        """
        print(f"[SILVER] Transforming {dataset_name}")
        start_time = time.time()
        
        # Read from bronze
        bronze_file = self.bronze_path / f"{dataset_name}.json"
        with open(bronze_file, 'r') as f:
            bronze_records = json.load(f)
        
        # Quality checks
        records_with_id = sum(1 for r in bronze_records if r.get('id') and r.get('id').strip())
        null_ids = len(bronze_records) - records_with_id
        
        # Clean and validate data
        silver_records = []
        for record in bronze_records:
            # Remove records with missing required fields
            if record.get('id') and record.get('id').strip():
                # Create cleaned record (keep all fields except None values)
                clean_record = {k: v for k, v in record.items() if v is not None}
                clean_record['_processed_timestamp'] = datetime.now().isoformat()
                silver_records.append(clean_record)
        
        # Remove duplicates by id
        seen_ids = set()
        deduplicated = []
        duplicate_count = 0
        
        for record in silver_records:
            record_id = record['id']
            if record_id not in seen_ids:
                seen_ids.add(record_id)
                deduplicated.append(record)
            else:
                duplicate_count += 1
        
        # Write to silver
        silver_file = self.silver_path / f"{dataset_name}.json"
        with open(silver_file, 'w') as f:
            json.dump(deduplicated, f, indent=2)
        
        duration = time.time() - start_time
        file_size = os.path.getsize(silver_file)
        data_retention_rate = len(deduplicated) / len(bronze_records) if bronze_records else 0
        
        # Detect columns from first record
        columns = []
        if deduplicated:
            for key in deduplicated[0].keys():
                columns.append({'name': key, 'type': 'string', 'nullable': True})
        
        # Register in catalog
        self.catalog.register_table(
            layer="silver",
            table_name=dataset_name,
            location=str(silver_file),
            columns=columns,
            description=f"Cleaned and validated data from bronze.{dataset_name}",
            format="json",
            row_count=len(deduplicated),
            size_bytes=file_size,
            properties={
                "data_retention_rate": data_retention_rate,
                "duplicates_removed": duplicate_count,
                "null_ids_removed": null_ids
            }
        )
        
        # Register lineage
        self.catalog.register_transformation(
            source_layer="bronze",
            source_table=dataset_name,
            target_layer="silver",
            target_table=dataset_name,
            transformation_type="cleaning_and_deduplication",
            pipeline_name="governed_pipeline",
            metadata={
                "duplicates_removed": duplicate_count,
                "null_records_removed": null_ids,
                "data_retention_rate": data_retention_rate
            }
        )
        
        # Record data flow
        if self.current_run_id:
            self.catalog.record_data_flow(
                run_id=self.current_run_id,
                source_layer="bronze",
                source_table=dataset_name,
                target_layer="silver",
                target_table=dataset_name,
                records_read=len(bronze_records),
                records_written=len(deduplicated),
                bytes_read=os.path.getsize(bronze_file),
                bytes_written=file_size,
                duration_seconds=duration
            )
        
        # Log quality checks
        self.catalog.log_quality_check(
            layer="silver",
            table_name=dataset_name,
            check_name="id_completeness",
            check_type="completeness",
            status="passed" if null_ids == 0 else "warning",
            passed_count=records_with_id,
            failed_count=null_ids,
            details={"field": "id", "requirement": "not_null"}
        )
        
        self.catalog.log_quality_check(
            layer="silver",
            table_name=dataset_name,
            check_name="deduplication",
            check_type="uniqueness",
            status="passed",
            passed_count=len(deduplicated),
            failed_count=duplicate_count,
            details={"key": "id", "duplicates_removed": duplicate_count}
        )
        
        print(f"[SILVER] Processed {len(deduplicated)} clean records "
              f"(retention: {data_retention_rate:.1%}) to {silver_file}")
        print(f"[GOVERNANCE] Registered table in catalog: silver.{dataset_name}")
        print(f"[GOVERNANCE] Logged 2 quality checks")
        
        return silver_file
    
    def aggregate_to_gold(self, dataset_name, group_by_field):
        """
        Create business aggregates in gold layer with governance
        
        Args:
            dataset_name: Name of the dataset
            group_by_field: Field to aggregate by
            
        Returns:
            Path to gold data file
        """
        print(f"[GOLD] Aggregating {dataset_name} by {group_by_field}")
        start_time = time.time()
        
        # Read from silver
        silver_file = self.silver_path / f"{dataset_name}.json"
        with open(silver_file, 'r') as f:
            silver_records = json.load(f)
        
        # Create aggregates
        aggregates = {}
        for record in silver_records:
            key = record.get(group_by_field, 'unknown')
            if key not in aggregates:
                aggregates[key] = {
                    group_by_field: key,
                    'count': 0,
                    'records': []
                }
            aggregates[key]['count'] += 1
            aggregates[key]['records'].append(record.get('id'))
        
        # Convert to list and add metadata
        gold_records = []
        for key, agg in aggregates.items():
            agg['_aggregation_timestamp'] = datetime.now().isoformat()
            gold_records.append(agg)
        
        # Write to gold
        gold_table_name = f"{dataset_name}_by_{group_by_field}"
        gold_file = self.gold_path / f"{gold_table_name}.json"
        with open(gold_file, 'w') as f:
            json.dump(gold_records, f, indent=2)
        
        duration = time.time() - start_time
        file_size = os.path.getsize(gold_file)
        
        # Register in catalog
        columns = [
            {'name': group_by_field, 'type': 'string', 'nullable': False},
            {'name': 'count', 'type': 'integer', 'nullable': False},
            {'name': 'records', 'type': 'array', 'nullable': False},
            {'name': '_aggregation_timestamp', 'type': 'timestamp', 'nullable': False}
        ]
        
        self.catalog.register_table(
            layer="gold",
            table_name=gold_table_name,
            location=str(gold_file),
            columns=columns,
            description=f"Aggregated metrics from silver.{dataset_name} grouped by {group_by_field}",
            format="json",
            row_count=len(gold_records),
            size_bytes=file_size,
            properties={
                "aggregation_type": "count",
                "group_by": group_by_field,
                "source_records": len(silver_records)
            }
        )
        
        # Register lineage
        self.catalog.register_transformation(
            source_layer="silver",
            source_table=dataset_name,
            target_layer="gold",
            target_table=gold_table_name,
            transformation_type="aggregation",
            pipeline_name="governed_pipeline",
            metadata={
                "aggregation_type": "count",
                "group_by": group_by_field,
                "aggregate_count": len(gold_records)
            }
        )
        
        # Record data flow
        if self.current_run_id:
            self.catalog.record_data_flow(
                run_id=self.current_run_id,
                source_layer="silver",
                source_table=dataset_name,
                target_layer="gold",
                target_table=gold_table_name,
                records_read=len(silver_records),
                records_written=len(gold_records),
                bytes_read=os.path.getsize(silver_file),
                bytes_written=file_size,
                duration_seconds=duration
            )
        
        print(f"[GOLD] Created {len(gold_records)} aggregates in {gold_file}")
        print(f"[GOVERNANCE] Registered table in catalog: gold.{gold_table_name}")
        
        return gold_file
    
    def run_full_pipeline(self, source_file, dataset_name, group_by_field):
        """
        Run the complete bronze -> silver -> gold pipeline with governance
        
        Args:
            source_file: Path to source CSV file
            dataset_name: Name of the dataset
            group_by_field: Field to aggregate by in gold layer
        """
        print("=" * 70)
        print("Starting Governed Lakehouse Pipeline")
        print("=" * 70)
        
        # Start pipeline run tracking
        self.current_run_id = self.catalog.start_pipeline_run(
            pipeline_name="governed_pipeline",
            run_type="full",
            metadata={
                "source_file": str(source_file),
                "dataset_name": dataset_name,
                "group_by_field": group_by_field
            }
        )
        
        print(f"[GOVERNANCE] Started pipeline run ID: {self.current_run_id}")
        
        try:
            # Bronze: Ingest raw data
            bronze_file = self.ingest_to_bronze(source_file, dataset_name)
            
            # Silver: Clean and validate
            silver_file = self.transform_to_silver(dataset_name)
            
            # Gold: Aggregate
            gold_file = self.aggregate_to_gold(dataset_name, group_by_field)
            
            # Complete pipeline run
            self.catalog.complete_pipeline_run(self.current_run_id, status="success")
            
            print("=" * 70)
            print("Pipeline completed successfully!")
            print("=" * 70)
            print(f"Bronze: {bronze_file}")
            print(f"Silver: {silver_file}")
            print(f"Gold: {gold_file}")
            print("")
            print("Governance Summary:")
            print("-" * 70)
            
            # Print governance summary
            summary = self.catalog.get_governance_summary()
            print(f"Catalog: {summary['catalog']}")
            print(f"Total Tables: {summary['total_tables']}")
            print(f"Total Records: {summary['total_records']}")
            print("")
            
            for layer, info in summary['layers'].items():
                print(f"{layer.upper()}: {info['table_count']} tables, "
                      f"{info['total_records']} records")
            
            return {
                'bronze': str(bronze_file),
                'silver': str(silver_file),
                'gold': str(gold_file),
                'run_id': self.current_run_id
            }
            
        except Exception as e:
            # Complete with failure
            self.catalog.complete_pipeline_run(
                self.current_run_id,
                status="failed",
                error_message=str(e)
            )
            print(f"ERROR: Pipeline failed: {str(e)}")
            raise
        finally:
            self.current_run_id = None
    
    def show_table_info(self, layer: str, table_name: str):
        """Display detailed information about a table"""
        print(f"\n{'=' * 70}")
        print(f"Table Information: {layer}.{table_name}")
        print('=' * 70)
        
        # Get metadata
        metadata = self.catalog.get_table_info(layer, table_name)
        if metadata:
            print(f"Type: {metadata['table_type']}")
            print(f"Location: {metadata['location']}")
            print(f"Format: {metadata['format']}")
            print(f"Rows: {metadata.get('row_count', 'N/A')}")
            print(f"Size: {metadata.get('size_bytes', 'N/A')} bytes")
            print(f"Created: {metadata['created_at']}")
            print(f"Updated: {metadata['updated_at']}")
            
            if metadata.get('columns'):
                print(f"\nColumns ({len(metadata['columns'])}):")
                for col in metadata['columns']:
                    nullable = "nullable" if col['nullable'] else "not null"
                    print(f"  - {col['column_name']}: {col['data_type']} ({nullable})")
        
        # Get lineage
        lineage = self.catalog.get_table_lineage(layer, table_name)
        if lineage['upstream']:
            print(f"\nUpstream Dependencies ({len(lineage['upstream'])}):")
            for dep in lineage['upstream'][:5]:  # Show first 5
                print(f"  - {dep['source_table']} ({dep['transformation_type']})")
        
        if lineage['downstream']:
            print(f"\nDownstream Consumers ({len(lineage['downstream'])}):")
            for dep in lineage['downstream'][:5]:  # Show first 5
                print(f"  - {dep['target_table']} ({dep['transformation_type']})")
        
        # Get recent access
        access = self.catalog.get_table_access_history(layer, table_name, limit=5)
        if access:
            print(f"\nRecent Access ({len(access)}):")
            for acc in access:
                print(f"  - {acc['timestamp']}: {acc['access_type']} "
                      f"({acc.get('rows_affected', 'N/A')} rows)")
        
        # Get quality history
        quality = self.catalog.get_table_quality_history(layer, table_name, limit=5)
        if quality:
            print(f"\nQuality Checks ({len(quality)}):")
            for qc in quality:
                print(f"  - {qc['check_name']}: {qc['status']} "
                      f"(error rate: {qc['error_rate']:.1%})")
    
    def close(self):
        """Close catalog connections"""
        self.catalog.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


if __name__ == "__main__":
    # Example usage
    with GovernedLakehousePipeline(user="admin") as pipeline:
        # Run pipeline with sample data
        result = pipeline.run_full_pipeline(
            source_file="data/sample_customers.csv",
            dataset_name="customers",
            group_by_field="region"
        )
        
        # Show detailed info about created tables
        print("\n" + "=" * 70)
        print("Detailed Table Information")
        print("=" * 70)
        
        pipeline.show_table_info("bronze", "customers")
        pipeline.show_table_info("silver", "customers")
        pipeline.show_table_info("gold", "customers_by_region")
