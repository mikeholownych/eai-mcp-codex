"""Database utilities using SQLite for local persistence."""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from contextlib import contextmanager

from .logging import get_logger

logger = get_logger("database")


class DatabaseManager:
    """Enhanced database manager with utilities for common operations."""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._ensure_directory()
    
    def _ensure_directory(self):
        """Ensure the database directory exists."""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections."""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            # Enable foreign keys
            conn.execute("PRAGMA foreign_keys = ON")
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def execute_script(self, script: str) -> bool:
        """Execute a SQL script."""
        try:
            with self.get_connection() as conn:
                conn.executescript(script)
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Failed to execute script: {e}")
            return False
    
    def execute_query(self, query: str, params: tuple = None) -> List[Dict[str, Any]]:
        """Execute a SELECT query and return results."""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(query, params or ())
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Query failed: {e}")
            return []
    
    def execute_update(self, query: str, params: tuple = None) -> int:
        """Execute an UPDATE/INSERT/DELETE query and return affected rows."""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(query, params or ())
                conn.commit()
                return cursor.rowcount
        except Exception as e:
            logger.error(f"Update failed: {e}")
            return 0
    
    def table_exists(self, table_name: str) -> bool:
        """Check if a table exists."""
        query = "SELECT name FROM sqlite_master WHERE type='table' AND name=?"
        results = self.execute_query(query, (table_name,))
        return len(results) > 0
    
    def get_table_info(self, table_name: str) -> List[Dict[str, Any]]:
        """Get table column information."""
        query = f"PRAGMA table_info({table_name})"
        return self.execute_query(query)
    
    def backup_database(self, backup_path: str) -> bool:
        """Create a backup of the database."""
        try:
            backup_path_obj = Path(backup_path)
            backup_path_obj.parent.mkdir(parents=True, exist_ok=True)
            
            with self.get_connection() as source:
                with sqlite3.connect(backup_path) as backup:
                    source.backup(backup)
            
            logger.info(f"Database backed up to {backup_path}")
            return True
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            return False
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        stats = {}
        
        # Get database size
        try:
            db_path = Path(self.db_path)
            stats["size_bytes"] = db_path.stat().st_size if db_path.exists() else 0
        except:
            stats["size_bytes"] = 0
        
        # Get table information
        tables_query = "SELECT name FROM sqlite_master WHERE type='table'"
        tables = self.execute_query(tables_query)
        stats["table_count"] = len(tables)
        stats["tables"] = {}
        
        for table in tables:
            table_name = table["name"]
            count_query = f"SELECT COUNT(*) as count FROM {table_name}"
            count_result = self.execute_query(count_query)
            stats["tables"][table_name] = count_result[0]["count"] if count_result else 0
        
        return stats


def get_connection(dsn: str) -> sqlite3.Connection:
    """Return a SQLite connection with enhanced configuration."""
    conn = sqlite3.connect(dsn, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")  # Better concurrency
    conn.execute("PRAGMA synchronous = NORMAL")  # Better performance
    return conn


def dict_factory(cursor, row):
    """Row factory that returns dictionaries."""
    return {cursor.description[idx][0]: value for idx, value in enumerate(row)}


def serialize_json_field(value: Any) -> str:
    """Serialize a value to JSON for database storage."""
    if value is None:
        return "{}"
    if isinstance(value, str):
        return value
    return json.dumps(value, default=str)


def deserialize_json_field(value: str) -> Any:
    """Deserialize a JSON field from database."""
    if not value:
        return {}
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return {}


def serialize_datetime(dt: Optional[datetime]) -> Optional[str]:
    """Serialize datetime for database storage."""
    return dt.isoformat() if dt else None


def deserialize_datetime(dt_str: Optional[str]) -> Optional[datetime]:
    """Deserialize datetime from database."""
    if not dt_str:
        return None
    try:
        return datetime.fromisoformat(dt_str)
    except (ValueError, TypeError):
        return None


def build_where_clause(conditions: Dict[str, Any]) -> tuple[str, tuple]:
    """Build WHERE clause from conditions dictionary."""
    if not conditions:
        return "1=1", ()
    
    clauses = []
    params = []
    
    for key, value in conditions.items():
        if value is None:
            clauses.append(f"{key} IS NULL")
        elif isinstance(value, (list, tuple)):
            placeholders = ",".join("?" * len(value))
            clauses.append(f"{key} IN ({placeholders})")
            params.extend(value)
        else:
            clauses.append(f"{key} = ?")
            params.append(value)
    
    return " AND ".join(clauses), tuple(params)


def build_insert_query(table: str, data: Dict[str, Any]) -> tuple[str, tuple]:
    """Build INSERT query from data dictionary."""
    columns = list(data.keys())
    placeholders = ",".join("?" * len(columns))
    column_names = ",".join(columns)
    
    query = f"INSERT INTO {table} ({column_names}) VALUES ({placeholders})"
    params = tuple(data.values())
    
    return query, params


def build_update_query(table: str, data: Dict[str, Any], conditions: Dict[str, Any]) -> tuple[str, tuple]:
    """Build UPDATE query from data and conditions."""
    set_clauses = [f"{key} = ?" for key in data.keys()]
    set_clause = ", ".join(set_clauses)
    
    where_clause, where_params = build_where_clause(conditions)
    
    query = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"
    params = tuple(data.values()) + where_params
    
    return query, params


class DatabaseMigration:
    """Database migration utilities."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.migrations_table = "schema_migrations"
        self._ensure_migrations_table()
    
    def _ensure_migrations_table(self):
        """Create migrations tracking table."""
        script = f"""
            CREATE TABLE IF NOT EXISTS {self.migrations_table} (
                version INTEGER PRIMARY KEY,
                description TEXT NOT NULL,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """
        self.db_manager.execute_script(script)
    
    def get_current_version(self) -> int:
        """Get the current schema version."""
        query = f"SELECT MAX(version) as version FROM {self.migrations_table}"
        result = self.db_manager.execute_query(query)
        return result[0]["version"] if result and result[0]["version"] else 0
    
    def apply_migration(self, version: int, description: str, script: str) -> bool:
        """Apply a database migration."""
        current_version = self.get_current_version()
        
        if version <= current_version:
            logger.info(f"Migration {version} already applied")
            return True
        
        try:
            # Execute migration script
            if not self.db_manager.execute_script(script):
                return False
            
            # Record migration
            insert_query = f"""
                INSERT INTO {self.migrations_table} (version, description)
                VALUES (?, ?)
            """
            self.db_manager.execute_update(insert_query, (version, description))
            
            logger.info(f"Applied migration {version}: {description}")
            return True
            
        except Exception as e:
            logger.error(f"Migration {version} failed: {e}")
            return False
    
    def get_migration_history(self) -> List[Dict[str, Any]]:
        """Get migration history."""
        query = f"SELECT * FROM {self.migrations_table} ORDER BY version"
        return self.db_manager.execute_query(query)
