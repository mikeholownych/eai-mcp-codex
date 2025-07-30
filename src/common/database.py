import os
import logging
import json
from datetime import datetime, timezone
from typing import Optional, Any, Dict, List

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
        return dt.replace(tzinfo=timezone.utc) # Assume UTC if no tzinfo
    return dt.astimezone(timezone.utc)

def deserialize_datetime(dt: Optional[datetime]) -> Optional[datetime]:
    if dt is None:
        return None
    # Ensure datetime is timezone-aware and in UTC
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc) # Assume UTC if no tzinfo
    return dt.astimezone(timezone.utc)

class DatabaseManager:
    def __init__(self, db_name: str):
        self.db_name = db_name
        self.dsn = self._get_dsn()
        self._pool: Optional[Any] = None # Use Any for _pool type hint

    def _get_dsn(self) -> str:
        if os.getenv("TESTING_MODE") == "true":
            logger.info(f"Using dummy DSN for in-memory testing for {self.db_name}")
            return "sqlite:///:memory:" # Dummy DSN
        
        user = os.getenv(f"{self.db_name.upper()}_DB_USER", "mcp_user")
        password = os.getenv(f"{self.db_name.upper()}_DB_PASSWORD", "mcp_password")
        host = os.getenv(f"{self.db_name.upper()}_DB_HOST", "localhost")
        port = os.getenv(f"{self.db_name.upper()}_DB_PORT", "5432")
        db = os.getenv(f"{self.db_name.upper()}_DB_NAME", self.db_name)
        return f"postgresql://{user}:{password}@{host}:{port}/{db}"

    async def connect(self):
        if os.getenv("TESTING_MODE") == "true":
            logger.info("Mocking DB connection in testing mode.")
            self._pool = MockAsyncpgPool() # Assign a mock object
            return

        if self._pool is None:
            try:
                self._pool = await asyncpg.create_pool(self.dsn)
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

    async def fetch(self, query: str, *args):
        if os.getenv("TESTING_MODE") == "true":
            logger.info(f"Mock DB fetch: {query}")
            # Return mock data for testing
            if "SELECT * FROM plans" in query:
                return []
            return []

        if self._pool is None:
            logger.error("Database pool not initialized. Call connect() first.")
            raise Exception("Database pool not initialized. Call connect() first.")
        async with self._pool.acquire() as connection:
            return await connection.fetch(query, *args)

    async def execute(self, query: str, *args):
        if os.getenv("TESTING_MODE") == "true":
            logger.info(f"Mock DB execute: {query}")
            return "MOCK_COMMAND_OK"

        if self._pool is None:
            logger.error("Database pool not initialized. Call connect() first.")
            raise Exception("Database pool not initialized. Call connect() first.")
        async with self._pool.acquire() as connection:
            return await connection.execute(query, *args)

    async def fetchrow(self, query: str, *args):
        if os.getenv("TESTING_MODE") == "true":
            logger.info(f"Mock DB fetchrow: {query}")
            return None

        if self._pool is None:
            logger.error("Database pool not initialized. Call connect() first.")
            raise Exception("Database pool not initialized. Call connect() first.")
        async with self._pool.acquire() as connection:
            return await connection.fetchrow(query, *args)

    async def execute_update(self, query: str, *args):
        if os.getenv("TESTING_MODE") == "true":
            logger.info(f"Mock DB execute_update: {query}")
            return 1 # Simulate one row affected

        if self._pool is None:
            logger.error("Database pool not initialized. Call connect() first.")
            raise Exception("Database pool not initialized. Call connect() first.")
        async with self._pool.acquire() as connection:
            return await connection.execute(query, *args)

    async def execute_script(self, script: str):
        if os.getenv("TESTING_MODE") == "true":
            logger.info(f"Mock DB execute_script: {script[:50]}...")
            return "MOCK_SCRIPT_OK"

        if self._pool is None:
            logger.error("Database pool not initialized. Call connect() first.")
            raise Exception("Database pool not initialized. Call connect() first.")
        async with self._pool.acquire() as connection:
            return await connection.execute(script)

    async def execute_query(self, query: str, *args) -> List[Dict[str, Any]]:
        if os.getenv("TESTING_MODE") == "true":
            logger.info(f"Mock DB execute_query: {query}")
            # Return mock data for specific queries if needed
            if "SELECT * FROM plans" in query:
                return []
            return []

        if self._pool is None:
            logger.error("Database pool not initialized. Call connect() first.")
            raise Exception("Database pool not initialized. Call connect() first.")
        async with self._pool.acquire() as connection:
            return await connection.fetch(query, *args)

# Mock class for asyncpg.Pool when TESTING_MODE is true
class MockAsyncpgPool:
    async def acquire(self):
        return MockAsyncpgConnection()

    async def close(self):
        pass

class MockAsyncpgConnection:
    async def fetch(self, query: str, *args):
        return []

    async def execute(self, query: str, *args):
        return "MOCK_COMMAND_OK"

    async def fetchrow(self, query: str, *args):
        return None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass
