"""
Metadata Store - SQLite-based storage for catalog metadata
Stores information about databases, schemas, tables, and columns
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any


class MetadataStore:
    """Persistent metadata storage using SQLite"""
    
    def __init__(self, db_path: str = "governance/catalog.db"):
        """
        Initialize metadata store
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = None
        self._initialize_database()
    
    def _initialize_database(self):
        """Create database schema if it doesn't exist"""
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
        
        cursor = self.conn.cursor()
        
        # Catalogs table (top-level namespace)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS catalogs (
                catalog_id INTEGER PRIMARY KEY AUTOINCREMENT,
                catalog_name TEXT UNIQUE NOT NULL,
                description TEXT,
                owner TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                properties TEXT
            )
        """)
        
        # Schemas table (databases within catalogs)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schemas (
                schema_id INTEGER PRIMARY KEY AUTOINCREMENT,
                catalog_id INTEGER NOT NULL,
                schema_name TEXT NOT NULL,
                description TEXT,
                location TEXT,
                owner TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                properties TEXT,
                FOREIGN KEY (catalog_id) REFERENCES catalogs(catalog_id),
                UNIQUE(catalog_id, schema_name)
            )
        """)
        
        # Tables table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tables (
                table_id INTEGER PRIMARY KEY AUTOINCREMENT,
                schema_id INTEGER NOT NULL,
                table_name TEXT NOT NULL,
                table_type TEXT NOT NULL,
                description TEXT,
                location TEXT NOT NULL,
                format TEXT,
                owner TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                row_count INTEGER,
                size_bytes INTEGER,
                properties TEXT,
                FOREIGN KEY (schema_id) REFERENCES schemas(schema_id),
                UNIQUE(schema_id, table_name)
            )
        """)
        
        # Columns table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS columns (
                column_id INTEGER PRIMARY KEY AUTOINCREMENT,
                table_id INTEGER NOT NULL,
                column_name TEXT NOT NULL,
                data_type TEXT NOT NULL,
                nullable BOOLEAN DEFAULT 1,
                description TEXT,
                position INTEGER NOT NULL,
                properties TEXT,
                FOREIGN KEY (table_id) REFERENCES tables(table_id),
                UNIQUE(table_id, column_name)
            )
        """)
        
        # Create indexes for faster lookups
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_schemas_catalog ON schemas(catalog_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tables_schema ON tables(schema_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_columns_table ON columns(table_id)")
        
        self.conn.commit()
    
    def create_catalog(self, name: str, description: str = None, 
                      owner: str = "system", properties: Dict = None) -> int:
        """Create a new catalog"""
        cursor = self.conn.cursor()
        now = datetime.now().isoformat()
        
        cursor.execute("""
            INSERT OR IGNORE INTO catalogs (catalog_name, description, owner, created_at, updated_at, properties)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (name, description, owner, now, now, json.dumps(properties or {})))
        
        self.conn.commit()
        return cursor.lastrowid
    
    def create_schema(self, catalog_name: str, schema_name: str, 
                     location: str = None, description: str = None,
                     owner: str = "system", properties: Dict = None) -> int:
        """Create a new schema in a catalog"""
        cursor = self.conn.cursor()
        
        # Get catalog_id
        cursor.execute("SELECT catalog_id FROM catalogs WHERE catalog_name = ?", (catalog_name,))
        row = cursor.fetchone()
        if not row:
            raise ValueError(f"Catalog '{catalog_name}' not found")
        
        catalog_id = row[0]
        now = datetime.now().isoformat()
        
        cursor.execute("""
            INSERT INTO schemas (catalog_id, schema_name, description, location, owner, created_at, updated_at, properties)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (catalog_id, schema_name, description, location, owner, now, now, json.dumps(properties or {})))
        
        self.conn.commit()
        return cursor.lastrowid
    
    def register_table(self, catalog_name: str, schema_name: str, table_name: str,
                      table_type: str, location: str, format: str = "json",
                      description: str = None, owner: str = "system",
                      row_count: int = None, size_bytes: int = None,
                      properties: Dict = None) -> int:
        """Register a new table in the catalog"""
        cursor = self.conn.cursor()
        
        # Get schema_id
        cursor.execute("""
            SELECT s.schema_id FROM schemas s
            JOIN catalogs c ON s.catalog_id = c.catalog_id
            WHERE c.catalog_name = ? AND s.schema_name = ?
        """, (catalog_name, schema_name))
        
        row = cursor.fetchone()
        if not row:
            raise ValueError(f"Schema '{catalog_name}.{schema_name}' not found")
        
        schema_id = row[0]
        now = datetime.now().isoformat()
        
        cursor.execute("""
            INSERT INTO tables (schema_id, table_name, table_type, description, location, format, 
                              owner, created_at, updated_at, row_count, size_bytes, properties)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (schema_id, table_name, table_type, description, location, format,
              owner, now, now, row_count, size_bytes, json.dumps(properties or {})))
        
        self.conn.commit()
        return cursor.lastrowid
    
    def register_columns(self, catalog_name: str, schema_name: str, table_name: str,
                        columns: List[Dict[str, Any]]):
        """Register columns for a table"""
        cursor = self.conn.cursor()
        
        # Get table_id
        cursor.execute("""
            SELECT t.table_id FROM tables t
            JOIN schemas s ON t.schema_id = s.schema_id
            JOIN catalogs c ON s.catalog_id = c.catalog_id
            WHERE c.catalog_name = ? AND s.schema_name = ? AND t.table_name = ?
        """, (catalog_name, schema_name, table_name))
        
        row = cursor.fetchone()
        if not row:
            raise ValueError(f"Table '{catalog_name}.{schema_name}.{table_name}' not found")
        
        table_id = row[0]
        
        # Insert columns
        for i, col in enumerate(columns):
            cursor.execute("""
                INSERT INTO columns (table_id, column_name, data_type, nullable, description, position, properties)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (table_id, col['name'], col['type'], col.get('nullable', True),
                  col.get('description'), i, json.dumps(col.get('properties', {}))))
        
        self.conn.commit()
    
    def get_table_metadata(self, catalog_name: str, schema_name: str, table_name: str) -> Optional[Dict]:
        """Get full metadata for a table including columns"""
        cursor = self.conn.cursor()
        
        # Get table metadata
        cursor.execute("""
            SELECT t.*, s.schema_name, c.catalog_name
            FROM tables t
            JOIN schemas s ON t.schema_id = s.schema_id
            JOIN catalogs c ON s.catalog_id = c.catalog_id
            WHERE c.catalog_name = ? AND s.schema_name = ? AND t.table_name = ?
        """, (catalog_name, schema_name, table_name))
        
        row = cursor.fetchone()
        if not row:
            return None
        
        table = dict(row)
        table['properties'] = json.loads(table['properties']) if table.get('properties') else {}
        
        # Get columns
        cursor.execute("""
            SELECT column_name, data_type, nullable, description, position
            FROM columns
            WHERE table_id = ?
            ORDER BY position
        """, (table['table_id'],))
        
        columns = [dict(row) for row in cursor.fetchall()]
        table['columns'] = columns
        
        return table
    
    def list_catalogs(self) -> List[Dict]:
        """List all catalogs"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM catalogs ORDER BY catalog_name")
        return [dict(row) for row in cursor.fetchall()]
    
    def list_schemas(self, catalog_name: str) -> List[Dict]:
        """List all schemas in a catalog"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT s.* FROM schemas s
            JOIN catalogs c ON s.catalog_id = c.catalog_id
            WHERE c.catalog_name = ?
            ORDER BY s.schema_name
        """, (catalog_name,))
        return [dict(row) for row in cursor.fetchall()]
    
    def list_tables(self, catalog_name: str, schema_name: str) -> List[Dict]:
        """List all tables in a schema"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT t.* FROM tables t
            JOIN schemas s ON t.schema_id = s.schema_id
            JOIN catalogs c ON s.catalog_id = c.catalog_id
            WHERE c.catalog_name = ? AND s.schema_name = ?
            ORDER BY t.table_name
        """, (catalog_name, schema_name))
        return [dict(row) for row in cursor.fetchall()]
    
    def update_table_stats(self, catalog_name: str, schema_name: str, table_name: str,
                          row_count: int, size_bytes: int):
        """Update table statistics"""
        cursor = self.conn.cursor()
        now = datetime.now().isoformat()
        
        cursor.execute("""
            UPDATE tables
            SET row_count = ?, size_bytes = ?, updated_at = ?
            WHERE table_id IN (
                SELECT t.table_id FROM tables t
                JOIN schemas s ON t.schema_id = s.schema_id
                JOIN catalogs c ON s.catalog_id = c.catalog_id
                WHERE c.catalog_name = ? AND s.schema_name = ? AND t.table_name = ?
            )
        """, (row_count, size_bytes, now, catalog_name, schema_name, table_name))
        
        self.conn.commit()
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
