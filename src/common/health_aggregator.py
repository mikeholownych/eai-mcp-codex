"""
Health Check Aggregation Service.
Provides centralized health check aggregation and monitoring for all MCP services.
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum

from .enhanced_health_check import HealthStatus
from .logging import get_logger
from .tracing import get_tracer
from .metrics import get_metrics_collector

logger = get_logger("health_aggregator")
tracer = get_tracer()
metrics = get_metrics_collector("health_aggregator")


class AggregationStatus(Enum):
    """Aggregation status levels."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    ERROR = "error"


@dataclass
class ServiceHealthSummary:
    """Summary of a service's health status."""
    service_name: str
    overall_status: str
    healthy_checks: int
    degraded_checks: int
    unhealthy_checks: int
    error_checks: int
    total_checks: int
    last_updated: str
    critical_issues: List[str]
    warnings: List[str]


@dataclass
class SystemHealthReport:
    """Comprehensive system health report."""
    timestamp: str
    overall_status: str
    total_services: int
    healthy_services: int
    degraded_services: int
    unhealthy_services: int
    error_services: int
    service_summaries: List[ServiceHealthSummary]
    system_issues: List[str]
    recommendations: List[str]
    uptime_percentage: float
    response_time_avg_ms: float


class HealthAggregator:
    """Aggregates health checks from all MCP services."""
    
    def __init__(self):
        self.service_endpoints = {
            "model-router": {
                "health": "http://model-router:8001/health",
                "liveness": "http://model-router:8001/health/liveness",
                "readiness": "http://model-router:8001/health/readiness"
            },
            "plan-management": {
                "health": "http://plan-management:8002/health",
                "liveness": "http://plan-management:8002/health/liveness",
                "readiness": "http://plan-management:8002/health/readiness"
            },
            "git-worktree": {
                "health": "http://git-worktree-manager:8003/health",
                "liveness": "http://git-worktree-manager:8003/health/liveness",
                "readiness": "http://git-worktree-manager:8003/health/readiness"
            },
            "workflow-orchestrator": {
                "health": "http://workflow-orchestrator:8004/health",
                "liveness": "http://workflow-orchestrator:8004/health/liveness",
                "readiness": "http://workflow-orchestrator:8004/health/readiness"
            },
            "verification-feedback": {
                "health": "http://verification-feedback:8005/health",
                "liveness": "http://verification-feedback:8005/health/liveness",
                "readiness": "http://verification-feedback:8005/health/readiness"
            }
        }
        
        self.health_history = []
        self.max_history_size = 100
        self.aggregation_timeout = 30.0  # seconds
        
        # Initialize metrics
        self._initialize_metrics()
    
    def _initialize_metrics(self):
        """Initialize health aggregation metrics."""
        metrics.register_gauge(
            "system_health_status",
            "Overall system health status (1=healthy, 2=degraded, 3=unhealthy, 4=error)",
            labels=["status"]
        )
        
        metrics.register_gauge(
            "service_health_status",
            "Individual service health status",
            labels=["service", "status"]
        )
        
        metrics.register_histogram(
            "health_aggregation_duration_seconds",
            "Time taken to aggregate health checks",
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0]
        )
        
        metrics.register_counter(
            "health_aggregation_errors_total",
            "Total number of health aggregation errors"
        )
    
    async def aggregate_all_health_checks(self) -> SystemHealthReport:
        """Aggregate health checks from all services."""
        start_time = datetime.utcnow()
        
        try:
            # Collect health data from all services
            service_health_data = await self._collect_all_service_health()
            
            # Generate service summaries
            service_summaries = self._generate_service_summaries(service_health_data)
            
            # Calculate overall system status
            overall_status = self._calculate_overall_status(service_summaries)
            
            # Generate system issues and recommendations
            system_issues, recommendations = self._generate_insights(service_summaries)
            
            # Calculate system metrics
            total_services = len(service_summaries)
            healthy_services = sum(1 for s in service_summaries if s.overall_status == HealthStatus.HEALTHY.value)
            degraded_services = sum(1 for s in service_summaries if s.overall_status == HealthStatus.DEGRADED.value)
            unhealthy_services = sum(1 for s in service_summaries if s.overall_status == HealthStatus.UNHEALTHY.value)
            error_services = sum(1 for s in service_summaries if s.overall_status == HealthStatus.ERROR.value)
            
            # Calculate uptime and response time
            uptime_percentage = self._calculate_uptime_percentage()
            response_time_avg_ms = self._calculate_average_response_time(service_health_data)
            
            # Create system health report
            report = SystemHealthReport(
                timestamp=datetime.utcnow().isoformat(),
                overall_status=overall_status.value,
                total_services=total_services,
                healthy_services=healthy_services,
                degraded_services=degraded_services,
                unhealthy_services=unhealthy_services,
                error_services=error_services,
                service_summaries=service_summaries,
                system_issues=system_issues,
                recommendations=recommendations,
                uptime_percentage=uptime_percentage,
                response_time_avg_ms=response_time_avg_ms
            )
            
            # Store in history
            self._store_in_history(report)
            
            # Update metrics
            self._update_metrics(report)
            
            # Log aggregation results
            duration = (datetime.utcnow() - start_time).total_seconds()
            metrics.histogram("health_aggregation_duration_seconds").observe(duration)
            
            logger.info(f"Health aggregation completed in {duration:.2f}s. "
                       f"Overall status: {overall_status.value}, "
                       f"Services: {healthy_services} healthy, {degraded_services} degraded, "
                       f"{unhealthy_services} unhealthy, {error_services} error")
            
            return report
            
        except Exception as e:
            metrics.counter("health_aggregation_errors_total").inc()
            logger.error(f"Health aggregation failed: {str(e)}")
            
            # Return error report
            return SystemHealthReport(
                timestamp=datetime.utcnow().isoformat(),
                overall_status=AggregationStatus.ERROR.value,
                total_services=len(self.service_endpoints),
                healthy_services=0,
                degraded_services=0,
                unhealthy_services=0,
                error_services=len(self.service_endpoints),
                service_summaries=[],
                system_issues=[f"Health aggregation failed: {str(e)}"],
                recommendations=["Check service connectivity and logs"],
                uptime_percentage=0.0,
                response_time_avg_ms=0.0
            )
    
    async def _collect_all_service_health(self) -> Dict[str, Dict[str, Any]]:
        """Collect health data from all services."""
        service_health_data = {}
        
        # Create tasks for all service health checks
        tasks = []
        for service_name, endpoints in self.service_endpoints.items():
            task = self._collect_service_health(service_name, endpoints)
            tasks.append(task)
        
        # Run all tasks concurrently with timeout
        try:
            results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=self.aggregation_timeout
            )
            
            # Process results
            for i, result in enumerate(results):
                service_name = list(self.service_endpoints.keys())[i]
                if isinstance(result, Exception):
                    logger.error(f"Failed to collect health data for {service_name}: {str(result)}")
                    service_health_data[service_name] = {
                        "error": str(result),
                        "status": AggregationStatus.ERROR.value,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                else:
                    service_health_data[service_name] = result
                    
        except asyncio.TimeoutError:
            logger.error("Health aggregation timed out")
            for service_name in self.service_endpoints.keys():
                if service_name not in service_health_data:
                    service_health_data[service_name] = {
                        "error": "Health check timeout",
                        "status": AggregationStatus.ERROR.value,
                        "timestamp": datetime.utcnow().isoformat()
                    }
        
        return service_health_data
    
    async def _collect_service_health(self, service_name: str, endpoints: Dict[str, str]) -> Dict[str, Any]:
        """Collect health data from a single service."""
        try:
            # Import httpx here to avoid import issues
            import httpx
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Try to get comprehensive health data first
                try:
                    response = await client.get(endpoints["health"])
                    if response.status_code == 200:
                        return response.json()
                except Exception as e:
                    logger.warning(f"Failed to get comprehensive health for {service_name}: {str(e)}")
                
                # Fall back to liveness check
                try:
                    response = await client.get(endpoints["liveness"])
                    if response.status_code == 200:
                        return {
                            "status": "alive",
                            "check_type": "liveness",
                            "timestamp": datetime.utcnow().isoformat(),
                            "checks": {"liveness": response.json()}
                        }
                except Exception as e:
                    logger.warning(f"Failed to get liveness for {service_name}: {str(e)}")
                
                # Fall back to readiness check
                try:
                    response = await client.get(endpoints["readiness"])
                    if response.status_code == 200:
                        return {
                            "status": "ready",
                            "check_type": "readiness",
                            "timestamp": datetime.utcnow().isoformat(),
                            "checks": {"readiness": response.json()}
                        }
                except Exception as e:
                    logger.warning(f"Failed to get readiness for {service_name}: {str(e)}")
                
                # All checks failed
                return {
                    "status": AggregationStatus.ERROR.value,
                    "error": "All health check endpoints failed",
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error collecting health data for {service_name}: {str(e)}")
            return {
                "status": AggregationStatus.ERROR.value,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def _generate_service_summaries(self, service_health_data: Dict[str, Dict[str, Any]]) -> List[ServiceHealthSummary]:
        """Generate service health summaries."""
        summaries = []
        
        for service_name, health_data in service_health_data.items():
            try:
                if "error" in health_data:
                    # Service health check failed
                    summary = ServiceHealthSummary(
                        service_name=service_name,
                        overall_status=AggregationStatus.ERROR.value,
                        healthy_checks=0,
                        degraded_checks=0,
                        unhealthy_checks=0,
                        error_checks=1,
                        total_checks=1,
                        last_updated=health_data.get("timestamp", datetime.utcnow().isoformat()),
                        critical_issues=[health_data["error"]],
                        warnings=[]
                    )
                else:
                    # Process health check results
                    checks = health_data.get("checks", {})
                    healthy = 0
                    degraded = 0
                    unhealthy = 0
                    error = 0
                    critical_issues = []
                    warnings = []
                    
                    for check_name, check_result in checks.items():
                        if isinstance(check_result, dict):
                            status = check_result.get("status", "unknown")
                            if status == HealthStatus.HEALTHY.value:
                                healthy += 1
                            elif status == HealthStatus.DEGRADED.value:
                                degraded += 1
                                warnings.append(f"{check_name} is degraded")
                            elif status == HealthStatus.UNHEALTHY.value:
                                unhealthy += 1
                                critical_issues.append(f"{check_name} is unhealthy")
                            else:
                                error += 1
                                critical_issues.append(f"{check_name} check failed")
                    
                    # Determine overall service status
                    if error > 0:
                        overall_status = AggregationStatus.ERROR.value
                    elif unhealthy > 0:
                        overall_status = AggregationStatus.UNHEALTHY.value
                    elif degraded > 0:
                        overall_status = AggregationStatus.DEGRADED.value
                    else:
                        overall_status = AggregationStatus.HEALTHY.value
                    
                    summary = ServiceHealthSummary(
                        service_name=service_name,
                        overall_status=overall_status,
                        healthy_checks=healthy,
                        degraded_checks=degraded,
                        unhealthy_checks=unhealthy,
                        error_checks=error,
                        total_checks=len(checks),
                        last_updated=health_data.get("timestamp", datetime.utcnow().isoformat()),
                        critical_issues=critical_issues,
                        warnings=warnings
                    )
                
                summaries.append(summary)
                
            except Exception as e:
                logger.error(f"Error generating summary for {service_name}: {str(e)}")
                summaries.append(ServiceHealthSummary(
                    service_name=service_name,
                    overall_status=AggregationStatus.ERROR.value,
                    healthy_checks=0,
                    degraded_checks=0,
                    unhealthy_checks=0,
                    error_checks=1,
                    total_checks=1,
                    last_updated=datetime.utcnow().isoformat(),
                    critical_issues=[f"Summary generation failed: {str(e)}"],
                    warnings=[]
                ))
        
        return summaries
    
    def _calculate_overall_status(self, service_summaries: List[ServiceHealthSummary]) -> AggregationStatus:
        """Calculate overall system status."""
        if not service_summaries:
            return AggregationStatus.ERROR
        
        error_count = sum(1 for s in service_summaries if s.overall_status == AggregationStatus.ERROR.value)
        unhealthy_count = sum(1 for s in service_summaries if s.overall_status == AggregationStatus.UNHEALTHY.value)
        degraded_count = sum(1 for s in service_summaries if s.overall_status == AggregationStatus.DEGRADED.value)
        
        total_services = len(service_summaries)
        
        if error_count > 0:
            return AggregationStatus.ERROR
        elif unhealthy_count > total_services * 0.3:  # More than 30% unhealthy
            return AggregationStatus.UNHEALTHY
        elif degraded_count > total_services * 0.5:  # More than 50% degraded
            return AggregationStatus.DEGRADED
        else:
            return AggregationStatus.HEALTHY
    
    def _generate_insights(self, service_summaries: List[ServiceHealthSummary]) -> tuple[List[str], List[str]]:
        """Generate system issues and recommendations."""
        system_issues = []
        recommendations = []
        
        # Check for critical issues
        for summary in service_summaries:
            if summary.overall_status == AggregationStatus.ERROR.value:
                system_issues.append(f"{summary.service_name} service is not responding")
                recommendations.append(f"Check {summary.service_name} service logs and restart if necessary")
            elif summary.overall_status == AggregationStatus.UNHEALTHY.value:
                system_issues.append(f"{summary.service_name} service has critical health issues")
                recommendations.append(f"Investigate {summary.service_name} critical issues immediately")
            elif summary.overall_status == AggregationStatus.DEGRADED.value:
                system_issues.append(f"{summary.service_name} service is running in degraded mode")
                recommendations.append(f"Monitor {summary.service_name} service and address warnings")
        
        # Check for patterns
        error_services = [s for s in service_summaries if s.overall_status == AggregationStatus.ERROR.value]
        if len(error_services) > 2:
            system_issues.append("Multiple services are not responding")
            recommendations.append("Check system-wide issues: network, infrastructure, or configuration")
        
        degraded_services = [s for s in service_summaries if s.overall_status == AggregationStatus.DEGRADED.value]
        if len(degraded_services) > len(service_summaries) * 0.6:
            system_issues.append("System-wide performance degradation detected")
            recommendations.append("Check resource utilization and load balancing")
        
        # Add general recommendations
        if not system_issues:
            recommendations.append("System is healthy. Continue monitoring.")
        else:
            recommendations.append("Review system logs for detailed error information.")
            recommendations.append("Consider enabling additional monitoring and alerting.")
        
        return system_issues, recommendations
    
    def _calculate_uptime_percentage(self) -> float:
        """Calculate system uptime percentage based on health history."""
        if not self.health_history:
            return 100.0
        
        # Look at last 24 hours of data
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        recent_history = [h for h in self.health_history 
                         if datetime.fromisoformat(h.timestamp) > cutoff_time]
        
        if not recent_history:
            return 100.0
        
        healthy_count = sum(1 for h in recent_history 
                          if h.overall_status == AggregationStatus.HEALTHY.value)
        
        return (healthy_count / len(recent_history)) * 100.0
    
    def _calculate_average_response_time(self, service_health_data: Dict[str, Dict[str, Any]]) -> float:
        """Calculate average response time across all services."""
        response_times = []
        
        for health_data in service_health_data.values():
            if "checks" in health_data:
                for check_result in health_data["checks"].values():
                    if isinstance(check_result, dict) and "duration_ms" in check_result:
                        response_times.append(check_result["duration_ms"])
        
        if not response_times:
            return 0.0
        
        return sum(response_times) / len(response_times)
    
    def _store_in_history(self, report: SystemHealthReport):
        """Store health report in history."""
        self.health_history.append(report)
        
        # Limit history size
        if len(self.health_history) > self.max_history_size:
            self.health_history = self.health_history[-self.max_history_size:]
    
    def _update_metrics(self, report: SystemHealthReport):
        """Update metrics with health report data."""
        # Update system health status
        metrics.gauge("system_health_status").labels(status=report.overall_status).set(
            1 if report.overall_status == AggregationStatus.HEALTHY.value
            else 2 if report.overall_status == AggregationStatus.DEGRADED.value
            else 3 if report.overall_status == AggregationStatus.UNHEALTHY.value
            else 4
        )
        
        # Update individual service health status
        for summary in report.service_summaries:
            metrics.gauge("service_health_status").labels(
                service=summary.service_name,
                status=summary.overall_status
            ).set(
                1 if summary.overall_status == AggregationStatus.HEALTHY.value
                else 2 if summary.overall_status == AggregationStatus.DEGRADED.value
                else 3 if summary.overall_status == AggregationStatus.UNHEALTHY.value
                else 4
            )
    
    def get_health_history(self, hours: int = 24) -> List[SystemHealthReport]:
        """Get health history for the specified number of hours."""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        return [h for h in self.health_history 
                if datetime.fromisoformat(h.timestamp) > cutoff_time]
    
    def get_service_health_trend(self, service_name: str, hours: int = 24) -> List[Dict[str, Any]]:
        """Get health trend for a specific service."""
        history = self.get_health_history(hours)
        trend = []
        
        for report in history:
            for summary in report.service_summaries:
                if summary.service_name == service_name:
                    trend.append({
                        "timestamp": report.timestamp,
                        "status": summary.overall_status,
                        "healthy_checks": summary.healthy_checks,
                        "degraded_checks": summary.degraded_checks,
                        "unhealthy_checks": summary.unhealthy_checks,
                        "error_checks": summary.error_checks
                    })
                    break
        
        return trend
    
    def get_system_health_summary(self) -> Dict[str, Any]:
        """Get current system health summary."""
        if not self.health_history:
            return {"status": "unknown", "message": "No health data available"}
        
        latest_report = self.health_history[-1]
        
        return {
            "status": latest_report.overall_status,
            "timestamp": latest_report.timestamp,
            "total_services": latest_report.total_services,
            "healthy_services": latest_report.healthy_services,
            "degraded_services": latest_report.degraded_services,
            "unhealthy_services": latest_report.unhealthy_services,
            "error_services": latest_report.error_services,
            "uptime_percentage": latest_report.uptime_percentage,
            "system_issues_count": len(latest_report.system_issues),
            "recommendations_count": len(latest_report.recommendations)
        }


# Global instance
_health_aggregator: Optional[HealthAggregator] = None


def get_health_aggregator() -> HealthAggregator:
    """Get the global health aggregator."""
    global _health_aggregator
    if _health_aggregator is None:
        _health_aggregator = HealthAggregator()
    return _health_aggregator


# Health aggregation endpoints
async def get_system_health() -> Dict[str, Any]:
    """Get comprehensive system health report."""
    aggregator = get_health_aggregator()
    report = await aggregator.aggregate_all_health_checks()
    return asdict(report)


async def get_service_health(service_name: str) -> Dict[str, Any]:
    """Get health report for a specific service."""
    aggregator = get_health_aggregator()
    
    if service_name not in aggregator.service_endpoints:
        return {"error": f"Service {service_name} not found"}
    
    # Get current health data
    health_data = await aggregator._collect_service_health(
        service_name, 
        aggregator.service_endpoints[service_name]
    )
    
    # Generate summary
    summaries = aggregator._generate_service_summaries({service_name: health_data})
    
    if summaries:
        return asdict(summaries[0])
    else:
        return {"error": f"Failed to generate health summary for {service_name}"}


async def get_health_history(hours: int = 24) -> Dict[str, Any]:
    """Get health history for the specified number of hours."""
    aggregator = get_health_aggregator()
    history = aggregator.get_health_history(hours)
    
    return {
        "hours": hours,
        "reports": [asdict(report) for report in history]
    }


async def get_service_health_trend(service_name: str, hours: int = 24) -> Dict[str, Any]:
    """Get health trend for a specific service."""
    aggregator = get_health_aggregator()
    trend = aggregator.get_service_health_trend(service_name, hours)
    
    return {
        "service": service_name,
        "hours": hours,
        "trend": trend
    }


async def get_system_health_summary() -> Dict[str, Any]:
    """Get current system health summary."""
    aggregator = get_health_aggregator()
    return aggregator.get_system_health_summary()