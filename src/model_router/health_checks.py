"""
Model Router specific health checks.
Provides comprehensive health monitoring for the Model Router service.
"""

import time
import asyncio
import json
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from ..common.enhanced_health_check import (
    HealthStatus, HealthCheckType, HealthChecker, 
    check_memory_usage, check_disk_usage, check_cpu_usage,
    check_network_connectivity, health_check
)
from ..common.logging import get_logger
from ..common.tracing import get_tracer
from ..common.metrics import get_metrics_collector

logger = get_logger("model_router.health")
tracer = get_tracer()
metrics = get_metrics_collector("model_router")


class ModelRouterHealthChecker:
    """Health checker for Model Router service."""
    
    def __init__(self):
        self.service_name = "model-router"
        self.base_checker = HealthChecker(self.service_name)
        self._setup_health_checks()
    
    def _setup_health_checks(self):
        """Set up all health checks for Model Router."""
        
        # Basic resource checks
        self.base_checker.register_simple_check(
            "memory_usage",
            lambda: check_memory_usage(max_usage_percent=85.0),
            check_type=HealthCheckType.RESOURCE,
            critical=False
        )
        
        self.base_checker.register_simple_check(
            "disk_usage",
            lambda: check_disk_usage(max_usage_percent=85.0),
            check_type=HealthCheckType.RESOURCE,
            critical=False
        )
        
        self.base_checker.register_simple_check(
            "cpu_usage",
            lambda: check_cpu_usage(max_usage_percent=85.0),
            check_type=HealthCheckType.RESOURCE,
            critical=False
        )
        
        # Model Router specific checks
        self.base_checker.register_simple_check(
            "model_availability",
            self._check_model_availability,
            check_type=HealthCheckType.BUSINESS_LOGIC,
            critical=True
        )
        
        self.base_checker.register_simple_check(
            "routing_logic",
            self._check_routing_logic,
            check_type=HealthCheckType.BUSINESS_LOGIC,
            critical=True
        )
        
        self.base_checker.register_simple_check(
            "api_connectivity",
            self._check_api_connectivity,
            check_type=HealthCheckType.DEPENDENCY,
            critical=True
        )
        
        self.base_checker.register_simple_check(
            "model_performance",
            self._check_model_performance,
            check_type=HealthCheckType.PERFORMANCE,
            critical=False
        )
        
        self.base_checker.register_simple_check(
            "cache_health",
            self._check_cache_health,
            check_type=HealthCheckType.DEPENDENCY,
            critical=False
        )
        
        self.base_checker.register_simple_check(
            "configuration_validity",
            self._check_configuration_validity,
            check_type=HealthCheckType.READINESS,
            critical=True
        )
        
        self.base_checker.register_simple_check(
            "rate_limiting",
            self._check_rate_limiting,
            check_type=HealthCheckType.BUSINESS_LOGIC,
            critical=False
        )
    
    async def _check_model_availability(self) -> Dict[str, Any]:
        """Check availability of configured models."""
        try:
            # This would typically check against actual model endpoints
            # For now, we'll simulate the check
            
            # Simulated model list
            models = [
                {"name": "claude-3-opus", "available": True, "endpoint": "http://localhost:8001"},
                {"name": "claude-3-sonnet", "available": True, "endpoint": "http://localhost:8001"},
                {"name": "claude-3-haiku", "available": True, "endpoint": "http://localhost:8001"},
            ]
            
            # Check model availability
            unavailable_models = [m for m in models if not m["available"]]
            
            if unavailable_models:
                return {
                    "status": HealthStatus.DEGRADED.value,
                    "message": f"{len(unavailable_models)} models unavailable",
                    "details": {
                        "total_models": len(models),
                        "available_models": len(models) - len(unavailable_models),
                        "unavailable_models": unavailable_models,
                        "model_status": {m["name"]: m["available"] for m in models},
                    },
                }
            else:
                return {
                    "status": HealthStatus.HEALTHY.value,
                    "message": f"All {len(models)} models available",
                    "details": {
                        "total_models": len(models),
                        "available_models": len(models),
                        "model_status": {m["name"]: m["available"] for m in models},
                    },
                }
                
        except Exception as e:
            return {
                "status": HealthStatus.ERROR.value,
                "message": f"Model availability check failed: {str(e)}",
            }
    
    async def _check_routing_logic(self) -> Dict[str, Any]:
        """Check routing logic functionality."""
        try:
            # Simulate routing logic test
            test_requests = [
                {"type": "code_generation", "complexity": "high"},
                {"type": "code_review", "complexity": "medium"},
                {"type": "debugging", "complexity": "low"},
            ]
            
            successful_routes = 0
            routing_results = []
            
            for request in test_requests:
                # Simulate routing decision
                try:
                    # This would normally call the actual routing logic
                    route_decision = self._simulate_routing_decision(request)
                    routing_results.append({
                        "request": request,
                        "route": route_decision,
                        "success": True
                    })
                    successful_routes += 1
                except Exception as e:
                    routing_results.append({
                        "request": request,
                        "error": str(e),
                        "success": False
                    })
            
            success_rate = successful_routes / len(test_requests)
            
            if success_rate == 1.0:
                status = HealthStatus.HEALTHY
            elif success_rate >= 0.8:
                status = HealthStatus.DEGRADED
            else:
                status = HealthStatus.UNHEALTHY
            
            return {
                "status": status.value,
                "message": f"Routing logic success rate: {success_rate:.1%}",
                "details": {
                    "total_requests": len(test_requests),
                    "successful_routes": successful_routes,
                    "success_rate": success_rate,
                    "routing_results": routing_results,
                },
            }
            
        except Exception as e:
            return {
                "status": HealthStatus.ERROR.value,
                "message": f"Routing logic check failed: {str(e)}",
            }
    
    def _simulate_routing_decision(self, request: Dict[str, Any]) -> str:
        """Simulate routing decision for testing."""
        # Simple simulation based on request type and complexity
        if request["type"] == "code_generation" and request["complexity"] == "high":
            return "claude-3-opus"
        elif request["type"] == "code_review":
            return "claude-3-sonnet"
        else:
            return "claude-3-haiku"
    
    async def _check_api_connectivity(self) -> Dict[str, Any]:
        """Check connectivity to external APIs."""
        try:
            # List of external endpoints to check
            endpoints = [
                {"name": "model_api", "url": "http://localhost:8001/health", "timeout": 5},
                {"name": "cache_api", "url": "http://localhost:6379", "timeout": 3},
                {"name": "metrics_api", "url": "http://localhost:9090", "timeout": 3},
            ]
            
            connectivity_results = []
            successful_connections = 0
            
            for endpoint in endpoints:
                try:
                    # Simulate connectivity check
                    result = await self._check_endpoint(endpoint["url"], endpoint["timeout"])
                    connectivity_results.append({
                        "endpoint": endpoint["name"],
                        "url": endpoint["url"],
                        "success": result["success"],
                        "response_time": result.get("response_time", 0),
                        "status_code": result.get("status_code"),
                    })
                    if result["success"]:
                        successful_connections += 1
                except Exception as e:
                    connectivity_results.append({
                        "endpoint": endpoint["name"],
                        "url": endpoint["url"],
                        "success": False,
                        "error": str(e),
                    })
            
            success_rate = successful_connections / len(endpoints)
            
            if success_rate == 1.0:
                status = HealthStatus.HEALTHY
            elif success_rate >= 0.7:
                status = HealthStatus.DEGRADED
            else:
                status = HealthStatus.UNHEALTHY
            
            return {
                "status": status.value,
                "message": f"API connectivity success rate: {success_rate:.1%}",
                "details": {
                    "total_endpoints": len(endpoints),
                    "successful_connections": successful_connections,
                    "success_rate": success_rate,
                    "connectivity_results": connectivity_results,
                },
            }
            
        except Exception as e:
            return {
                "status": HealthStatus.ERROR.value,
                "message": f"API connectivity check failed: {str(e)}",
            }
    
    async def _check_endpoint(self, url: str, timeout: int) -> Dict[str, Any]:
        """Check a specific endpoint."""
        # This would normally make an actual HTTP request
        # For simulation, we'll return a mock response
        await asyncio.sleep(0.1)  # Simulate network delay
        return {
            "success": True,
            "response_time": 100,  # milliseconds
            "status_code": 200,
        }
    
    async def _check_model_performance(self) -> Dict[str, Any]:
        """Check model performance metrics."""
        try:
            # Simulate performance metrics collection
            performance_metrics = {
                "claude-3-opus": {
                    "avg_response_time": 2.5,  # seconds
                    "success_rate": 0.98,
                    "token_throughput": 150,  # tokens/second
                },
                "claude-3-sonnet": {
                    "avg_response_time": 1.8,
                    "success_rate": 0.99,
                    "token_throughput": 200,
                },
                "claude-3-haiku": {
                    "avg_response_time": 0.8,
                    "success_rate": 0.995,
                    "token_throughput": 300,
                },
            }
            
            # Check performance thresholds
            performance_issues = []
            for model, metrics in performance_metrics.items():
                if metrics["avg_response_time"] > 5.0:
                    performance_issues.append(f"{model}: High response time")
                if metrics["success_rate"] < 0.95:
                    performance_issues.append(f"{model}: Low success rate")
                if metrics["token_throughput"] < 50:
                    performance_issues.append(f"{model}: Low token throughput")
            
            if performance_issues:
                status = HealthStatus.DEGRADED if len(performance_issues) <= 2 else HealthStatus.UNHEALTHY
                message = f"Performance issues detected: {len(performance_issues)} issues"
            else:
                status = HealthStatus.HEALTHY
                message = "All models performing within acceptable thresholds"
            
            return {
                "status": status.value,
                "message": message,
                "details": {
                    "performance_metrics": performance_metrics,
                    "performance_issues": performance_issues,
                    "thresholds": {
                        "max_response_time": 5.0,
                        "min_success_rate": 0.95,
                        "min_token_throughput": 50,
                    },
                },
            }
            
        except Exception as e:
            return {
                "status": HealthStatus.ERROR.value,
                "message": f"Model performance check failed: {str(e)}",
            }
    
    async def _check_cache_health(self) -> Dict[str, Any]:
        """Check cache system health."""
        try:
            # Simulate cache health check
            cache_metrics = {
                "hit_rate": 0.85,
                "memory_usage": 0.65,  # 65% of allocated memory
                "eviction_rate": 0.02,
                "avg_access_time": 0.001,  # milliseconds
                "total_entries": 10000,
            }
            
            # Check cache health thresholds
            issues = []
            if cache_metrics["hit_rate"] < 0.7:
                issues.append("Low cache hit rate")
            if cache_metrics["memory_usage"] > 0.9:
                issues.append("High memory usage")
            if cache_metrics["eviction_rate"] > 0.1:
                issues.append("High eviction rate")
            if cache_metrics["avg_access_time"] > 0.01:
                issues.append("Slow access time")
            
            if issues:
                status = HealthStatus.DEGRADED if len(issues) <= 2 else HealthStatus.UNHEALTHY
                message = f"Cache issues detected: {len(issues)} issues"
            else:
                status = HealthStatus.HEALTHY
                message = "Cache system healthy"
            
            return {
                "status": status.value,
                "message": message,
                "details": {
                    "cache_metrics": cache_metrics,
                    "issues": issues,
                    "thresholds": {
                        "min_hit_rate": 0.7,
                        "max_memory_usage": 0.9,
                        "max_eviction_rate": 0.1,
                        "max_access_time": 0.01,
                    },
                },
            }
            
        except Exception as e:
            return {
                "status": HealthStatus.ERROR.value,
                "message": f"Cache health check failed: {str(e)}",
            }
    
    async def _check_configuration_validity(self) -> Dict[str, Any]:
        """Check configuration validity."""
        try:
            # Simulate configuration validation
            config_checks = {
                "model_configs": {"valid": True, "issues": []},
                "routing_rules": {"valid": True, "issues": []},
                "api_endpoints": {"valid": True, "issues": []},
                "cache_settings": {"valid": True, "issues": []},
                "rate_limits": {"valid": True, "issues": []},
            }
            
            # Collect all issues
            all_issues = []
            for component, check in config_checks.items():
                all_issues.extend(check["issues"])
                if not check["valid"]:
                    all_issues.append(f"{component}: Invalid configuration")
            
            if all_issues:
                status = HealthStatus.DEGRADED if len(all_issues) <= 2 else HealthStatus.UNHEALTHY
                message = f"Configuration issues detected: {len(all_issues)} issues"
            else:
                status = HealthStatus.HEALTHY
                message = "All configurations valid"
            
            return {
                "status": status.value,
                "message": message,
                "details": {
                    "config_checks": config_checks,
                    "issues": all_issues,
                    "total_components": len(config_checks),
                },
            }
            
        except Exception as e:
            return {
                "status": HealthStatus.ERROR.value,
                "message": f"Configuration validity check failed: {str(e)}",
            }
    
    async def _check_rate_limiting(self) -> Dict[str, Any]:
        """Check rate limiting functionality."""
        try:
            # Simulate rate limiting check
            rate_limit_metrics = {
                "current_requests_per_second": 45,
                "max_requests_per_second": 100,
                "current_burst_size": 5,
                "max_burst_size": 10,
                "rejected_requests_last_minute": 2,
                "total_requests_last_minute": 200,
            }
            
            # Calculate metrics
            usage_rate = rate_limit_metrics["current_requests_per_second"] / rate_limit_metrics["max_requests_per_second"]
            rejection_rate = rate_limit_metrics["rejected_requests_last_minute"] / rate_limit_metrics["total_requests_last_minute"]
            
            issues = []
            if usage_rate > 0.9:
                issues.append("High request rate usage")
            if rejection_rate > 0.05:
                issues.append("High rejection rate")
            if rate_limit_metrics["current_burst_size"] > rate_limit_metrics["max_burst_size"] * 0.9:
                issues.append("High burst size")
            
            if issues:
                status = HealthStatus.DEGRADED if len(issues) <= 1 else HealthStatus.UNHEALTHY
                message = f"Rate limiting issues detected: {len(issues)} issues"
            else:
                status = HealthStatus.HEALTHY
                message = "Rate limiting functioning normally"
            
            return {
                "status": status.value,
                "message": message,
                "details": {
                    "rate_limit_metrics": rate_limit_metrics,
                    "calculated_metrics": {
                        "usage_rate": usage_rate,
                        "rejection_rate": rejection_rate,
                    },
                    "issues": issues,
                    "thresholds": {
                        "max_usage_rate": 0.9,
                        "max_rejection_rate": 0.05,
                        "max_burst_usage": 0.9,
                    },
                },
            }
            
        except Exception as e:
            return {
                "status": HealthStatus.ERROR.value,
                "message": f"Rate limiting check failed: {str(e)}",
            }
    
    async def run_all_checks(self) -> Dict[str, Any]:
        """Run all health checks and return comprehensive report."""
        return await self.base_checker.run_all_checks()
    
    async def run_liveness_checks(self) -> Dict[str, Any]:
        """Run liveness checks only."""
        results = await self.base_checker.run_checks_by_type(HealthCheckType.LIVENESS)
        return {
            "service": self.service_name,
            "check_type": "liveness",
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {name: result.to_dict() for name, result in results.items()},
        }
    
    async def run_readiness_checks(self) -> Dict[str, Any]:
        """Run readiness checks only."""
        results = await self.base_checker.run_checks_by_type(HealthCheckType.READINESS)
        return {
            "service": self.service_name,
            "check_type": "readiness",
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {name: result.to_dict() for name, result in results.items()},
        }
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Get health summary without running checks."""
        return self.base_checker.get_service_health_summary()


# Global instance
_model_router_health_checker: Optional[ModelRouterHealthChecker] = None


def get_model_router_health_checker() -> ModelRouterHealthChecker:
    """Get the global Model Router health checker."""
    global _model_router_health_checker
    if _model_router_health_checker is None:
        _model_router_health_checker = ModelRouterHealthChecker()
    return _model_router_health_checker


# Health check endpoints
async def model_router_liveness() -> Dict[str, Any]:
    """Model Router liveness endpoint."""
    checker = get_model_router_health_checker()
    return await checker.run_liveness_checks()


async def model_router_readiness() -> Dict[str, Any]:
    """Model Router readiness endpoint."""
    checker = get_model_router_health_checker()
    return await checker.run_readiness_checks()


async def model_router_health() -> Dict[str, Any]:
    """Model Router comprehensive health endpoint."""
    checker = get_model_router_health_checker()
    return await checker.run_all_checks()


# Decorated health checks for easy registration
@health_check("model_router_model_availability", HealthCheckType.BUSINESS_LOGIC, critical=True)
async def check_model_router_model_availability():
    """Check model availability for Model Router."""
    checker = get_model_router_health_checker()
    return await checker._check_model_availability()


@health_check("model_router_routing_logic", HealthCheckType.BUSINESS_LOGIC, critical=True)
async def check_model_router_routing_logic():
    """Check routing logic for Model Router."""
    checker = get_model_router_health_checker()
    return await checker._check_routing_logic()


@health_check("model_router_api_connectivity", HealthCheckType.DEPENDENCY, critical=True)
async def check_model_router_api_connectivity():
    """Check API connectivity for Model Router."""
    checker = get_model_router_health_checker()
    return await checker._check_api_connectivity()