"""Prometheus metrics utilities with comprehensive monitoring."""

import time
from datetime import datetime
from typing import Dict, Any, Optional
from contextlib import contextmanager
from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry, generate_latest, CONTENT_TYPE_LATEST

from .logging import get_logger

logger = get_logger("metrics")

# Default registry for all metrics
default_registry = CollectorRegistry()

# Service request metrics
REQUEST_COUNTER = Counter(
    "mcp_requests_total",
    "Total service requests",
    ["service", "method", "endpoint", "status"],
    registry=default_registry
)

REQUEST_DURATION = Histogram(
    "mcp_request_duration_seconds",
    "Request duration in seconds",
    ["service", "method", "endpoint"],
    registry=default_registry
)

# Database metrics
DB_QUERY_COUNTER = Counter(
    "mcp_db_queries_total",
    "Total database queries",
    ["service", "operation", "table"],
    registry=default_registry
)

DB_QUERY_DURATION = Histogram(
    "mcp_db_query_duration_seconds",
    "Database query duration in seconds",
    ["service", "operation", "table"],
    registry=default_registry
)

# Business logic metrics
BUSINESS_OPERATION_COUNTER = Counter(
    "mcp_business_operations_total",
    "Total business operations",
    ["service", "operation", "status"],
    registry=default_registry
)

BUSINESS_OPERATION_DURATION = Histogram(
    "mcp_business_operation_duration_seconds",
    "Business operation duration in seconds",
    ["service", "operation"],
    registry=default_registry
)

# System metrics
ACTIVE_CONNECTIONS = Gauge(
    "mcp_active_connections",
    "Number of active connections",
    ["service"],
    registry=default_registry
)

QUEUE_SIZE = Gauge(
    "mcp_queue_size",
    "Size of processing queues",
    ["service", "queue_type"],
    registry=default_registry
)

ERROR_COUNTER = Counter(
    "mcp_errors_total",
    "Total errors",
    ["service", "error_type", "severity"],
    registry=default_registry
)

# Cache metrics
CACHE_OPERATIONS = Counter(
    "mcp_cache_operations_total",
    "Total cache operations",
    ["service", "operation", "result"],
    registry=default_registry
)

CACHE_HIT_RATIO = Gauge(
    "mcp_cache_hit_ratio",
    "Cache hit ratio",
    ["service", "cache_type"],
    registry=default_registry
)


class MetricsCollector:
    """Enhanced metrics collector with context managers and utilities."""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self._cache_stats = {"hits": 0, "misses": 0}
    
    def record_request(self, method: str = "POST", endpoint: str = "/", status: str = "success") -> None:
        """Record a service request."""
        REQUEST_COUNTER.labels(
            service=self.service_name,
            method=method,
            endpoint=endpoint,
            status=status
        ).inc()
    
    @contextmanager
    def time_request(self, method: str = "POST", endpoint: str = "/"):
        """Context manager to time requests."""
        start_time = time.time()
        status = "success"
        try:
            yield
        except Exception as e:
            status = "error"
            self.record_error("request_error", "high", str(e))
            raise
        finally:
            duration = time.time() - start_time
            REQUEST_DURATION.labels(
                service=self.service_name,
                method=method,
                endpoint=endpoint
            ).observe(duration)
            self.record_request(method, endpoint, status)
    
    def record_db_query(self, operation: str, table: str, duration: float = None):
        """Record a database query."""
        DB_QUERY_COUNTER.labels(
            service=self.service_name,
            operation=operation,
            table=table
        ).inc()
        
        if duration is not None:
            DB_QUERY_DURATION.labels(
                service=self.service_name,
                operation=operation,
                table=table
            ).observe(duration)
    
    @contextmanager
    def time_db_query(self, operation: str, table: str):
        """Context manager to time database queries."""
        start_time = time.time()
        try:
            yield
        finally:
            duration = time.time() - start_time
            self.record_db_query(operation, table, duration)
    
    def record_business_operation(self, operation: str, status: str = "success", duration: float = None):
        """Record a business operation."""
        BUSINESS_OPERATION_COUNTER.labels(
            service=self.service_name,
            operation=operation,
            status=status
        ).inc()
        
        if duration is not None:
            BUSINESS_OPERATION_DURATION.labels(
                service=self.service_name,
                operation=operation
            ).observe(duration)
    
    @contextmanager
    def time_business_operation(self, operation: str):
        """Context manager to time business operations."""
        start_time = time.time()
        status = "success"
        try:
            yield
        except Exception as e:
            status = "error"
            self.record_error("business_operation_error", "medium", str(e))
            raise
        finally:
            duration = time.time() - start_time
            self.record_business_operation(operation, status, duration)
    
    def record_error(self, error_type: str, severity: str = "medium", details: str = None):
        """Record an error."""
        ERROR_COUNTER.labels(
            service=self.service_name,
            error_type=error_type,
            severity=severity
        ).inc()
        
        if details:
            logger.error(f"Error recorded - Type: {error_type}, Severity: {severity}, Details: {details}")
    
    def set_active_connections(self, count: int):
        """Set the number of active connections."""
        ACTIVE_CONNECTIONS.labels(service=self.service_name).set(count)
    
    def set_queue_size(self, queue_type: str, size: int):
        """Set the size of a processing queue."""
        QUEUE_SIZE.labels(service=self.service_name, queue_type=queue_type).set(size)
    
    def record_cache_operation(self, operation: str, result: str):
        """Record a cache operation."""
        CACHE_OPERATIONS.labels(
            service=self.service_name,
            operation=operation,
            result=result
        ).inc()
        
        # Update internal cache stats for hit ratio calculation
        if operation == "get":
            if result == "hit":
                self._cache_stats["hits"] += 1
            elif result == "miss":
                self._cache_stats["misses"] += 1
            
            # Update hit ratio
            total = self._cache_stats["hits"] + self._cache_stats["misses"]
            if total > 0:
                hit_ratio = self._cache_stats["hits"] / total
                CACHE_HIT_RATIO.labels(
                    service=self.service_name,
                    cache_type="default"
                ).set(hit_ratio)
    
    def get_service_stats(self) -> Dict[str, Any]:
        """Get service-specific statistics."""
        return {
            "service": self.service_name,
            "cache_stats": self._cache_stats.copy(),
            "timestamp": datetime.utcnow().isoformat()
        }


# Global service metrics collectors
_service_collectors: Dict[str, MetricsCollector] = {}


def get_metrics_collector(service_name: str) -> MetricsCollector:
    """Get or create a metrics collector for a service."""
    if service_name not in _service_collectors:
        _service_collectors[service_name] = MetricsCollector(service_name)
    return _service_collectors[service_name]


def record_request(service: str, method: str = "POST", endpoint: str = "/", status: str = "success") -> None:
    """Record a service request (legacy compatibility)."""
    collector = get_metrics_collector(service)
    collector.record_request(method, endpoint, status)


def get_metrics_output(registry: CollectorRegistry = None) -> str:
    """Get Prometheus metrics output."""
    if registry is None:
        registry = default_registry
    return generate_latest(registry).decode('utf-8')


def get_metrics_content_type() -> str:
    """Get the content type for Prometheus metrics."""
    return CONTENT_TYPE_LATEST


class PerformanceMonitor:
    """Performance monitoring utilities."""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.collector = get_metrics_collector(service_name)
    
    @contextmanager
    def monitor_operation(self, operation_name: str, operation_type: str = "business"):
        """Monitor any operation with automatic metrics collection."""
        if operation_type == "business":
            with self.collector.time_business_operation(operation_name):
                yield
        elif operation_type == "request":
            with self.collector.time_request("POST", f"/{operation_name}"):
                yield
        else:
            # Generic monitoring
            start_time = time.time()
            try:
                yield
            finally:
                duration = time.time() - start_time
                logger.info(f"Operation {operation_name} took {duration:.3f}s")
    
    def track_resource_usage(self, connections: int = None, queue_sizes: Dict[str, int] = None):
        """Track resource usage metrics."""
        if connections is not None:
            self.collector.set_active_connections(connections)
        
        if queue_sizes:
            for queue_type, size in queue_sizes.items():
                self.collector.set_queue_size(queue_type, size)
    
    def alert_on_threshold(self, metric_name: str, value: float, threshold: float, 
                          comparison: str = "greater") -> bool:
        """Check if a metric exceeds threshold and alert if needed."""
        should_alert = False
        
        if comparison == "greater" and value > threshold:
            should_alert = True
        elif comparison == "less" and value < threshold:
            should_alert = True
        
        if should_alert:
            self.collector.record_error(
                f"threshold_exceeded_{metric_name}",
                "high",
                f"{metric_name} value {value} {comparison} than threshold {threshold}"
            )
            logger.warning(f"ALERT: {metric_name} = {value} (threshold: {threshold})")
        
        return should_alert


# Utility functions for common patterns
@contextmanager
def time_operation(service_name: str, operation_name: str, operation_type: str = "business"):
    """Convenience context manager for timing operations."""
    monitor = PerformanceMonitor(service_name)
    with monitor.monitor_operation(operation_name, operation_type):
        yield


def setup_metrics_endpoint(app, endpoint: str = "/metrics"):
    """Setup metrics endpoint for web applications (FastAPI example)."""
    try:
        @app.get(endpoint)
        async def metrics():
            return Response(get_metrics_output(), media_type=get_metrics_content_type())
        logger.info(f"Metrics endpoint available at {endpoint}")
    except Exception as e:
        logger.error(f"Failed to setup metrics endpoint: {e}")


def reset_metrics():
    """Reset all metrics (useful for testing)."""
    global default_registry, _service_collectors
    default_registry = CollectorRegistry()
    _service_collectors.clear()
    logger.info("All metrics have been reset")
