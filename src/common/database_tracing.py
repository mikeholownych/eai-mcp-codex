"""
Database tracing utilities for MCP services.
Provides trace correlation for database operations and query execution.
"""

import logging
from typing import Dict, Any, Optional, List
from contextlib import asynccontextmanager
import time
import hashlib
import re

from opentelemetry.trace import (
    Span, 
    SpanKind, 
    Status, 
    StatusCode
)
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

import asyncpg
import redis.asyncio as redis

from .tracing import get_tracing_config
from .trace_propagation import TracePropagationUtils

logger = logging.getLogger(__name__)

# Global propagator instance
_trace_context_propagator = TraceContextTextMapPropagator()


class DatabaseTracing:
    """Tracing utilities for database operations."""
    
    def __init__(self):
        self.tracer = get_tracing_config().get_tracer()
        self.propagator = _trace_context_propagator
        self.propagation_utils = TracePropagationUtils()
        self._query_sanitization_patterns = [
            (r'\bpassword\s*=\s*[^\s]+', 'password=***'),
            (r'\btoken\s*=\s*[^\s]+', 'token=***'),
            (r'\bapi[_-]?key\s*=\s*[^\s]+', 'api_key=***'),
            (r'\bsecret\s*=\s*[^\s]+', 'secret=***'),
            (r'\bauthorization\s*=\s*[^\s]+', 'authorization=***'),
            (r'\bauth\s*=\s*[^\s]+', 'auth=***'),
            (r'\bcredit_card\s*=\s*[^\s]+', 'credit_card=***'),
            (r'\bssn\s*=\s*[^\s]+', 'ssn=***'),
            (r'\bemail\s*=\s*[^\s]+', 'email=***'),
        ]
    
    @asynccontextmanager
    async def trace_database_query(self, query: str, operation: str = "query", 
                                 database_name: str = "unknown", 
                                 table_name: str = None,
                                 parameters: Dict[str, Any] = None):
        """Trace database query execution."""
        span_name = f"database.{operation}"
        
        # Sanitize query for logging
        sanitized_query = self._sanitize_query(query)
        query_hash = self._hash_query(sanitized_query)
        
        attributes = {
            "db.system": "postgresql",
            "db.name": database_name,
            "db.operation": operation,
            "db.statement": sanitized_query,
            "db.statement_hash": query_hash,
            "db.statement_type": self._get_query_type(query)
        }
        
        if table_name:
            attributes["db.sql.table"] = table_name
        
        if parameters:
            attributes["db.parameters_count"] = len(parameters)
        
        with self.tracer.start_as_current_span(span_name, kind=SpanKind.CLIENT, attributes=attributes) as span:
            start_time = time.time()
            try:
                yield span
                duration = time.time() - start_time
                span.set_attribute("db.duration_ms", duration * 1000)
                span.set_status(Status(StatusCode.OK))
            except Exception as e:
                duration = time.time() - start_time
                span.set_attribute("db.duration_ms", duration * 1000)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                raise
    
    @asynccontextmanager
    async def trace_database_transaction(self, transaction_id: str, 
                                       database_name: str = "unknown",
                                       operations: List[str] = None):
        """Trace database transaction."""
        span_name = "database.transaction"
        attributes = {
            "db.system": "postgresql",
            "db.name": database_name,
            "db.transaction_id": transaction_id
        }
        
        if operations:
            attributes["db.transaction_operations"] = ",".join(operations)
        
        with self.tracer.start_as_current_span(span_name, attributes=attributes) as span:
            start_time = time.time()
            try:
                yield span
                duration = time.time() - start_time
                span.set_attribute("db.duration_ms", duration * 1000)
                span.set_status(Status(StatusCode.OK))
            except Exception as e:
                duration = time.time() - start_time
                span.set_attribute("db.duration_ms", duration * 1000)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                raise
    
    @asynccontextmanager
    async def trace_database_connection(self, database_name: str, 
                                      connection_id: str = None,
                                      host: str = None, port: int = None):
        """Trace database connection."""
        span_name = "database.connection"
        attributes = {
            "db.system": "postgresql",
            "db.name": database_name
        }
        
        if connection_id:
            attributes["db.connection_id"] = connection_id
        if host:
            attributes["net.peer.name"] = host
        if port:
            attributes["net.peer.port"] = port
        
        with self.tracer.start_as_current_span(span_name, attributes=attributes) as span:
            start_time = time.time()
            try:
                yield span
                duration = time.time() - start_time
                span.set_attribute("db.duration_ms", duration * 1000)
                span.set_status(Status(StatusCode.OK))
            except Exception as e:
                duration = time.time() - start_time
                span.set_attribute("db.duration_ms", duration * 1000)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                raise
    
    @asynccontextmanager
    async def trace_redis_operation(self, operation: str, key: str = None, 
                                 database_index: int = 0):
        """Trace Redis operations."""
        span_name = f"redis.{operation}"
        attributes = {
            "db.system": "redis",
            "redis.operation": operation,
            "redis.database_index": database_index
        }
        
        if key:
            attributes["redis.key"] = self._sanitize_key(key)
        
        with self.tracer.start_as_current_span(span_name, kind=SpanKind.CLIENT, attributes=attributes) as span:
            start_time = time.time()
            try:
                yield span
                duration = time.time() - start_time
                span.set_attribute("db.duration_ms", duration * 1000)
                span.set_status(Status(StatusCode.OK))
            except Exception as e:
                duration = time.time() - start_time
                span.set_attribute("db.duration_ms", duration * 1000)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                raise
    
    def _sanitize_query(self, query: str) -> str:
        """Sanitize query to remove sensitive information."""
        sanitized = query
        for pattern, replacement in self._query_sanitization_patterns:
            sanitized = re.sub(pattern, replacement, sanitized, flags=re.IGNORECASE)
        return sanitized
    
    def _sanitize_key(self, key: str) -> str:
        """Sanitize Redis key to remove sensitive information."""
        if any(sensitive in key.lower() for sensitive in ['password', 'token', 'secret', 'auth']):
            return "***"
        return key
    
    def _hash_query(self, query: str) -> str:
        """Generate hash for query normalization."""
        return hashlib.md5(query.encode('utf-8')).hexdigest()
    
    def _get_query_type(self, query: str) -> str:
        """Extract query type from SQL statement."""
        query_upper = query.strip().upper()
        if query_upper.startswith('SELECT'):
            return 'SELECT'
        elif query_upper.startswith('INSERT'):
            return 'INSERT'
        elif query_upper.startswith('UPDATE'):
            return 'UPDATE'
        elif query_upper.startswith('DELETE'):
            return 'DELETE'
        elif query_upper.startswith('CREATE'):
            return 'CREATE'
        elif query_upper.startswith('ALTER'):
            return 'ALTER'
        elif query_upper.startswith('DROP'):
            return 'DROP'
        elif query_upper.startswith('BEGIN') or query_upper.startswith('START'):
            return 'BEGIN'
        elif query_upper.startswith('COMMIT'):
            return 'COMMIT'
        elif query_upper.startswith('ROLLBACK'):
            return 'ROLLBACK'
        else:
            return 'OTHER'
    
    def add_database_attributes_to_span(self, span: Span, connection_id: str = None,
                                      transaction_id: str = None, 
                                      rows_affected: int = None,
                                      query_plan: str = None):
        """Add database operation attributes to span."""
        if connection_id:
            span.set_attribute("db.connection_id", connection_id)
        if transaction_id:
            span.set_attribute("db.transaction_id", transaction_id)
        if rows_affected is not None:
            span.set_attribute("db.rows_affected", rows_affected)
        if query_plan:
            span.set_attribute("db.query_plan", query_plan)
    
    def add_performance_attributes_to_span(self, span: Span, execution_time: float,
                                         cache_hit: bool = None, index_used: bool = None):
        """Add performance attributes to span."""
        span.set_attribute("db.execution_time_ms", execution_time * 1000)
        if cache_hit is not None:
            span.set_attribute("db.cache_hit", cache_hit)
        if index_used is not None:
            span.set_attribute("db.index_used", index_used)


class TracedAsyncPGConnection:
    """Traced asyncpg connection wrapper."""
    
    def __init__(self, connection: asyncpg.Connection, 
                 database_tracing: DatabaseTracing):
        self.connection = connection
        self.database_tracing = database_tracing
        self.connection_id = id(connection)
    
    async def execute(self, query: str, *args, timeout: float = None):
        """Execute a query with tracing."""
        table_name = self._extract_table_name(query)
        parameters = args[0] if args and isinstance(args[0], dict) else None
        
        async with self.database_tracing.trace_database_query(
            query, "execute", self.connection.get_settings().database, 
            table_name, parameters
        ) as span:
            try:
                result = await self.connection.execute(query, *args, timeout=timeout)
                
                # Add performance attributes
                self.database_tracing.add_performance_attributes_to_span(
                    span, getattr(result, 'duration', 0) / 1000 if hasattr(result, 'duration') else 0
                )
                
                return result
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                raise
    
    async def fetch(self, query: str, *args, timeout: float = None):
        """Fetch records with tracing."""
        table_name = self._extract_table_name(query)
        parameters = args[0] if args and isinstance(args[0], dict) else None
        
        async with self.database_tracing.trace_database_query(
            query, "fetch", self.connection.get_settings().database, 
            table_name, parameters
        ) as span:
            try:
                result = await self.connection.fetch(query, *args, timeout=timeout)
                
                # Add performance attributes
                self.database_tracing.add_performance_attributes_to_span(
                    span, getattr(result, 'duration', 0) / 1000 if hasattr(result, 'duration') else 0
                )
                
                # Add row count
                if result:
                    span.set_attribute("db.rows_affected", len(result))
                
                return result
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                raise
    
    async def fetchrow(self, query: str, *args, timeout: float = None):
        """Fetch a single row with tracing."""
        table_name = self._extract_table_name(query)
        parameters = args[0] if args and isinstance(args[0], dict) else None
        
        async with self.database_tracing.trace_database_query(
            query, "fetchrow", self.connection.get_settings().database, 
            table_name, parameters
        ) as span:
            try:
                result = await self.connection.fetchrow(query, *args, timeout=timeout)
                
                # Add performance attributes
                self.database_tracing.add_performance_attributes_to_span(
                    span, getattr(result, 'duration', 0) / 1000 if hasattr(result, 'duration') else 0
                )
                
                return result
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                raise
    
    async def fetchval(self, query: str, *args, column: int = 0, timeout: float = None):
        """Fetch a single value with tracing."""
        table_name = self._extract_table_name(query)
        parameters = args[0] if args and isinstance(args[0], dict) else None
        
        async with self.database_tracing.trace_database_query(
            query, "fetchval", self.connection.get_settings().database, 
            table_name, parameters
        ) as span:
            try:
                result = await self.connection.fetchval(query, *args, column=column, timeout=timeout)
                
                # Add performance attributes
                self.database_tracing.add_performance_attributes_to_span(
                    span, getattr(result, 'duration', 0) / 1000 if hasattr(result, 'duration') else 0
                )
                
                return result
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                raise
    
    async def transaction(self, isolation: str = None, readonly: bool = None, 
                         deferrable: bool = None):
        """Create a transaction with tracing."""
        transaction_id = f"txn_{int(time.time() * 1000)}_{self.connection_id}"
        
        async with self.database_tracing.trace_database_transaction(
            transaction_id, self.connection.get_settings().database
        ) as span:
            try:
                async with self.connection.transaction(isolation, readonly, deferrable) as transaction:
                    # Add transaction attributes to span
                    self.database_tracing.add_database_attributes_to_span(
                        span, transaction_id=transaction_id
                    )
                    yield TracedAsyncPGTransaction(transaction, self.database_tracing, transaction_id)
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                raise
    
    def _extract_table_name(self, query: str) -> Optional[str]:
        """Extract table name from query."""
        # Simple extraction - in production, you might want a more sophisticated parser
        match = re.search(r'\bFROM\s+(\w+)', query, re.IGNORECASE)
        if match:
            return match.group(1)
        
        match = re.search(r'\bINSERT\s+INTO\s+(\w+)', query, re.IGNORECASE)
        if match:
            return match.group(1)
        
        match = re.search(r'\bUPDATE\s+(\w+)', query, re.IGNORECASE)
        if match:
            return match.group(1)
        
        return None


class TracedAsyncPGTransaction:
    """Traced asyncpg transaction wrapper."""
    
    def __init__(self, transaction: asyncpg.transaction.Transaction, 
                 database_tracing: DatabaseTracing, transaction_id: str):
        self.transaction = transaction
        self.database_tracing = database_tracing
        self.transaction_id = transaction_id
        self.operations = []
    
    async def execute(self, query: str, *args, timeout: float = None):
        """Execute a query within the transaction."""
        operation = "execute"
        self.operations.append(operation)
        
        table_name = self._extract_table_name(query)
        parameters = args[0] if args and isinstance(args[0], dict) else None
        
        async with self.database_tracing.trace_database_query(
            query, operation, self.transaction.connection.get_settings().database, 
            table_name, parameters
        ) as span:
            # Add transaction correlation
            self.database_tracing.add_database_attributes_to_span(
                span, transaction_id=self.transaction_id
            )
            
            try:
                result = await self.transaction.execute(query, *args, timeout=timeout)
                
                # Add performance attributes
                self.database_tracing.add_performance_attributes_to_span(
                    span, getattr(result, 'duration', 0) / 1000 if hasattr(result, 'duration') else 0
                )
                
                return result
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                raise
    
    async def fetch(self, query: str, *args, timeout: float = None):
        """Fetch records within the transaction."""
        operation = "fetch"
        self.operations.append(operation)
        
        table_name = self._extract_table_name(query)
        parameters = args[0] if args and isinstance(args[0], dict) else None
        
        async with self.database_tracing.trace_database_query(
            query, operation, self.transaction.connection.get_settings().database, 
            table_name, parameters
        ) as span:
            # Add transaction correlation
            self.database_tracing.add_database_attributes_to_span(
                span, transaction_id=self.transaction_id
            )
            
            try:
                result = await self.transaction.fetch(query, *args, timeout=timeout)
                
                # Add performance attributes
                self.database_tracing.add_performance_attributes_to_span(
                    span, getattr(result, 'duration', 0) / 1000 if hasattr(result, 'duration') else 0
                )
                
                # Add row count
                if result:
                    span.set_attribute("db.rows_affected", len(result))
                
                return result
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                raise
    
    async def commit(self):
        """Commit the transaction."""
        operation = "commit"
        self.operations.append(operation)
        
        async with self.database_tracing.trace_database_transaction(
            self.transaction_id, self.transaction.connection.get_settings().database, 
            self.operations
        ) as span:
            try:
                await self.transaction.commit()
                span.set_status(Status(StatusCode.OK))
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                raise
    
    async def rollback(self):
        """Rollback the transaction."""
        operation = "rollback"
        self.operations.append(operation)
        
        async with self.database_tracing.trace_database_transaction(
            self.transaction_id, self.transaction.connection.get_settings().database, 
            self.operations
        ) as span:
            try:
                await self.transaction.rollback()
                span.set_status(Status(StatusCode.OK))
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                raise
    
    def _extract_table_name(self, query: str) -> Optional[str]:
        """Extract table name from query."""
        match = re.search(r'\bFROM\s+(\w+)', query, re.IGNORECASE)
        if match:
            return match.group(1)
        
        match = re.search(r'\bINSERT\s+INTO\s+(\w+)', query, re.IGNORECASE)
        if match:
            return match.group(1)
        
        match = re.search(r'\bUPDATE\s+(\w+)', query, re.IGNORECASE)
        if match:
            return match.group(1)
        
        return None


class TracedRedisConnection:
    """Traced Redis connection wrapper."""
    
    def __init__(self, connection: redis.Redis, database_tracing: DatabaseTracing):
        self.connection = connection
        self.database_tracing = database_tracing
    
    async def get(self, key: str):
        """Get a value from Redis with tracing."""
        async with self.database_tracing.trace_redis_operation("get", key) as span:
            try:
                result = await self.connection.get(key)
                span.set_attribute("redis.key_found", result is not None)
                return result
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                raise
    
    async def set(self, key: str, value: str, ex: int = None):
        """Set a value in Redis with tracing."""
        async with self.database_tracing.trace_redis_operation("set", key) as span:
            try:
                result = await self.connection.set(key, value, ex=ex)
                span.set_attribute("redis.operation_success", result)
                return result
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                raise
    
    async def delete(self, key: str):
        """Delete a key from Redis with tracing."""
        async with self.database_tracing.trace_redis_operation("delete", key) as span:
            try:
                result = await self.connection.delete(key)
                span.set_attribute("redis.keys_deleted", result)
                return result
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                raise
    
    async def exists(self, key: str):
        """Check if a key exists in Redis with tracing."""
        async with self.database_tracing.trace_redis_operation("exists", key) as span:
            try:
                result = await self.connection.exists(key)
                span.set_attribute("redis.key_exists", bool(result))
                return result
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                raise


# Decorators for database operations
def trace_database_query(operation: str = "query", table_name: str = None):
    """Decorator to trace database queries."""
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            database_tracing = DatabaseTracing()
            
            # Extract query from kwargs or args
            query = kwargs.get('query') or (args[0] if args else "")
            
            async with database_tracing.trace_database_query(
                query, operation, table_name=table_name
            ) as span:
                try:
                    result = await func(*args, **kwargs)
                    span.set_status(Status(StatusCode.OK))
                    return result
                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    raise
        
        if hasattr(func, '__call__') and hasattr(func, '__code__') and func.__code__.co_flags & 0x80:
            return async_wrapper
        return func
    
    return decorator


def trace_database_transaction():
    """Decorator to trace database transactions."""
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            database_tracing = DatabaseTracing()
            transaction_id = f"txn_{int(time.time() * 1000)}"
            
            async with database_tracing.trace_database_transaction(transaction_id) as span:
                try:
                    result = await func(*args, **kwargs)
                    span.set_status(Status(StatusCode.OK))
                    return result
                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    raise
        
        if hasattr(func, '__call__') and hasattr(func, '__code__') and func.__code__.co_flags & 0x80:
            return async_wrapper
        return func
    
    return decorator


def trace_redis_operation(operation: str):
    """Decorator to trace Redis operations."""
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            database_tracing = DatabaseTracing()
            
            # Extract key from kwargs or args
            key = kwargs.get('key') or (args[0] if args else None)
            
            async with database_tracing.trace_redis_operation(operation, key) as span:
                try:
                    result = await func(*args, **kwargs)
                    span.set_status(Status(StatusCode.OK))
                    return result
                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    raise
        
        if hasattr(func, '__call__') and hasattr(func, '__code__') and func.__code__.co_flags & 0x80:
            return async_wrapper
        return func
    
    return decorator


# Global instance
database_tracing = DatabaseTracing()


def get_database_tracing() -> DatabaseTracing:
    """Get the global database tracing instance."""
    return database_tracing


def create_traced_asyncpg_connection(connection: asyncpg.Connection):
    """Create a traced asyncpg connection."""
    return TracedAsyncPGConnection(connection, database_tracing)


def create_traced_redis_connection(connection: redis.Redis):
    """Create a traced Redis connection."""
    return TracedRedisConnection(connection, database_tracing)