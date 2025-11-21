"""
Simple Lakehouse Pipeline - Tracer Bullet Implementation
A minimal end-to-end pipeline demonstrating Bronze -> Silver -> Gold flow
Uses only Python standard library with local file storage
"""

import json
import csv
import os
from datetime import datetime
from pathlib import Path


class SimpleLakehousePipeline:
    """Minimal lakehouse pipeline using local file system storage"""
    
    def __init__(self, base_path="data"):
        """Initialize pipeline with base data path"""
        self.base_path = Path(base_path)
        self.bronze_path = self.base_path / "bronze"
        self.silver_path = self.base_path / "silver"
        self.gold_path = self.base_path / "gold"
        
        # Ensure directories exist
        self.bronze_path.mkdir(parents=True, exist_ok=True)
        self.silver_path.mkdir(parents=True, exist_ok=True)
        self.gold_path.mkdir(parents=True, exist_ok=True)
    
    def ingest_to_bronze(self, source_file, dataset_name):
        """
        Ingest raw CSV data to bronze layer as JSON
        
        Args:
            source_file: Path to source CSV file
            dataset_name: Name of the dataset
            
        Returns:
            Path to bronze data file
        """
        print(f"[BRONZE] Ingesting data from {source_file}")
        
        # Read CSV data
        records = []
        with open(source_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Add metadata
                row['_ingestion_timestamp'] = datetime.now().isoformat()
                row['_source_file'] = str(source_file)
                records.append(row)
        
        # Write to bronze as JSON
        bronze_file = self.bronze_path / f"{dataset_name}.json"
        with open(bronze_file, 'w') as f:
            json.dump(records, f, indent=2)
        
        print(f"[BRONZE] Ingested {len(records)} records to {bronze_file}")
        return bronze_file
    
    def transform_to_silver(self, dataset_name):
        """
        Transform bronze data to silver layer with cleaning and validation
        
        Args:
            dataset_name: Name of the dataset
            
        Returns:
            Path to silver data file
        """
        print(f"[SILVER] Transforming {dataset_name}")
        
        # Read from bronze
        bronze_file = self.bronze_path / f"{dataset_name}.json"
        with open(bronze_file, 'r') as f:
            bronze_records = json.load(f)
        
        # Clean and validate data
        silver_records = []
        for record in bronze_records:
            # Remove duplicates by id (simple deduplication)
            # Remove records with missing required fields
            if record.get('id') and record.get('id').strip():
                # Create cleaned record
                clean_record = {k: v for k, v in record.items() if v}
                clean_record['_processed_timestamp'] = datetime.now().isoformat()
                silver_records.append(clean_record)
        
        # Remove duplicates by id
        seen_ids = set()
        deduplicated = []
        for record in silver_records:
            record_id = record['id']
            if record_id not in seen_ids:
                seen_ids.add(record_id)
                deduplicated.append(record)
        
        # Write to silver
        silver_file = self.silver_path / f"{dataset_name}.json"
        with open(silver_file, 'w') as f:
            json.dump(deduplicated, f, indent=2)
        
        quality_score = len(deduplicated) / len(bronze_records) if bronze_records else 0
        print(f"[SILVER] Processed {len(deduplicated)} clean records "
              f"(quality: {quality_score:.1%}) to {silver_file}")
        return silver_file
    
    def aggregate_to_gold(self, dataset_name, group_by_field):
        """
        Create business aggregates in gold layer
        
        Args:
            dataset_name: Name of the dataset
            group_by_field: Field to aggregate by
            
        Returns:
            Path to gold data file
        """
        print(f"[GOLD] Aggregating {dataset_name} by {group_by_field}")
        
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
        gold_file = self.gold_path / f"{dataset_name}_by_{group_by_field}.json"
        with open(gold_file, 'w') as f:
            json.dump(gold_records, f, indent=2)
        
        print(f"[GOLD] Created {len(gold_records)} aggregates in {gold_file}")
        return gold_file
    
    def run_full_pipeline(self, source_file, dataset_name, group_by_field):
        """
        Run the complete bronze -> silver -> gold pipeline
        
        Args:
            source_file: Path to source CSV file
            dataset_name: Name of the dataset
            group_by_field: Field to aggregate by in gold layer
        """
        print("=" * 70)
        print("Starting Simple Lakehouse Pipeline")
        print("=" * 70)
        
        try:
            # Bronze: Ingest raw data
            bronze_file = self.ingest_to_bronze(source_file, dataset_name)
            
            # Silver: Clean and validate
            silver_file = self.transform_to_silver(dataset_name)
            
            # Gold: Aggregate
            gold_file = self.aggregate_to_gold(dataset_name, group_by_field)
            
            print("=" * 70)
            print("Pipeline completed successfully!")
            print("=" * 70)
            print(f"Bronze: {bronze_file}")
            print(f"Silver: {silver_file}")
            print(f"Gold: {gold_file}")
            
            return {
                'bronze': str(bronze_file),
                'silver': str(silver_file),
                'gold': str(gold_file)
            }
            
        except Exception as e:
            print(f"ERROR: Pipeline failed: {str(e)}")
            raise


if __name__ == "__main__":
    # Example usage
    pipeline = SimpleLakehousePipeline()
    
    # Run pipeline with sample data
    pipeline.run_full_pipeline(
        source_file="data/sample_customers.csv",
        dataset_name="customers",
        group_by_field="region"
    )
