"""
Lineage Tracker - Track data lineage through the lakehouse layers
Records relationships between datasets and transformations
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class LineageTracker:
    """Track data lineage and dependencies"""
    
    def __init__(self, db_path: str = "governance/catalog.db"):
        """
        Initialize lineage tracker
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = None
        self._initialize_database()
    
    def _initialize_database(self):
        """Create lineage tables if they don't exist"""
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
        
        cursor = self.conn.cursor()
        
        # Lineage relationships table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS lineage (
                lineage_id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_table TEXT NOT NULL,
                target_table TEXT NOT NULL,
                transformation_type TEXT NOT NULL,
                pipeline_name TEXT,
                created_at TEXT NOT NULL,
                metadata TEXT
            )
        """)
        
        # Pipeline runs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pipeline_runs (
                run_id INTEGER PRIMARY KEY AUTOINCREMENT,
                pipeline_name TEXT NOT NULL,
                run_type TEXT NOT NULL,
                status TEXT NOT NULL,
                started_at TEXT NOT NULL,
                completed_at TEXT,
                error_message TEXT,
                metadata TEXT
            )
        """)
        
        # Data flow table (records actual data movement)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS data_flows (
                flow_id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id INTEGER NOT NULL,
                source_table TEXT NOT NULL,
                target_table TEXT NOT NULL,
                records_read INTEGER,
                records_written INTEGER,
                bytes_read INTEGER,
                bytes_written INTEGER,
                duration_seconds REAL,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (run_id) REFERENCES pipeline_runs(run_id)
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_lineage_source ON lineage(source_table)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_lineage_target ON lineage(target_table)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_pipeline_runs_name ON pipeline_runs(pipeline_name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_data_flows_run ON data_flows(run_id)")
        
        self.conn.commit()
    
    def register_lineage(self, source_table: str, target_table: str,
                        transformation_type: str, pipeline_name: str = None,
                        metadata: Dict = None):
        """
        Register a lineage relationship between tables
        
        Args:
            source_table: Fully qualified source table name (catalog.schema.table)
            target_table: Fully qualified target table name
            transformation_type: Type of transformation (e.g., 'bronze_to_silver', 'aggregation')
            pipeline_name: Name of the pipeline performing the transformation
            metadata: Additional metadata about the transformation
        """
        cursor = self.conn.cursor()
        now = datetime.now().isoformat()
        
        cursor.execute("""
            INSERT INTO lineage (source_table, target_table, transformation_type, pipeline_name, created_at, metadata)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (source_table, target_table, transformation_type, pipeline_name, now, json.dumps(metadata or {})))
        
        self.conn.commit()
    
    def start_pipeline_run(self, pipeline_name: str, run_type: str = "full",
                          metadata: Dict = None) -> int:
        """
        Start tracking a pipeline run
        
        Args:
            pipeline_name: Name of the pipeline
            run_type: Type of run (full, incremental, etc.)
            metadata: Additional metadata about the run
            
        Returns:
            run_id for tracking this run
        """
        cursor = self.conn.cursor()
        now = datetime.now().isoformat()
        
        cursor.execute("""
            INSERT INTO pipeline_runs (pipeline_name, run_type, status, started_at, metadata)
            VALUES (?, ?, ?, ?, ?)
        """, (pipeline_name, run_type, "running", now, json.dumps(metadata or {})))
        
        self.conn.commit()
        return cursor.lastrowid
    
    def complete_pipeline_run(self, run_id: int, status: str = "success",
                             error_message: str = None):
        """
        Mark a pipeline run as complete
        
        Args:
            run_id: ID of the run
            status: Final status (success, failed, partial)
            error_message: Error message if failed
        """
        cursor = self.conn.cursor()
        now = datetime.now().isoformat()
        
        cursor.execute("""
            UPDATE pipeline_runs
            SET status = ?, completed_at = ?, error_message = ?
            WHERE run_id = ?
        """, (status, now, error_message, run_id))
        
        self.conn.commit()
    
    def record_data_flow(self, run_id: int, source_table: str, target_table: str,
                        records_read: int = None, records_written: int = None,
                        bytes_read: int = None, bytes_written: int = None,
                        duration_seconds: float = None):
        """
        Record actual data flow during a pipeline run
        
        Args:
            run_id: ID of the pipeline run
            source_table: Source table name
            target_table: Target table name
            records_read: Number of records read
            records_written: Number of records written
            bytes_read: Bytes read
            bytes_written: Bytes written
            duration_seconds: Duration of the operation
        """
        cursor = self.conn.cursor()
        now = datetime.now().isoformat()
        
        cursor.execute("""
            INSERT INTO data_flows (run_id, source_table, target_table, records_read, records_written,
                                  bytes_read, bytes_written, duration_seconds, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (run_id, source_table, target_table, records_read, records_written,
              bytes_read, bytes_written, duration_seconds, now))
        
        self.conn.commit()
    
    def get_upstream_lineage(self, table_name: str, max_depth: int = 10) -> List[Dict]:
        """
        Get upstream lineage (sources) for a table
        
        Args:
            table_name: Fully qualified table name
            max_depth: Maximum depth to traverse
            
        Returns:
            List of upstream tables and their relationships
        """
        cursor = self.conn.cursor()
        
        upstream = []
        visited = set()
        to_visit = [(table_name, 0)]
        
        while to_visit and len(upstream) < 100:  # Limit results
            current_table, depth = to_visit.pop(0)
            
            if current_table in visited or depth > max_depth:
                continue
            
            visited.add(current_table)
            
            cursor.execute("""
                SELECT source_table, target_table, transformation_type, pipeline_name, created_at
                FROM lineage
                WHERE target_table = ?
                ORDER BY created_at DESC
            """, (current_table,))
            
            for row in cursor.fetchall():
                lineage_info = dict(row)
                lineage_info['depth'] = depth
                upstream.append(lineage_info)
                
                # Add sources to visit
                if depth < max_depth:
                    to_visit.append((lineage_info['source_table'], depth + 1))
        
        return upstream
    
    def get_downstream_lineage(self, table_name: str, max_depth: int = 10) -> List[Dict]:
        """
        Get downstream lineage (consumers) for a table
        
        Args:
            table_name: Fully qualified table name
            max_depth: Maximum depth to traverse
            
        Returns:
            List of downstream tables and their relationships
        """
        cursor = self.conn.cursor()
        
        downstream = []
        visited = set()
        to_visit = [(table_name, 0)]
        
        while to_visit and len(downstream) < 100:  # Limit results
            current_table, depth = to_visit.pop(0)
            
            if current_table in visited or depth > max_depth:
                continue
            
            visited.add(current_table)
            
            cursor.execute("""
                SELECT source_table, target_table, transformation_type, pipeline_name, created_at
                FROM lineage
                WHERE source_table = ?
                ORDER BY created_at DESC
            """, (current_table,))
            
            for row in cursor.fetchall():
                lineage_info = dict(row)
                lineage_info['depth'] = depth
                downstream.append(lineage_info)
                
                # Add targets to visit
                if depth < max_depth:
                    to_visit.append((lineage_info['target_table'], depth + 1))
        
        return downstream
    
    def get_pipeline_history(self, pipeline_name: str, limit: int = 10) -> List[Dict]:
        """
        Get run history for a pipeline
        
        Args:
            pipeline_name: Name of the pipeline
            limit: Maximum number of runs to return
            
        Returns:
            List of pipeline runs
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM pipeline_runs
            WHERE pipeline_name = ?
            ORDER BY started_at DESC
            LIMIT ?
        """, (pipeline_name, limit))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_data_flow_stats(self, run_id: int) -> List[Dict]:
        """
        Get data flow statistics for a pipeline run
        
        Args:
            run_id: Pipeline run ID
            
        Returns:
            List of data flows with statistics
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM data_flows
            WHERE run_id = ?
            ORDER BY timestamp
        """, (run_id,))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_lineage_graph(self, table_name: str) -> Dict:
        """
        Get full lineage graph (both upstream and downstream)
        
        Args:
            table_name: Fully qualified table name
            
        Returns:
            Dictionary with upstream and downstream lineage
        """
        return {
            'table': table_name,
            'upstream': self.get_upstream_lineage(table_name),
            'downstream': self.get_downstream_lineage(table_name)
        }
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
