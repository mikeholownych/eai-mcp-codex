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


# Common health check functions
def check_memory_usage(max_usage_percent: float = 80.0) -> Dict[str, Any]:
    """Check system memory usage."""
    memory = psutil.virtual_memory()
    usage_percent = memory.percent

    status = "healthy" if usage_percent < max_usage_percent else "unhealthy"

    return {
        "status": status,
        "message": f"Memory usage: {usage_percent:.1f}%",
        "details": {
            "usage_percent": usage_percent,
            "available_mb": memory.available / (1024 * 1024),
            "total_mb": memory.total / (1024 * 1024),
        },
    }


def check_disk_usage(
    path: str = "/", max_usage_percent: float = 80.0
) -> Dict[str, Any]:
    """Check disk usage for a given path."""
    disk = psutil.disk_usage(path)
    usage_percent = (disk.used / disk.total) * 100

    status = "healthy" if usage_percent < max_usage_percent else "unhealthy"

    return {
        "status": status,
        "message": f"Disk usage ({path}): {usage_percent:.1f}%",
        "details": {
            "path": path,
            "usage_percent": usage_percent,
            "free_gb": disk.free / (1024 * 1024 * 1024),
            "total_gb": disk.total / (1024 * 1024 * 1024),
        },
    }





def check_redis_connection(redis_client) -> Dict[str, Any]:
    """Check Redis connectivity."""
    try:
        redis_client.ping()
        info = redis_client.info()

        return {
            "status": "healthy",
            "message": "Redis connection OK",
            "details": {
                "redis_version": info.get("redis_version"),
                "connected_clients": info.get("connected_clients"),
                "used_memory_human": info.get("used_memory_human"),
            },
        }
    except Exception as e:
        return {"status": "unhealthy", "message": f"Redis connection failed: {str(e)}"}


def check_external_service(url: str, timeout: int = 5) -> Dict[str, Any]:
    """Check external service availability."""
    import requests

    try:
        start_time = time.time()
        response = requests.get(url, timeout=timeout)
        response_time = (time.time() - start_time) * 1000

        status = "healthy" if response.status_code == 200 else "unhealthy"

        return {
            "status": status,
            "message": f"Service responded with status {response.status_code}",
            "details": {
                "url": url,
                "status_code": response.status_code,
                "response_time_ms": response_time,
            },
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "message": f"Service check failed: {str(e)}",
            "details": {"url": url},
        }


# Global health checker instance
_health_checker: Optional[HealthChecker] = None


def get_health_checker(service_name: str = "default") -> HealthChecker:
    """Get or create the global health checker."""
    global _health_checker
    if _health_checker is None:
        _health_checker = HealthChecker(service_name)

        # Register common checks
        _health_checker.register_check(
            "memory", lambda: check_memory_usage(), critical=False
        )
        _health_checker.register_check(
            "disk", lambda: check_disk_usage(), critical=False
        )

    return _health_checker


def health() -> Dict[str, str]:
    """Return the standard health payload (legacy compatibility)."""
    return {"status": "ok"}


def detailed_health(service_name: str = "default") -> Dict[str, Any]:
    """Return detailed health information."""
    checker = get_health_checker(service_name)
    return checker.run_all_checks()


def register_health_check(name: str, check_func: callable, critical: bool = True):
    """Register a custom health check (convenience function)."""
    checker = get_health_checker()
    checker.register_check(name, check_func, critical)
