"""
Audit Logger - Track all data access and operations for compliance
Records who accessed what data and when
"""

import sqlite3
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional


class AuditLogger:
    """Audit logging for data governance and compliance"""
    
    def __init__(self, db_path: str = "governance/catalog.db"):
        """
        Initialize audit logger
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = None
        self._initialize_database()
    
    def _initialize_database(self):
        """Create audit tables if they don't exist"""
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
        
        cursor = self.conn.cursor()
        
        # Audit log table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                audit_id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                user TEXT NOT NULL,
                action TEXT NOT NULL,
                resource_type TEXT NOT NULL,
                resource_name TEXT NOT NULL,
                status TEXT NOT NULL,
                ip_address TEXT,
                session_id TEXT,
                details TEXT
            )
        """)
        
        # Data access log (specifically for table access)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS data_access_log (
                access_id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                user TEXT NOT NULL,
                table_name TEXT NOT NULL,
                access_type TEXT NOT NULL,
                rows_affected INTEGER,
                query TEXT,
                status TEXT NOT NULL,
                duration_ms INTEGER,
                details TEXT
            )
        """)
        
        # Data quality log
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quality_log (
                quality_id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                table_name TEXT NOT NULL,
                check_name TEXT NOT NULL,
                check_type TEXT NOT NULL,
                status TEXT NOT NULL,
                passed_count INTEGER,
                failed_count INTEGER,
                error_rate REAL,
                details TEXT
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_log(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_log(user)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_resource ON audit_log(resource_name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_access_timestamp ON data_access_log(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_access_table ON data_access_log(table_name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_quality_table ON quality_log(table_name)")
        
        self.conn.commit()
    
    def log_action(self, user: str, action: str, resource_type: str,
                   resource_name: str, status: str = "success",
                   ip_address: str = None, session_id: str = None,
                   details: Dict = None):
        """
        Log a general action in the audit log
        
        Args:
            user: User performing the action
            action: Action performed (create, read, update, delete, etc.)
            resource_type: Type of resource (catalog, schema, table, etc.)
            resource_name: Name of the resource
            status: Status of the action (success, failed, denied)
            ip_address: IP address of the user
            session_id: Session ID
            details: Additional details about the action
        """
        cursor = self.conn.cursor()
        now = datetime.now().isoformat()
        
        cursor.execute("""
            INSERT INTO audit_log (timestamp, user, action, resource_type, resource_name, 
                                 status, ip_address, session_id, details)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (now, user, action, resource_type, resource_name, status,
              ip_address, session_id, json.dumps(details or {})))
        
        self.conn.commit()
    
    def log_data_access(self, user: str, table_name: str, access_type: str,
                       rows_affected: int = None, query: str = None,
                       status: str = "success", duration_ms: int = None,
                       details: Dict = None):
        """
        Log data access operation
        
        Args:
            user: User accessing the data
            table_name: Fully qualified table name
            access_type: Type of access (select, insert, update, delete, scan)
            rows_affected: Number of rows read/written
            query: SQL query or operation description
            status: Status of the access (success, failed, denied)
            duration_ms: Duration of the operation in milliseconds
            details: Additional details
        """
        cursor = self.conn.cursor()
        now = datetime.now().isoformat()
        
        cursor.execute("""
            INSERT INTO data_access_log (timestamp, user, table_name, access_type, 
                                        rows_affected, query, status, duration_ms, details)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (now, user, table_name, access_type, rows_affected, query,
              status, duration_ms, json.dumps(details or {})))
        
        self.conn.commit()
    
    def log_quality_check(self, table_name: str, check_name: str, check_type: str,
                         status: str, passed_count: int = 0, failed_count: int = 0,
                         details: Dict = None):
        """
        Log data quality check results
        
        Args:
            table_name: Table being checked
            check_name: Name of the quality check
            check_type: Type of check (completeness, validity, consistency, etc.)
            status: Overall status (passed, failed, warning)
            passed_count: Number of records that passed
            failed_count: Number of records that failed
            details: Additional details about the check
        """
        cursor = self.conn.cursor()
        now = datetime.now().isoformat()
        
        total = passed_count + failed_count
        error_rate = failed_count / total if total > 0 else 0.0
        
        cursor.execute("""
            INSERT INTO quality_log (timestamp, table_name, check_name, check_type, 
                                   status, passed_count, failed_count, error_rate, details)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (now, table_name, check_name, check_type, status,
              passed_count, failed_count, error_rate, json.dumps(details or {})))
        
        self.conn.commit()
    
    def get_audit_trail(self, resource_name: str = None, user: str = None,
                       start_date: str = None, end_date: str = None,
                       limit: int = 100) -> List[Dict]:
        """
        Retrieve audit trail with optional filters
        
        Args:
            resource_name: Filter by resource name
            user: Filter by user
            start_date: Start date (ISO format)
            end_date: End date (ISO format)
            limit: Maximum number of records to return
            
        Returns:
            List of audit log entries
        """
        cursor = self.conn.cursor()
        
        query = "SELECT * FROM audit_log WHERE 1=1"
        params = []
        
        if resource_name:
            query += " AND resource_name = ?"
            params.append(resource_name)
        
        if user:
            query += " AND user = ?"
            params.append(user)
        
        if start_date:
            query += " AND timestamp >= ?"
            params.append(start_date)
        
        if end_date:
            query += " AND timestamp <= ?"
            params.append(end_date)
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]
    
    def get_data_access_history(self, table_name: str = None, user: str = None,
                               access_type: str = None, limit: int = 100) -> List[Dict]:
        """
        Get data access history with optional filters
        
        Args:
            table_name: Filter by table name
            user: Filter by user
            access_type: Filter by access type
            limit: Maximum number of records to return
            
        Returns:
            List of data access log entries
        """
        cursor = self.conn.cursor()
        
        query = "SELECT * FROM data_access_log WHERE 1=1"
        params = []
        
        if table_name:
            query += " AND table_name = ?"
            params.append(table_name)
        
        if user:
            query += " AND user = ?"
            params.append(user)
        
        if access_type:
            query += " AND access_type = ?"
            params.append(access_type)
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]
    
    def get_quality_history(self, table_name: str = None, check_type: str = None,
                           status: str = None, limit: int = 100) -> List[Dict]:
        """
        Get data quality check history
        
        Args:
            table_name: Filter by table name
            check_type: Filter by check type
            status: Filter by status
            limit: Maximum number of records to return
            
        Returns:
            List of quality check results
        """
        cursor = self.conn.cursor()
        
        query = "SELECT * FROM quality_log WHERE 1=1"
        params = []
        
        if table_name:
            query += " AND table_name = ?"
            params.append(table_name)
        
        if check_type:
            query += " AND check_type = ?"
            params.append(check_type)
        
        if status:
            query += " AND status = ?"
            params.append(status)
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]
    
    def get_access_summary(self, table_name: str, days: int = 30) -> Dict:
        """
        Get access summary for a table
        
        Args:
            table_name: Table name
            days: Number of days to look back
            
        Returns:
            Summary statistics
        """
        cursor = self.conn.cursor()
        
        start_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        # Count by access type
        cursor.execute("""
            SELECT access_type, COUNT(*) as count, SUM(rows_affected) as total_rows
            FROM data_access_log
            WHERE table_name = ? AND timestamp >= ?
            GROUP BY access_type
        """, (table_name, start_date))
        
        access_by_type = {row['access_type']: dict(row) for row in cursor.fetchall()}
        
        # Unique users
        cursor.execute("""
            SELECT COUNT(DISTINCT user) as unique_users
            FROM data_access_log
            WHERE table_name = ? AND timestamp >= ?
        """, (table_name, start_date))
        
        unique_users = cursor.fetchone()['unique_users']
        
        # Total accesses
        cursor.execute("""
            SELECT COUNT(*) as total_accesses
            FROM data_access_log
            WHERE table_name = ? AND timestamp >= ?
        """, (table_name, start_date))
        
        total_accesses = cursor.fetchone()['total_accesses']
        
        return {
            'table_name': table_name,
            'period_days': days,
            'total_accesses': total_accesses,
            'unique_users': unique_users,
            'access_by_type': access_by_type
        }
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
