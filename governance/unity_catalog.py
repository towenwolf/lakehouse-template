"""
Unity Catalog - Main interface for end-to-end data governance
Coordinates metadata management, lineage tracking, and audit logging
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from governance.metadata_store import MetadataStore
from governance.lineage_tracker import LineageTracker
from governance.audit_logger import AuditLogger


class UnityCatalog:
    """
    Unity Catalog - Unified governance for lakehouse
    
    Provides:
    - Metadata management for catalogs, schemas, and tables
    - Data lineage tracking
    - Audit logging
    - Data quality monitoring
    - Access control (simulated for local use)
    """
    
    def __init__(self, db_path: str = "governance/catalog.db", user: str = "system"):
        """
        Initialize Unity Catalog
        
        Args:
            db_path: Path to catalog database
            user: Current user for audit logging
        """
        self.db_path = db_path
        self.current_user = user
        
        # Initialize components
        self.metadata = MetadataStore(db_path)
        self.lineage = LineageTracker(db_path)
        self.audit = AuditLogger(db_path)
        
        # Initialize default catalog structure
        self._initialize_default_structure()
    
    def _initialize_default_structure(self):
        """Create default lakehouse catalog structure"""
        try:
            # Create main catalog
            self.metadata.create_catalog(
                name="lakehouse",
                description="Local lakehouse catalog for medallion architecture",
                owner=self.current_user,
                properties={"type": "lakehouse", "version": "1.0"}
            )
            
            # Create schemas for each layer
            for layer in ["bronze", "silver", "gold"]:
                self.metadata.create_schema(
                    catalog_name="lakehouse",
                    schema_name=layer,
                    location=f"data/{layer}",
                    description=f"{layer.capitalize()} layer for medallion architecture",
                    owner=self.current_user,
                    properties={"layer": layer}
                )
        except Exception:
            # Already exists, skip
            pass
    
    def register_table(self, layer: str, table_name: str, location: str,
                      columns: List[Dict[str, Any]] = None,
                      description: str = None, format: str = "json",
                      row_count: int = None, size_bytes: int = None,
                      properties: Dict = None) -> int:
        """
        Register a table in the catalog
        
        Args:
            layer: Layer name (bronze, silver, gold)
            table_name: Name of the table
            location: File system location
            columns: List of column definitions
            description: Table description
            format: File format (json, parquet, delta, etc.)
            row_count: Number of rows
            size_bytes: Size in bytes
            properties: Additional properties
            
        Returns:
            Table ID
        """
        # Determine table type based on layer
        table_type = {
            "bronze": "raw",
            "silver": "cleaned",
            "gold": "aggregate"
        }.get(layer, "table")
        
        # Register table
        table_id = self.metadata.register_table(
            catalog_name="lakehouse",
            schema_name=layer,
            table_name=table_name,
            table_type=table_type,
            location=location,
            format=format,
            description=description,
            owner=self.current_user,
            row_count=row_count,
            size_bytes=size_bytes,
            properties=properties
        )
        
        # Register columns if provided
        if columns:
            self.metadata.register_columns(
                catalog_name="lakehouse",
                schema_name=layer,
                table_name=table_name,
                columns=columns
            )
        
        # Audit log
        self.audit.log_action(
            user=self.current_user,
            action="create_table",
            resource_type="table",
            resource_name=f"lakehouse.{layer}.{table_name}",
            status="success",
            details={"location": location, "format": format}
        )
        
        return table_id
    
    def register_transformation(self, source_layer: str, source_table: str,
                               target_layer: str, target_table: str,
                               transformation_type: str, pipeline_name: str = None,
                               metadata: Dict = None):
        """
        Register a data transformation in lineage
        
        Args:
            source_layer: Source layer (bronze, silver, gold)
            source_table: Source table name
            target_layer: Target layer
            target_table: Target table name
            transformation_type: Type of transformation
            pipeline_name: Name of the pipeline
            metadata: Additional metadata
        """
        source_fqn = f"lakehouse.{source_layer}.{source_table}"
        target_fqn = f"lakehouse.{target_layer}.{target_table}"
        
        self.lineage.register_lineage(
            source_table=source_fqn,
            target_table=target_fqn,
            transformation_type=transformation_type,
            pipeline_name=pipeline_name,
            metadata=metadata
        )
        
        # Audit log
        self.audit.log_action(
            user=self.current_user,
            action="register_lineage",
            resource_type="transformation",
            resource_name=f"{source_fqn} -> {target_fqn}",
            status="success",
            details={"type": transformation_type, "pipeline": pipeline_name}
        )
    
    def start_pipeline_run(self, pipeline_name: str, run_type: str = "full",
                          metadata: Dict = None) -> int:
        """Start tracking a pipeline run"""
        run_id = self.lineage.start_pipeline_run(pipeline_name, run_type, metadata)
        
        self.audit.log_action(
            user=self.current_user,
            action="start_pipeline",
            resource_type="pipeline",
            resource_name=pipeline_name,
            status="success",
            details={"run_id": run_id, "run_type": run_type}
        )
        
        return run_id
    
    def complete_pipeline_run(self, run_id: int, status: str = "success",
                             error_message: str = None):
        """Complete a pipeline run"""
        self.lineage.complete_pipeline_run(run_id, status, error_message)
        
        self.audit.log_action(
            user=self.current_user,
            action="complete_pipeline",
            resource_type="pipeline",
            resource_name=f"run_{run_id}",
            status=status,
            details={"error": error_message} if error_message else None
        )
    
    def record_data_flow(self, run_id: int, source_layer: str, source_table: str,
                        target_layer: str, target_table: str,
                        records_read: int = None, records_written: int = None,
                        bytes_read: int = None, bytes_written: int = None,
                        duration_seconds: float = None):
        """Record data flow during pipeline execution"""
        source_fqn = f"lakehouse.{source_layer}.{source_table}"
        target_fqn = f"lakehouse.{target_layer}.{target_table}"
        
        self.lineage.record_data_flow(
            run_id=run_id,
            source_table=source_fqn,
            target_table=target_fqn,
            records_read=records_read,
            records_written=records_written,
            bytes_read=bytes_read,
            bytes_written=bytes_written,
            duration_seconds=duration_seconds
        )
        
        # Log data access
        if records_read:
            self.audit.log_data_access(
                user=self.current_user,
                table_name=source_fqn,
                access_type="read",
                rows_affected=records_read,
                status="success",
                duration_ms=int(duration_seconds * 1000) if duration_seconds else None
            )
        
        if records_written:
            self.audit.log_data_access(
                user=self.current_user,
                table_name=target_fqn,
                access_type="write",
                rows_affected=records_written,
                status="success",
                duration_ms=int(duration_seconds * 1000) if duration_seconds else None
            )
    
    def log_quality_check(self, layer: str, table_name: str, check_name: str,
                         check_type: str, status: str, passed_count: int = 0,
                         failed_count: int = 0, details: Dict = None):
        """Log data quality check results"""
        table_fqn = f"lakehouse.{layer}.{table_name}"
        
        self.audit.log_quality_check(
            table_name=table_fqn,
            check_name=check_name,
            check_type=check_type,
            status=status,
            passed_count=passed_count,
            failed_count=failed_count,
            details=details
        )
    
    def get_table_info(self, layer: str, table_name: str) -> Optional[Dict]:
        """Get complete information about a table"""
        return self.metadata.get_table_metadata("lakehouse", layer, table_name)
    
    def get_table_lineage(self, layer: str, table_name: str) -> Dict:
        """Get lineage information for a table"""
        table_fqn = f"lakehouse.{layer}.{table_name}"
        return self.lineage.get_lineage_graph(table_fqn)
    
    def get_table_access_history(self, layer: str, table_name: str, limit: int = 100) -> List[Dict]:
        """Get access history for a table"""
        table_fqn = f"lakehouse.{layer}.{table_name}"
        return self.audit.get_data_access_history(table_name=table_fqn, limit=limit)
    
    def get_table_quality_history(self, layer: str, table_name: str, limit: int = 100) -> List[Dict]:
        """Get quality check history for a table"""
        table_fqn = f"lakehouse.{layer}.{table_name}"
        return self.audit.get_quality_history(table_name=table_fqn, limit=limit)
    
    def list_tables(self, layer: str) -> List[Dict]:
        """List all tables in a layer"""
        return self.metadata.list_tables("lakehouse", layer)
    
    def update_table_stats(self, layer: str, table_name: str,
                          row_count: int, size_bytes: int):
        """Update table statistics"""
        self.metadata.update_table_stats("lakehouse", layer, table_name,
                                        row_count, size_bytes)
        
        self.audit.log_action(
            user=self.current_user,
            action="update_stats",
            resource_type="table",
            resource_name=f"lakehouse.{layer}.{table_name}",
            status="success",
            details={"row_count": row_count, "size_bytes": size_bytes}
        )
    
    def get_governance_summary(self) -> Dict:
        """Get overall governance summary"""
        summary = {
            "catalog": "lakehouse",
            "layers": {},
            "total_tables": 0,
            "total_records": 0
        }
        
        for layer in ["bronze", "silver", "gold"]:
            tables = self.list_tables(layer)
            total_rows = sum(t.get('row_count', 0) or 0 for t in tables)
            
            summary["layers"][layer] = {
                "table_count": len(tables),
                "total_records": total_rows,
                "tables": [t['table_name'] for t in tables]
            }
            
            summary["total_tables"] += len(tables)
            summary["total_records"] += total_rows
        
        return summary
    
    def export_catalog(self, output_path: str):
        """Export catalog metadata to JSON file"""
        export_data = {
            "export_date": datetime.now().isoformat(),
            "catalog": "lakehouse",
            "layers": {}
        }
        
        for layer in ["bronze", "silver", "gold"]:
            tables = self.list_tables(layer)
            layer_data = []
            
            for table in tables:
                table_meta = self.get_table_info(layer, table['table_name'])
                if table_meta:
                    layer_data.append(table_meta)
            
            export_data["layers"][layer] = layer_data
        
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        self.audit.log_action(
            user=self.current_user,
            action="export_catalog",
            resource_type="catalog",
            resource_name="lakehouse",
            status="success",
            details={"output_path": output_path}
        )
    
    def close(self):
        """Close all connections"""
        self.metadata.close()
        self.lineage.close()
        self.audit.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
