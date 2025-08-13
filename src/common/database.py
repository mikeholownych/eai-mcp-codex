import os
import logging
import json
import asyncio
from datetime import datetime, timezone
from typing import Optional, Any, Dict, List
from contextlib import asynccontextmanager

__all__ = ["DatabaseManager", "DatabaseMigration", "get_postgres_connection"]

logger = logging.getLogger(__name__)

# Conditionally import asyncpg
if os.getenv("TESTING_MODE") != "true":
    import asyncpg


# Utility functions for serialization/deserialization
def serialize_json_field(data: Any) -> str:
    return json.dumps(data) if data is not None else "{}"


def deserialize_json_field(data: Any) -> Dict[str, Any]:
    if isinstance(data, dict):
        return data
    return json.loads(data) if data else {}


def serialize_datetime(dt: Optional[datetime]) -> Optional[datetime]:
    if dt is None:
        return None
    # Ensure datetime is timezone-aware and in UTC
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)  # Assume UTC if no tzinfo
    return dt.astimezone(timezone.utc)


def deserialize_datetime(dt: Optional[datetime]) -> Optional[datetime]:
    if dt is None:
        return None
    # Ensure datetime is timezone-aware and in UTC
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)  # Assume UTC if no tzinfo
    return dt.astimezone(timezone.utc)


class DatabaseManager:
    def __init__(self, db_name: str):
        logger.info(f"DatabaseManager initialized with db_name: {db_name}")
        
        # For workflow orchestrator, always use environment variables
        if db_name.startswith('postgresql://'):
            logger.info("DSN detected, extracting database name and using environment variables")
            # Extract database name from DSN
            import urllib.parse as urlparse
            parsed = urlparse.urlparse(db_name)
            self.db_name = parsed.path.lstrip('/')
            if not self.db_name:
                self.db_name = "workflow_orchestrator"
        else:
            self.db_name = db_name
            
        self.dsn = self._get_dsn()
        self._pool: Optional[Any] = None  # Use Any for _pool type hint

    def _get_dsn(self) -> str:
        if os.getenv("TESTING_MODE") == "true":
            logger.info(f"Using dummy DSN for in-memory testing for {self.db_name}")
            return "sqlite:///:memory:"  # Dummy DSN

        # Try environment variables with DB_NAME prefix first (for workflow orchestrator)
        user = os.getenv(f"{self.db_name.upper()}_DB_USER")
        password = os.getenv(f"{self.db_name.upper()}_DB_PASSWORD")
        host = os.getenv(f"{self.db_name.upper()}_DB_HOST")
        port = os.getenv(f"{self.db_name.upper()}_DB_PORT")
        db = os.getenv(f"{self.db_name.upper()}_DB_NAME")
        
        # If not found, try generic MCP variables (for other services)
        if not user:
            user = os.getenv("MCP_DB_USER", "mcp_user")
        if not password:
            password = os.getenv("MCP_DB_PASSWORD", "mcp_password")
        if not host:
            host = os.getenv("MCP_DB_HOST", "postgres")
        if not port:
            port = os.getenv("MCP_DB_PORT", "5432")
        if not db:
            db = self.db_name
        
        # Log the values being used
        logger.info(f"Database connection for {self.db_name}:")
        logger.info(f"  User: {user}")
        logger.info(f"  Host: {host}")
        logger.info(f"  Port: {port}")
        logger.info(f"  Database: {db}")
        
        dsn = f"postgresql://{user}:{password}@{host}:{port}/{db}"
        logger.info(f"  DSN: {dsn}")
        
        return dsn

    async def connect(self):
        if os.getenv("TESTING_MODE") == "true":
            logger.info("Mocking DB connection in testing mode.")
            self._pool = MockAsyncpgPool()  # Assign a mock object
            return

        if self._pool is None:
            try:
                # Parse the DSN to get connection parameters
                import urllib.parse as urlparse
                parsed = urlparse.urlparse(self.dsn)
                
                # Create connection pool with explicit server settings
                self._pool = await asyncpg.create_pool(
                    host=parsed.hostname,
                    port=parsed.port,
                    user=parsed.username,
                    password=parsed.password,
                    database=parsed.path.lstrip('/'),
                    timeout=10,
                    command_timeout=10,
                    min_size=1,
                    max_size=10
                )
                logger.info(f"Successfully connected to database: {self.db_name}")
            except Exception as e:
                logger.error(f"Failed to create PostgreSQL connection pool: {e}")
                raise

    async def disconnect(self):
        if os.getenv("TESTING_MODE") == "true":
            logger.info("Mocking DB disconnection in testing mode.")
            self._pool = None
            return

        if self._pool:
            logger.info(f"Disconnecting from database: {self.db_name}")
            await self._pool.close()
            self._pool = None
            logger.info("PostgreSQL connection pool closed.")

    @asynccontextmanager
    async def get_connection(self):
        """Asynchronous context manager for database connections from the pool."""
        if self._pool is None:
            # In testing mode, auto-provision a mock pool to avoid boilerplate connects
            if os.getenv("TESTING_MODE") == "true":
                logger.info("Auto-initializing mock DB pool in testing mode.")
                self._pool = MockAsyncpgPool()
            else:
                raise ConnectionError(
                    "Database pool not initialized. Call connect() first."
                )
        conn = None
        try:
            conn = await self._pool.acquire()
            yield conn
        except Exception as e:
            logger.error(
                f"Database error during connection acquisition or operation: {e}"
            )
            raise
        finally:
            if conn:
                await self._pool.release(conn)

    async def execute_script(self, script: str) -> bool:
        """Execute a SQL script."""
        try:
            async with self.get_connection() as conn:
                await conn.execute(script)
                return True
        except Exception as e:
            logger.error(f"Failed to execute script: {e}")
            return False

    async def execute_query(
        self, query: str, params: tuple = ()
    ) -> List[Dict[str, Any]]:
        """Execute a SELECT query and return results as a list of dictionaries."""
        try:
            async with self.get_connection() as conn:
                records = await conn.fetch(query, *params)
                # If MockAsyncpgConnection returns list[dict], pass through
                if records and isinstance(records[0], dict):
                    return records  # already list of dicts
                return [dict(r) for r in records]
        except Exception as e:
            logger.error(f"Query failed: {e}")
            return []

    async def execute_update(self, query: str, params: tuple = ()) -> int:
        """Execute an INSERT/UPDATE/DELETE query and return affected rows count."""
        try:
            async with self.get_connection() as conn:
                status = await conn.execute(query, *params)
                # asyncpg.execute returns command status, e.g., 'INSERT 0 1'
                # We need to parse the row count from it.
                parts = status.split(" ")
                if len(parts) > 2 and parts[0] in ("INSERT", "UPDATE", "DELETE"):
                    return int(parts[-1])
                return 0  # Or raise an error if expected a row count
        except Exception as e:
            logger.error(f"Update failed: {e}")
            return 0

    async def table_exists(self, table_name: str) -> bool:
        """Check if a table exists."""
        query = """
            SELECT EXISTS (
                SELECT 1
                FROM information_schema.tables
                WHERE table_name = $1
            );
        """
        try:
            async with self.get_connection() as conn:
                exists = await conn.fetchval(query, table_name)
                return exists
        except Exception as e:
            logger.error(f"Failed to check table existence: {e}")
            return False

    async def get_table_info(self, table_name: str) -> List[Dict[str, Any]]:
        """Get table column information."""
        query = """
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_name = $1
            ORDER BY ordinal_position;
        """
        try:
            async with self.get_connection() as conn:
                records = await conn.fetch(query, table_name)
                return [dict(r) for r in records]
        except Exception as e:
            logger.error(f"Failed to get table info: {e}")
            return []

    async def backup_database(self, backup_path: str) -> bool:
        """Create a backup of the database (simplified - typically uses pg_dump)."""
        logger.warning(
            "Database backup for PostgreSQL typically uses pg_dump. This is a placeholder."
        )
        # This method would ideally integrate with pg_dump or a similar tool.
        # For now, it's a placeholder as direct file copy is not applicable for remote PG.
        return False

    async def get_database_stats(self) -> Dict[str, Any]:
        """Get basic statistics about the connected database."""
        if os.getenv("TESTING_MODE") == "true":
            logger.info("Mocking DB stats in testing mode.")
            return {"size_bytes": 0, "table_count": 0, "tables": {}}

        stats: Dict[str, Any] = {}
        try:
            async with self.get_connection() as conn:
                db_size = await conn.fetchval(
                    "SELECT pg_database_size(current_database());"
                )
                stats["size_bytes"] = db_size

                tables_query = """
                    SELECT relname AS table_name, reltuples AS row_count
                    FROM pg_class
                    WHERE relkind = 'r'
                      AND relnamespace = (
                        SELECT oid FROM pg_namespace WHERE nspname = 'public'
                    );
                """
                table_records = await conn.fetch(tables_query)
                stats["table_count"] = len(table_records)
                stats["tables"] = {
                    r["table_name"]: int(r["row_count"]) for r in table_records
                }
        except Exception as exc:  # pragma: no cover - unexpected DB errors
            logger.error("Failed to get database stats: %s", exc)
        return stats

    async def fetchrow(self, query: str, *args) -> Optional[Dict[str, Any]]:
        """Fetch a single row from the database as a dictionary."""
        if os.getenv("TESTING_MODE") == "true":
            logger.info("Mock DB fetchrow: %s", query)
            return None
        if self._pool is None:
            logger.error("Database pool not initialized. Call connect() first.")
            raise Exception("Database pool not initialized. Call connect() first.")
        async with self._pool.acquire() as connection:
            row = await connection.fetchrow(query, *args)
            return dict(row) if row else None


def get_connection(dsn: str) -> None:
    """Deprecated synchronous connection helper."""
    logger.warning(
        "get_connection is deprecated. Use DatabaseManager.get_connection() instead."
    )
    raise NotImplementedError(
        "Synchronous get_connection is not supported for asyncpg."
    )



def dict_factory(cursor, row):  # Not directly used with asyncpg fetch methods
    logger.warning("dict_factory is not directly used with asyncpg fetch methods.")
    return {cursor.description[idx][0]: value for idx, value in enumerate(row)}


class MockAsyncpgConnection:
    def __init__(self):
        # very lightweight in-memory store keyed by table
        self._tables: Dict[str, list[Dict[str, Any]]] = {}

    async def fetch(self, query: str, *args):
        # Simple matcher for workflow queries in tests
        if query.strip().lower().startswith("select * from workflows where id ="):
            workflow_id = args[0]
            rows = self._tables.get("workflows", [])
            return [r for r in rows if r.get("id") == workflow_id]
        if query.strip().lower().startswith("select * from workflow_steps where workflow_id ="):
            workflow_id = args[0]
            rows = self._tables.get("workflow_steps", [])
            return [r for r in rows if r.get("workflow_id") == workflow_id]
        return []

    async def execute(self, query: str, *args):
        sql = query.strip().lower()
        if sql.startswith("insert into workflows"):
            # Match parameter order used in orchestrator insert ($1..$13)
            row = {
                "id": args[0],
                "name": args[1],
                "description": args[2],
                "status": args[3],
                "execution_mode": args[4],
                "created_by": args[5],
                "created_at": args[6],
                "updated_at": args[7],
                "global_parameters": args[8],
                "success_criteria": args[9],
                "failure_handling": args[10],
                "notifications": args[11],
                "metadata": args[12],
                # Optional fields not provided by insert, default to None
                "priority": None,
                "started_at": None,
                "completed_at": None,
            }
            self._tables.setdefault("workflows", []).append(row)
            return "INSERT 0 1"
        if sql.startswith("insert into workflow_steps"):
            # Match parameter order used in orchestrator insert ($1..$18)
            row = {
                "id": args[0],
                "workflow_id": args[1],
                "name": args[2],
                "description": args[3],
                "step_type": args[4],
                "service_name": args[5],
                "endpoint": args[6],
                "parameters": args[7],
                "expected_output": args[8],
                "timeout_seconds": args[9],
                "retry_count": args[10],
                "max_retries": args[11],
                "status": args[12],
                "order_index": args[13],
                "depends_on": args[14],
                "conditions": args[15],
                "created_at": args[16],
                "metadata": args[17],
                # Fields updated later
                "started_at": None,
                "completed_at": None,
                "result": None,
                "error_message": None,
            }
            self._tables.setdefault("workflow_steps", []).append(row)
            return "INSERT 0 1"
        if sql.startswith("update workflows set"):
            # no-op for tests
            return "UPDATE 0 1"
        if sql.startswith("update workflow_steps set"):
            return "UPDATE 0 1"
        if sql.startswith("insert into workflow_executions"):
            return "INSERT 0 1"
        return "MOCK_COMMAND_OK"

    async def fetchrow(self, query: str, *args):
        rows = await self.fetch(query, *args)
        return rows[0] if rows else None

    async def close(self) -> None:
        return None


class MockAsyncpgPool:
    def __init__(self):
        # Share a single connection so state persists across acquire calls
        self._conn = MockAsyncpgConnection()

    async def acquire(self) -> MockAsyncpgConnection:
        return self._conn

    async def release(self, conn: MockAsyncpgConnection) -> None:
        return None

    async def close(self) -> None:
        return None


async def get_postgres_connection(db_name: str = "mcp") -> "asyncpg.Connection":
    """Create a single Postgres connection for ad-hoc operations."""
    if os.getenv("TESTING_MODE") == "true":
        logger.info("Providing mock Postgres connection in testing mode")
        return MockAsyncpgConnection()

    manager = DatabaseManager(db_name)
    await manager.connect()
    assert manager.dsn is not None  # for mypy
    return await asyncpg.connect(manager.dsn)


def deserialize_datetime_str(dt_str: str | None) -> Optional[datetime]:
    """Deserialize a datetime from ISO format string."""
    if not dt_str:
        return None
    try:
        return datetime.fromisoformat(dt_str)
    except (ValueError, TypeError):
        logger.warning("Failed to deserialize datetime: %s", dt_str)
        return None


def build_where_clause(conditions: Dict[str, Any]) -> tuple[str, tuple]:
    """Build WHERE clause from conditions dictionary for asyncpg ($1, $2 style)."""
    if not conditions:
        return "1=1", ()

    clauses = []
    params = []
    param_idx = 1

    for key, value in conditions.items():
        if value is None:
            clauses.append(f"{key} IS NULL")
        elif isinstance(value, (list, tuple)):
            placeholders = ", ".join(
                [f"${i}" for i in range(param_idx, param_idx + len(value))]
            )
            clauses.append(f"{key} IN ({placeholders})")
            params.extend(value)
            param_idx += len(value)
        else:
            clauses.append(f"{key} = ${param_idx}")
            params.append(value)
            param_idx += 1

    return " AND ".join(clauses), tuple(params)


def build_insert_query(table: str, data: Dict[str, Any]) -> tuple[str, tuple]:
    """Build INSERT query from data dictionary for asyncpg ($1, $2 style)."""
    columns = list(data.keys())
    placeholders = ", ".join([f"${i}" for i in range(1, len(columns) + 1)])
    column_names = ", ".join(columns)

    query = f"INSERT INTO {table} ({column_names}) VALUES ({placeholders})"
    params = tuple(data.values())

    return query, params


def build_update_query(
    table: str, data: Dict[str, Any], conditions: Dict[str, Any]
) -> tuple[str, tuple]:
    """Build UPDATE query from data and conditions for asyncpg ($1, $2 style)."""
    set_clauses = []
    set_params = []
    param_idx = 1

    for key, value in data.items():
        set_clauses.append(f"{key} = ${param_idx}")
        set_params.append(value)
        param_idx += 1

    set_clause = ", ".join(set_clauses)

    where_clause, where_params = build_where_clause(
        conditions
    )  # This will use $1, $2 style internally

    # Need to re-index where_params if they follow set_params
    # A simpler approach for now is to combine params and let asyncpg handle it.
    # However, asyncpg requires positional parameters to be contiguous.
    # So, we need to adjust the where_clause parameters to start after set_params.

    # Rebuild where_clause with adjusted parameter indices
    adjusted_where_clause = where_clause
    if conditions:
        # This is a bit tricky with regex, a more robust way would be to rebuild the clause
        # based on the number of set_params. For simplicity, let's assume simple equality for now.
        # A better approach would be to pass the starting index to build_where_clause.
        # For now, we'll just combine and hope for the best, or simplify the where_clause building.

        # Let's simplify build_where_clause to return clauses and params separately,
        # then combine here.

        # Re-calling build_where_clause to get clauses and params without $ indexing
        where_clauses_no_idx = []
        where_params_combined = []
        for key, value in conditions.items():
            if value is None:
                where_clauses_no_idx.append(f"{key} IS NULL")
            elif isinstance(value, (list, tuple)):
                placeholders = ", ".join(
                    [f"${i}" for i in range(param_idx, param_idx + len(value))]
                )
                where_clauses_no_idx.append(f"{key} IN ({placeholders})")
                where_params_combined.extend(value)
                param_idx += len(value)
            else:
                where_clauses_no_idx.append(f"{key} = ${param_idx}")
                where_params_combined.append(value)
                param_idx += 1

        adjusted_where_clause = " AND ".join(where_clauses_no_idx)
        params = tuple(set_params) + tuple(where_params_combined)

    else:
        adjusted_where_clause = "1=1"
        params = tuple(set_params)

    query = f"UPDATE {table} SET {set_clause} WHERE {adjusted_where_clause}"

    return query, params


class DatabaseMigration:
    """Database migration utilities."""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.migrations_table = "schema_migrations"
        # Ensure migrations table exists (synchronously for init)
        asyncio.run(self._ensure_migrations_table_sync())

    async def _ensure_migrations_table_sync(self):
        """Create migrations tracking table synchronously for initialization."""
        script = f"""
            CREATE TABLE IF NOT EXISTS {self.migrations_table} (
                version INTEGER PRIMARY KEY,
                description TEXT NOT NULL,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """
        # Use a direct connection for this initial setup if pool is not ready
        # Or assume connect() is called before this.
        # For simplicity, let's use execute_script which handles connection.
        await self.db_manager.execute_script(script)

    async def get_current_version(self) -> int:
        """Get the current schema version."""
        query = f"SELECT MAX(version) as version FROM {self.migrations_table}"
        result = await self.db_manager.execute_query(query)
        return result[0]["version"] if result and result[0]["version"] else 0

    async def apply_migration(
        self, version: int, description: str, script: str
    ) -> bool:
        """Apply a database migration."""
        current_version = await self.get_current_version()

        if version <= current_version:
            logger.info(f"Migration {version} already applied")
            return True

        try:
            # Execute migration script
            if not await self.db_manager.execute_script(script):
                return False

            # Record migration
            insert_query = f"""
                INSERT INTO {self.migrations_table} (version, description)
                VALUES ($1, $2)
            """
            await self.db_manager.execute_update(insert_query, (version, description))

            logger.info(f"Applied migration {version}: {description}")
            return True
        except Exception as exc:  # pragma: no cover - unexpected DB errors
            logger.error("Migration %s failed: %s", version, exc)
            return False

    async def __aenter__(self):
        return self

    async def get_migration_history(self) -> List[Dict[str, Any]]:
        """Get migration history."""
        query = f"SELECT * FROM {self.migrations_table} ORDER BY version"
        return await self.db_manager.execute_query(query)
