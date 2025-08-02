import time
import psutil
from typing import Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass

from .logging import get_logger

logger = get_logger("health")


@dataclass
class HealthCheckResult:
    """Result of a health check."""

    name: str
    status: str
    message: str
    details: Dict[str, Any] = None
    duration_ms: float = 0.0


class HealthChecker:
    """Comprehensive health checking system."""

    def __init__(self, service_name: str):
        self.service_name = service_name
        self.checks = {}
        self.start_time = datetime.utcnow()

    def register_check(self, name: str, check_func: callable, critical: bool = True):
        """Register a health check function."""
        self.checks[name] = {"func": check_func, "critical": critical}

    def run_check(self, name: str) -> HealthCheckResult:
        """Run a specific health check."""
        if name not in self.checks:
            return HealthCheckResult(
                name=name, status="error", message=f"Health check '{name}' not found"
            )

        start_time = time.time()
        try:
            check_func = self.checks[name]["func"]
            result = check_func()

            duration_ms = (time.time() - start_time) * 1000

            if isinstance(result, bool):
                return HealthCheckResult(
                    name=name,
                    status="healthy" if result else "unhealthy",
                    message="OK" if result else "Check failed",
                    duration_ms=duration_ms,
                )
            elif isinstance(result, dict):
                return HealthCheckResult(
                    name=name,
                    status=result.get("status", "healthy"),
                    message=result.get("message", "OK"),
                    details=result.get("details"),
                    duration_ms=duration_ms,
                )
            else:
                return HealthCheckResult(
                    name=name,
                    status="healthy",
                    message=str(result),
                    duration_ms=duration_ms,
                )

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(f"Health check '{name}' failed: {e}")
            return HealthCheckResult(
                name=name, status="error", message=str(e), duration_ms=duration_ms
            )

    def run_all_checks(self) -> Dict[str, Any]:
        """Run all registered health checks."""
        results = {}
        overall_status = "healthy"

        for name, config in self.checks.items():
            result = self.run_check(name)
            results[name] = {
                "status": result.status,
                "message": result.message,
                "duration_ms": result.duration_ms,
            }

            if result.details:
                results[name]["details"] = result.details

            # If this is a critical check and it's not healthy, mark overall as unhealthy
            if config["critical"] and result.status != "healthy":
                overall_status = "unhealthy"

        uptime_seconds = (datetime.utcnow() - self.start_time).total_seconds()

        return {
            "service": self.service_name,
            "status": overall_status,
            "timestamp": datetime.utcnow().isoformat(),
            "uptime_seconds": uptime_seconds,
            "checks": results,
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
