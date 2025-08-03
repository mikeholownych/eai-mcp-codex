import time
import psutil
import asyncio
import aiohttp
import asyncpg
import redis.asyncio as redis
from typing import Dict, Any, Optional, List, Callable, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from contextlib import asynccontextmanager
import json
import socket
import os

from .logging import get_logger
from .tracing import get_tracer, traced
from .metrics import get_metrics_collector

logger = get_logger("health")


class HealthStatus(Enum):
    """Health status enumeration."""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"
    ERROR = "error"


class HealthCheckType(Enum):
    """Health check type enumeration."""
    LIVENESS = "liveness"
    READINESS = "readiness"
    DEPENDENCY = "dependency"
    RESOURCE = "resource"
    BUSINESS_LOGIC = "business_logic"
    PERFORMANCE = "performance"


@dataclass
class HealthCheckResult:
    """Result of a health check."""

    name: str
    status: HealthStatus
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    duration_ms: float = 0.0
    check_type: HealthCheckType = HealthCheckType.LIVENESS
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "status": self.status.value,
            "message": self.message,
            "details": self.details,
            "duration_ms": self.duration_ms,
            "check_type": self.check_type.value,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class HealthCheckConfig:
    """Configuration for a health check."""
    name: str
    check_func: Union[Callable, Callable[[], asyncio.Awaitable]]
    check_type: HealthCheckType = HealthCheckType.LIVENESS
    critical: bool = True
    timeout: float = 5.0
    interval: float = 30.0
    retry_count: int = 3
    retry_delay: float = 1.0
    enabled: bool = True


class HealthChecker:
    """Comprehensive health checking system with enhanced features."""

    def __init__(self, service_name: str):
        self.service_name = service_name
        self.checks: Dict[str, HealthCheckConfig] = {}
        self.start_time = datetime.utcnow()
        self.last_check_time: Dict[str, datetime] = {}
        self.check_history: Dict[str, List[HealthCheckResult]] = {}
        self.tracer = get_tracer()
        self.metrics = get_metrics_collector(service_name)
        self._lock = asyncio.Lock()

    def register_check(self, config: HealthCheckConfig):
        """Register a health check with configuration."""
        self.checks[config.name] = config
        self.check_history[config.name] = []
        logger.info(f"Registered health check: {config.name} ({config.check_type.value})")

    def register_simple_check(self, name: str, check_func: Callable, **kwargs):
        """Register a simple health check function."""
        config = HealthCheckConfig(name=name, check_func=check_func, **kwargs)
        self.register_check(config)

    async def run_check(self, name: str) -> HealthCheckResult:
        """Run a specific health check."""
        if name not in self.checks:
            return HealthCheckResult(
                name=name,
                status=HealthStatus.ERROR,
                message=f"Health check '{name}' not found",
            )

        config = self.checks[name]
        if not config.enabled:
            return HealthCheckResult(
                name=name,
                status=HealthStatus.HEALTHY,
                message="Check disabled",
                check_type=config.check_type,
            )

        start_time = time.time()
        
        with self.tracer.start_span(f"health_check.{name}") as span:
            span.set_attribute("health_check.name", name)
            span.set_attribute("health_check.type", config.check_type.value)
            span.set_attribute("health_check.critical", config.critical)
            
            try:
                # Run the check with retries
                result = await self._run_check_with_retries(config)
                duration_ms = (time.time() - start_time) * 1000
                
                result.duration_ms = duration_ms
                result.check_type = config.check_type
                
                # Record metrics
                self._record_check_metrics(result)
                
                # Update history
                self.check_history[name].append(result)
                if len(self.check_history[name]) > 100:  # Keep last 100 results
                    self.check_history[name].pop(0)
                
                self.last_check_time[name] = datetime.utcnow()
                
                # Set span attributes
                span.set_attribute("health_check.status", result.status.value)
                span.set_attribute("health_check.duration_ms", duration_ms)
                
                return result
                
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                logger.error(f"Health check '{name}' failed: {e}")
                
                result = HealthCheckResult(
                    name=name,
                    status=HealthStatus.ERROR,
                    message=str(e),
                    duration_ms=duration_ms,
                    check_type=config.check_type,
                )
                
                # Record error metrics
                self._record_check_metrics(result)
                
                # Set span attributes for error
                span.set_attribute("health_check.status", result.status.value)
                span.set_attribute("health_check.duration_ms", duration_ms)
                span.set_status("ERROR", str(e))
                
                return result

    async def _run_check_with_retries(self, config: HealthCheckConfig) -> HealthCheckResult:
        """Run a health check with retries."""
        last_exception = None
        
        for attempt in range(config.retry_count + 1):
            try:
                if asyncio.iscoroutinefunction(config.check_func):
                    result = await asyncio.wait_for(
                        config.check_func(),
                        timeout=config.timeout
                    )
                else:
                    # Run sync function in executor
                    result = await asyncio.wait_for(
                        asyncio.get_event_loop().run_in_executor(None, config.check_func),
                        timeout=config.timeout
                    )
                
                # Convert result to HealthCheckResult if needed
                if isinstance(result, bool):
                    return HealthCheckResult(
                        name=config.name,
                        status=HealthStatus.HEALTHY if result else HealthStatus.UNHEALTHY,
                        message="OK" if result else "Check failed",
                    )
                elif isinstance(result, dict):
                    return HealthCheckResult(
                        name=config.name,
                        status=HealthStatus(result.get("status", "healthy")),
                        message=result.get("message", "OK"),
                        details=result.get("details", {}),
                    )
                else:
                    return HealthCheckResult(
                        name=config.name,
                        status=HealthStatus.HEALTHY,
                        message=str(result),
                    )
                    
            except asyncio.TimeoutError:
                last_exception = "Timeout"
                if attempt < config.retry_count:
                    await asyncio.sleep(config.retry_delay)
                    continue
            except Exception as e:
                last_exception = str(e)
                if attempt < config.retry_count:
                    await asyncio.sleep(config.retry_delay)
                    continue
        
        # All retries failed
        return HealthCheckResult(
            name=config.name,
            status=HealthStatus.UNHEALTHY,
            message=f"Check failed after {config.retry_count + 1} attempts: {last_exception}",
        )

    async def run_checks_by_type(self, check_type: HealthCheckType) -> Dict[str, HealthCheckResult]:
        """Run all health checks of a specific type."""
        results = {}
        
        for name, config in self.checks.items():
            if config.check_type == check_type:
                results[name] = await self.run_check(name)
        
        return results

    async def run_all_checks(self) -> Dict[str, Any]:
        """Run all registered health checks and return comprehensive report."""
        async with self._lock:
            results = {}
            overall_status = HealthStatus.HEALTHY
            critical_failures = []
            degraded_checks = []

            # Group checks by type
            checks_by_type = {}
            for name, config in self.checks.items():
                if config.enabled:
                    if config.check_type not in checks_by_type:
                        checks_by_type[config.check_type] = []
                    checks_by_type[config.check_type].append(name)

            # Run checks by type in parallel
            for check_type, check_names in checks_by_type.items():
                tasks = [self.run_check(name) for name in check_names]
                type_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for i, result in enumerate(type_results):
                    name = check_names[i]
                    if isinstance(result, Exception):
                        logger.error(f"Health check '{name}' failed with exception: {result}")
                        results[name] = HealthCheckResult(
                            name=name,
                            status=HealthStatus.ERROR,
                            message=f"Exception: {str(result)}",
                            check_type=check_type,
                        ).to_dict()
                    else:
                        results[name] = result.to_dict()

            # Determine overall status
            for name, config in self.checks.items():
                if not config.enabled:
                    continue
                    
                result_data = results.get(name)
                if not result_data:
                    continue
                    
                result_status = HealthStatus(result_data["status"])
                
                if config.critical and result_status in [HealthStatus.UNHEALTHY, HealthStatus.ERROR]:
                    overall_status = HealthStatus.UNHEALTHY
                    critical_failures.append(name)
                elif result_status == HealthStatus.DEGRADED:
                    if overall_status == HealthStatus.HEALTHY:
                        overall_status = HealthStatus.DEGRADED
                    degraded_checks.append(name)
                elif result_status == HealthStatus.ERROR and not config.critical:
                    if overall_status == HealthStatus.HEALTHY:
                        overall_status = HealthStatus.DEGRADED

            uptime_seconds = (datetime.utcnow() - self.start_time).total_seconds()
            
            # Calculate health score
            health_score = self._calculate_health_score(results)

            return {
                "service": self.service_name,
                "status": overall_status.value,
                "health_score": health_score,
                "timestamp": datetime.utcnow().isoformat(),
                "uptime_seconds": uptime_seconds,
                "critical_failures": critical_failures,
                "degraded_checks": degraded_checks,
                "checks_by_type": {
                    check_type.value: [
                        name for name, config in self.checks.items()
                        if config.check_type == check_type and config.enabled
                    ]
                    for check_type in HealthCheckType
                },
                "checks": results,
            }

    def _calculate_health_score(self, results: Dict[str, Any]) -> float:
        """Calculate overall health score (0.0 to 1.0)."""
        if not results:
            return 1.0
        
        total_weight = 0
        weighted_score = 0
        
        for name, config in self.checks.items():
            if not config.enabled:
                continue
                
            result_data = results.get(name)
            if not result_data:
                continue
                
            weight = 3 if config.critical else 1
            total_weight += weight
            
            status = HealthStatus(result_data["status"])
            if status == HealthStatus.HEALTHY:
                score = 1.0
            elif status == HealthStatus.DEGRADED:
                score = 0.7
            elif status == HealthStatus.UNHEALTHY:
                score = 0.3
            else:  # ERROR
                score = 0.0
            
            weighted_score += score * weight
        
        return weighted_score / total_weight if total_weight > 0 else 1.0

    def _record_check_metrics(self, result: HealthCheckResult):
        """Record health check metrics."""
        # Record health check result
        self.metrics.record_business_operation(
            f"health_check_{result.name}",
            result.status.value,
            result.duration_ms / 1000.0
        )
        
        # Record error if unhealthy
        if result.status in [HealthStatus.UNHEALTHY, HealthStatus.ERROR]:
            self.metrics.record_error(
                "health_check_failure",
                "high" if result.status == HealthStatus.ERROR else "medium",
                f"Health check {result.name} failed: {result.message}"
            )

    def get_check_history(self, name: str, limit: int = 10) -> List[HealthCheckResult]:
        """Get recent history for a specific health check."""
        return self.check_history.get(name, [])[-limit:]

    def get_service_health_summary(self) -> Dict[str, Any]:
        """Get a summary of service health without running checks."""
        return {
            "service": self.service_name,
            "uptime_seconds": (datetime.utcnow() - self.start_time).total_seconds(),
            "registered_checks": len(self.checks),
            "enabled_checks": sum(1 for c in self.checks.values() if c.enabled),
            "check_types": {
                check_type.value: [
                    name for name, config in self.checks.items()
                    if config.check_type == check_type
                ]
                for check_type in HealthCheckType
            },
            "last_check_times": {
                name: self.last_check_time[name].isoformat()
                for name in self.last_check_time
            }
        }


# Enhanced health check functions
async def check_memory_usage(max_usage_percent: float = 80.0) -> Dict[str, Any]:
    """Check system memory usage."""
    try:
        memory = psutil.virtual_memory()
        usage_percent = memory.percent

        status = HealthStatus.HEALTHY if usage_percent < max_usage_percent else HealthStatus.UNHEALTHY
        
        # Degraded status if approaching limit
        if usage_percent >= max_usage_percent * 0.9:
            status = HealthStatus.DEGRADED

        return {
            "status": status.value,
            "message": f"Memory usage: {usage_percent:.1f}%",
            "details": {
                "usage_percent": usage_percent,
                "available_mb": round(memory.available / (1024 * 1024), 2),
                "total_mb": round(memory.total / (1024 * 1024), 2),
                "used_mb": round(memory.used / (1024 * 1024), 2),
                "max_threshold_percent": max_usage_percent,
            },
        }
    except Exception as e:
        return {
            "status": HealthStatus.ERROR.value,
            "message": f"Memory check failed: {str(e)}",
        }


async def check_disk_usage(
    path: str = "/", max_usage_percent: float = 80.0
) -> Dict[str, Any]:
    """Check disk usage for a given path."""
    try:
        disk = psutil.disk_usage(path)
        usage_percent = (disk.used / disk.total) * 100

        status = HealthStatus.HEALTHY if usage_percent < max_usage_percent else HealthStatus.UNHEALTHY
        
        # Degraded status if approaching limit
        if usage_percent >= max_usage_percent * 0.9:
            status = HealthStatus.DEGRADED

        return {
            "status": status.value,
            "message": f"Disk usage ({path}): {usage_percent:.1f}%",
            "details": {
                "path": path,
                "usage_percent": usage_percent,
                "free_gb": round(disk.free / (1024 * 1024 * 1024), 2),
                "total_gb": round(disk.total / (1024 * 1024 * 1024), 2),
                "used_gb": round(disk.used / (1024 * 1024 * 1024), 2),
                "max_threshold_percent": max_usage_percent,
            },
        }
    except Exception as e:
        return {
            "status": HealthStatus.ERROR.value,
            "message": f"Disk check failed: {str(e)}",
        }


async def check_cpu_usage(max_usage_percent: float = 80.0, duration: float = 1.0) -> Dict[str, Any]:
    """Check CPU usage over a duration."""
    try:
        # Get CPU usage over the specified duration
        usage_percent = psutil.cpu_percent(interval=duration)
        
        status = HealthStatus.HEALTHY if usage_percent < max_usage_percent else HealthStatus.UNHEALTHY
        
        # Degraded status if approaching limit
        if usage_percent >= max_usage_percent * 0.9:
            status = HealthStatus.DEGRADED

        # Get additional CPU info
        cpu_count = psutil.cpu_count()
        cpu_count_logical = psutil.cpu_count(logical=True)
        load_avg = psutil.getloadavg() if hasattr(psutil, 'getloadavg') else [0, 0, 0]

        return {
            "status": status.value,
            "message": f"CPU usage: {usage_percent:.1f}% over {duration}s",
            "details": {
                "usage_percent": usage_percent,
                "duration_seconds": duration,
                "cpu_count_physical": cpu_count,
                "cpu_count_logical": cpu_count_logical,
                "load_avg_1min": load_avg[0],
                "load_avg_5min": load_avg[1],
                "load_avg_15min": load_avg[2],
                "max_threshold_percent": max_usage_percent,
            },
        }
    except Exception as e:
        return {
            "status": HealthStatus.ERROR.value,
            "message": f"CPU check failed: {str(e)}",
        }


async def check_redis_connection(redis_client, timeout: float = 5.0) -> Dict[str, Any]:
    """Check Redis connectivity and performance."""
    try:
        start_time = time.time()
        await asyncio.wait_for(redis_client.ping(), timeout=timeout)
        ping_time = (time.time() - start_time) * 1000
        
        # Get Redis info
        info = await redis_client.info()
        
        # Check memory usage
        used_memory = int(info.get('used_memory', 0))
        max_memory = int(info.get('maxmemory', 0))
        memory_usage_percent = (used_memory / max_memory * 100) if max_memory > 0 else 0
        
        # Check connection count
        connected_clients = int(info.get('connected_clients', 0))
        max_clients = int(info.get('maxclients', 10000))
        client_usage_percent = (connected_clients / max_clients * 100) if max_clients > 0 else 0
        
        # Determine status based on performance metrics
        status = HealthStatus.HEALTHY
        if ping_time > 1000:  # More than 1 second ping time
            status = HealthStatus.DEGRADED
        if ping_time > 5000:  # More than 5 seconds ping time
            status = HealthStatus.UNHEALTHY
        if memory_usage_percent > 90 or client_usage_percent > 90:
            status = HealthStatus.DEGRADED
        if memory_usage_percent > 95 or client_usage_percent > 95:
            status = HealthStatus.UNHEALTHY

        return {
            "status": status.value,
            "message": f"Redis connection OK (ping: {ping_time:.1f}ms)",
            "details": {
                "redis_version": info.get("redis_version"),
                "ping_time_ms": round(ping_time, 2),
                "connected_clients": connected_clients,
                "max_clients": max_clients,
                "client_usage_percent": round(client_usage_percent, 2),
                "used_memory_mb": round(used_memory / (1024 * 1024), 2),
                "max_memory_mb": round(max_memory / (1024 * 1024), 2) if max_memory > 0 else 0,
                "memory_usage_percent": round(memory_usage_percent, 2),
                "uptime_seconds": int(info.get("uptime_in_seconds", 0)),
            },
        }
    except Exception as e:
        return {
            "status": HealthStatus.ERROR.value,
            "message": f"Redis connection failed: {str(e)}",
        }


async def check_database_connection(db_pool, timeout: float = 5.0) -> Dict[str, Any]:
    """Check database connectivity and performance."""
    try:
        start_time = time.time()
        
        # Test basic connection
        async with db_pool.acquire() as conn:
            await asyncio.wait_for(conn.fetchval("SELECT 1"), timeout=timeout)
            
        connection_time = (time.time() - start_time) * 1000
        
        # Get database stats
        async with db_pool.acquire() as conn:
            # Get connection pool stats
            pool_stats = db_pool.get_size()
            
            # Get database stats
            db_stats = await conn.fetchrow("""
                SELECT 
                    count(*) as total_connections,
                    count(*) filter (where state = 'active') as active_connections,
                    count(*) filter (where state = 'idle') as idle_connections
                FROM pg_stat_activity 
                WHERE datname = current_database()
            """)
            
            # Get table count
            table_count = await conn.fetchval("""
                SELECT count(*) 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """)
        
        # Determine status based on performance metrics
        status = HealthStatus.HEALTHY
        if connection_time > 1000:  # More than 1 second connection time
            status = HealthStatus.DEGRADED
        if connection_time > 5000:  # More than 5 seconds connection time
            status = HealthStatus.UNHEALTHY
        
        # Check pool usage
        pool_usage_percent = (pool_stats[0] / db_pool.get_max_size()) * 100
        if pool_usage_percent > 90:
            status = HealthStatus.DEGRADED
        if pool_usage_percent > 95:
            status = HealthStatus.UNHEALTHY

        return {
            "status": status.value,
            "message": f"Database connection OK (connection: {connection_time:.1f}ms)",
            "details": {
                "connection_time_ms": round(connection_time, 2),
                "pool_size": pool_stats[0],
                "pool_max_size": db_pool.get_max_size(),
                "pool_usage_percent": round(pool_usage_percent, 2),
                "total_connections": db_stats['total_connections'],
                "active_connections": db_stats['active_connections'],
                "idle_connections": db_stats['idle_connections'],
                "table_count": table_count,
            },
        }
    except Exception as e:
        return {
            "status": HealthStatus.ERROR.value,
            "message": f"Database connection failed: {str(e)}",
        }


async def check_external_service(url: str, timeout: int = 5, method: str = "GET") -> Dict[str, Any]:
    """Check external service availability and performance."""
    try:
        start_time = time.time()
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
            async with session.request(method, url) as response:
                response_time = (time.time() - start_time) * 1000
                content = await response.text()
                
                # Determine status based on response
                if response.status == 200:
                    status = HealthStatus.HEALTHY
                    if response_time > 2000:  # More than 2 seconds
                        status = HealthStatus.DEGRADED
                    if response_time > 5000:  # More than 5 seconds
                        status = HealthStatus.UNHEALTHY
                elif response.status in [401, 403, 404]:
                    status = HealthStatus.DEGRADED
                else:
                    status = HealthStatus.UNHEALTHY

                return {
                    "status": status.value,
                    "message": f"Service responded with status {response.status}",
                    "details": {
                        "url": url,
                        "method": method,
                        "status_code": response.status,
                        "response_time_ms": round(response_time, 2),
                        "content_length": len(content),
                        "response_headers": dict(response.headers),
                    },
                }
    except asyncio.TimeoutError:
        return {
            "status": HealthStatus.UNHEALTHY.value,
            "message": f"Service check timed out after {timeout}s",
            "details": {"url": url, "timeout": timeout},
        }
    except Exception as e:
        return {
            "status": HealthStatus.ERROR.value,
            "message": f"Service check failed: {str(e)}",
            "details": {"url": url},
        }


async def check_file_system(path: str, operation: str = "read") -> Dict[str, Any]:
    """Check file system operations."""
    try:
        if operation == "read":
            # Test read operation
            if not os.path.exists(path):
                return {
                    "status": HealthStatus.ERROR.value,
                    "message": f"Path does not exist: {path}",
                }
            
            if os.path.isfile(path):
                with open(path, 'r') as f:
                    content = f.read(100)  # Read first 100 bytes
                return {
                    "status": HealthStatus.HEALTHY.value,
                    "message": f"File read successful: {path}",
                    "details": {
                        "path": path,
                        "operation": "read",
                        "file_size_bytes": os.path.getsize(path),
                        "content_preview": content[:50],
                    },
                }
            else:
                # Directory read test
                files = os.listdir(path)[:10]  # List first 10 files
                return {
                    "status": HealthStatus.HEALTHY.value,
                    "message": f"Directory read successful: {path}",
                    "details": {
                        "path": path,
                        "operation": "read",
                        "file_count": len(os.listdir(path)),
                        "sample_files": files,
                    },
                }
                
        elif operation == "write":
            # Test write operation
            if not os.path.exists(path):
                os.makedirs(path, exist_ok=True)
            
            test_file = os.path.join(path, f"health_check_{int(time.time())}.tmp")
            try:
                with open(test_file, 'w') as f:
                    f.write("health check test")
                os.remove(test_file)
                
                return {
                    "status": HealthStatus.HEALTHY.value,
                    "message": f"File write successful: {path}",
                    "details": {
                        "path": path,
                        "operation": "write",
                        "test_file": test_file,
                    },
                }
            except Exception as e:
                return {
                    "status": HealthStatus.ERROR.value,
                    "message": f"File write failed: {str(e)}",
                    "details": {"path": path, "operation": "write"},
                }
        
        else:
            return {
                "status": HealthStatus.ERROR.value,
                "message": f"Unsupported operation: {operation}",
            }
            
    except Exception as e:
        return {
            "status": HealthStatus.ERROR.value,
            "message": f"File system check failed: {str(e)}",
            "details": {"path": path, "operation": operation},
        }


async def check_network_connectivity(host: str = "8.8.8.8", port: int = 53, timeout: float = 5.0) -> Dict[str, Any]:
    """Check basic network connectivity."""
    try:
        start_time = time.time()
        
        # Create socket and attempt connection
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        
        result = sock.connect_ex((host, port))
        connection_time = (time.time() - start_time) * 1000
        
        sock.close()
        
        if result == 0:
            status = HealthStatus.HEALTHY
            if connection_time > 1000:  # More than 1 second
                status = HealthStatus.DEGRADED
            if connection_time > 3000:  # More than 3 seconds
                status = HealthStatus.UNHEALTHY
                
            return {
                "status": status.value,
                "message": f"Network connectivity OK to {host}:{port}",
                "details": {
                    "host": host,
                    "port": port,
                    "connection_time_ms": round(connection_time, 2),
                    "timeout": timeout,
                },
            }
        else:
            return {
                "status": HealthStatus.UNHEALTHY.value,
                "message": f"Failed to connect to {host}:{port}",
                "details": {
                    "host": host,
                    "port": port,
                    "error_code": result,
                    "timeout": timeout,
                },
            }
            
    except Exception as e:
        return {
            "status": HealthStatus.ERROR.value,
            "message": f"Network check failed: {str(e)}",
            "details": {"host": host, "port": port},
        }


async def check_process_running(process_name: str) -> Dict[str, Any]:
    """Check if a specific process is running."""
    try:
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'status']):
            try:
                if process_name.lower() in proc.info['name'].lower():
                    processes.append({
                        'pid': proc.info['pid'],
                        'name': proc.info['name'],
                        'status': proc.info['status'],
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        
        if processes:
            return {
                "status": HealthStatus.HEALTHY.value,
                "message": f"Process '{process_name}' is running ({len(processes)} instances)",
                "details": {
                    "process_name": process_name,
                    "instances": processes,
                    "instance_count": len(processes),
                },
            }
        else:
            return {
                "status": HealthStatus.UNHEALTHY.value,
                "message": f"Process '{process_name}' is not running",
                "details": {
                    "process_name": process_name,
                    "instance_count": 0,
                },
            }
            
    except Exception as e:
        return {
            "status": HealthStatus.ERROR.value,
            "message": f"Process check failed: {str(e)}",
            "details": {"process_name": process_name},
        }


# Health check decorators and context managers
def health_check(name: str, check_type: HealthCheckType = HealthCheckType.LIVENESS, **kwargs):
    """Decorator to register a function as a health check."""
    def decorator(func):
        async def wrapper():
            return await func()
        
        # Store the health check info on the function
        wrapper._health_check_info = {
            'name': name,
            'check_type': check_type,
            'func': wrapper,
            **kwargs
        }
        return wrapper
    return decorator


@asynccontextmanager
async def monitor_health(check_name: str, checker: HealthChecker):
    """Context manager to monitor health during an operation."""
    start_result = await checker.run_check(check_name)
    logger.info(f"Health check '{check_name}' before operation: {start_result.status.value}")
    
    try:
        yield start_result
    finally:
        end_result = await checker.run_check(check_name)
        logger.info(f"Health check '{check_name}' after operation: {end_result.status.value}")
        
        # Log if health degraded
        if start_result.status == HealthStatus.HEALTHY and end_result.status != HealthStatus.HEALTHY:
            logger.warning(f"Health degraded for '{check_name}' during operation")


# Global health checker instances
_health_checkers: Dict[str, HealthChecker] = {}


def get_health_checker(service_name: str = "default") -> HealthChecker:
    """Get or create a health checker for a service."""
    if service_name not in _health_checkers:
        _health_checkers[service_name] = HealthChecker(service_name)
        
        # Register common checks
        _health_checkers[service_name].register_simple_check(
            "memory_usage", 
            lambda: check_memory_usage(),
            check_type=HealthCheckType.RESOURCE,
            critical=False
        )
        _health_checkers[service_name].register_simple_check(
            "disk_usage", 
            lambda: check_disk_usage(),
            check_type=HealthCheckType.RESOURCE,
            critical=False
        )
        _health_checkers[service_name].register_simple_check(
            "cpu_usage", 
            lambda: check_cpu_usage(),
            check_type=HealthCheckType.RESOURCE,
            critical=False
        )
        _health_checkers[service_name].register_simple_check(
            "network_connectivity", 
            lambda: check_network_connectivity(),
            check_type=HealthCheckType.DEPENDENCY,
            critical=False
        )
    
    return _health_checkers[service_name]


async def health() -> Dict[str, str]:
    """Return the standard health payload (legacy compatibility)."""
    return {"status": "ok"}


async def detailed_health(service_name: str = "default") -> Dict[str, Any]:
    """Return detailed health information."""
    checker = get_health_checker(service_name)
    return await checker.run_all_checks()


async def health_by_type(service_name: str = "default", check_type: HealthCheckType = HealthCheckType.LIVENESS) -> Dict[str, Any]:
    """Return health information for a specific check type."""
    checker = get_health_checker(service_name)
    results = await checker.run_checks_by_type(check_type)
    return {
        "service": service_name,
        "check_type": check_type.value,
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {name: result.to_dict() for name, result in results.items()},
    }


def register_health_check(name: str, check_func: Callable, **kwargs):
    """Register a custom health check (convenience function)."""
    checker = get_health_checker()
    config = HealthCheckConfig(name=name, check_func=check_func, **kwargs)
    checker.register_check(config)


def register_health_checks_from_module(module, service_name: str = "default"):
    """Register health checks from a module."""
    checker = get_health_checker(service_name)
    
    for attr_name in dir(module):
        attr = getattr(module, attr_name)
        if hasattr(attr, '_health_check_info'):
            info = attr._health_check_info
            config = HealthCheckConfig(
                name=info['name'],
                check_func=info['func'],
                check_type=info['check_type'],
                **{k: v for k, v in info.items() if k not in ['name', 'check_type', 'func']}
            )
            checker.register_check(config)