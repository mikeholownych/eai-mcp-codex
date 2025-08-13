"""
Health Check Service Application.
Provides comprehensive health check endpoints and monitoring for all MCP services.
"""

from typing import Dict, Any, Optional
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from pydantic import BaseModel, Field

from src.common.enhanced_health_check import HealthStatus
from src.common.health_aggregator import get_health_aggregator
from src.common.health_monitoring import (
    get_health_monitor,
    AlertRule,
    AlertSeverity,
    AlertType,
)
from src.common.health_check_testing import (
    get_health_check_tester,
    get_health_check_performance_tester,
)
from src.common.logging import get_logger, setup_logging
from src.common.tracing import get_tracer, TracingConfig, InstrumentationManager
from src.common.metrics import get_metrics_collector

# Initialize logging and tracing
logger = get_logger("health_service")
tracer = get_tracer()
metrics = get_metrics_collector("health_service")


# Request/Response models
class HealthCheckRequest(BaseModel):
    """Health check request model."""
    service_name: Optional[str] = Field(None, description="Service name to check")
    check_type: Optional[str] = Field(None, description="Type of health check to run")


class AlertRuleRequest(BaseModel):
    """Alert rule request model."""
    name: str = Field(..., description="Rule name")
    enabled: bool = Field(True, description="Whether the rule is enabled")
    condition: str = Field(..., description="Alert condition")
    severity: str = Field(..., description="Alert severity")
    alert_type: str = Field(..., description="Alert type")
    threshold: float = Field(..., description="Alert threshold")
    duration: int = Field(..., description="Alert duration in seconds")
    services: list[str] = Field(default_factory=list, description="Services to monitor")
    notification_channels: list[str] = Field(default_factory=list, description="Notification channels")


class TestRequest(BaseModel):
    """Test request model."""
    suite_name: Optional[str] = Field(None, description="Test suite to run")
    iterations: Optional[int] = Field(100, description="Number of test iterations")
    concurrent_requests: Optional[int] = Field(50, description="Number of concurrent requests")


# Global variables
health_monitor = None
tracing_config = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting Health Check Service")
    
    # Initialize tracing
    global tracing_config
    tracing_config = TracingConfig()
    tracing_config.initialize("health-service")
    
    # Initialize health monitoring
    global health_monitor
    health_monitor = get_health_monitor()
    
    # Start monitoring
    await health_monitor.start_monitoring()
    
    # Log startup
    logger.info("Health Check Service started successfully")
    
    yield
    
    # Cleanup
    logger.info("Shutting down Health Check Service")


# Create FastAPI app
app = FastAPI(
    title="MCP Health Check Service",
    description="Comprehensive health check and monitoring service for MCP services",
    version="1.0.0",
    lifespan=lifespan
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]
)

# Instrument FastAPI app
instrumentation_manager = InstrumentationManager(tracing_config)
instrumentation_manager.instrument_fastapi(app)


# Health check endpoints
@app.get("/health", response_model=Dict[str, Any])
async def health_check():
    """Comprehensive health check endpoint."""
    try:
        aggregator = get_health_aggregator()
        return await aggregator.aggregate_all_health_checks()
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@app.get("/health/liveness", response_model=Dict[str, Any])
async def liveness_check():
    """Liveness check endpoint."""
    return {
        "service": "health-service",
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {
            "liveness": {
                "status": HealthStatus.HEALTHY.value,
                "message": "Service is alive"
            }
        }
    }


@app.get("/health/readiness", response_model=Dict[str, Any])
async def readiness_check():
    """Readiness check endpoint."""
    try:
        # Check if monitoring is running
        monitor = get_health_monitor()
        monitoring_status = monitor.get_monitoring_status()
        
        if monitoring_status.get("monitoring_active"):
            status = HealthStatus.HEALTHY.value
            message = "Service is ready"
        else:
            status = HealthStatus.DEGRADED.value
            message = "Service is starting up"
        
        return {
            "service": "health-service",
            "status": status,
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {
                "readiness": {
                    "status": status,
                    "message": message
                },
                "monitoring": monitoring_status
            }
        }
    except Exception as e:
        logger.error(f"Readiness check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Readiness check failed: {str(e)}")


@app.get("/health/service/{service_name}", response_model=Dict[str, Any])
async def service_health_check(service_name: str):
    """Get health check for a specific service."""
    try:
        aggregator = get_health_aggregator()
        return await aggregator.get_service_health(service_name)
    except Exception as e:
        logger.error(f"Service health check failed for {service_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Service health check failed: {str(e)}")


# Health aggregation endpoints
@app.get("/health/system", response_model=Dict[str, Any])
async def system_health():
    """Get system health summary."""
    try:
        aggregator = get_health_aggregator()
        return await aggregator.get_system_health_summary()
    except Exception as e:
        logger.error(f"System health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"System health check failed: {str(e)}")


@app.get("/health/history", response_model=Dict[str, Any])
async def health_history(hours: int = 24):
    """Get health history."""
    try:
        aggregator = get_health_aggregator()
        return await aggregator.get_health_history(hours)
    except Exception as e:
        logger.error(f"Health history failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Health history failed: {str(e)}")


@app.get("/health/trend/{service_name}", response_model=Dict[str, Any])
async def health_trend(service_name: str, hours: int = 24):
    """Get health trend for a service."""
    try:
        aggregator = get_health_aggregator()
        return await aggregator.get_service_health_trend(service_name, hours)
    except Exception as e:
        logger.error(f"Health trend failed for {service_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Health trend failed: {str(e)}")


# Alert management endpoints
@app.get("/alerts", response_model=Dict[str, Any])
async def get_alerts(severity: Optional[str] = None, alert_type: Optional[str] = None):
    """Get active alerts."""
    try:
        monitor = get_health_monitor()
        return await monitor.get_active_alerts(severity=severity, alert_type=alert_type)
    except Exception as e:
        logger.error(f"Failed to get alerts: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get alerts: {str(e)}")


@app.get("/alerts/history", response_model=Dict[str, Any])
async def get_alert_history(hours: int = 24):
    """Get alert history."""
    try:
        monitor = get_health_monitor()
        return await monitor.get_alert_history(hours)
    except Exception as e:
        logger.error(f"Failed to get alert history: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get alert history: {str(e)}")


@app.get("/alerts/rules", response_model=Dict[str, Any])
async def get_alert_rules():
    """Get alert rules."""
    try:
        monitor = get_health_monitor()
        return await monitor.get_alert_rules()
    except Exception as e:
        logger.error(f"Failed to get alert rules: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get alert rules: {str(e)}")


@app.post("/alerts/rules", response_model=Dict[str, Any])
async def add_alert_rule(rule: AlertRuleRequest):
    """Add a new alert rule."""
    try:
        monitor = get_health_monitor()
        
        alert_rule = AlertRule(
            name=rule.name,
            enabled=rule.enabled,
            condition=rule.condition,
            severity=AlertSeverity(rule.severity),
            alert_type=AlertType(rule.alert_type),
            threshold=rule.threshold,
            duration=rule.duration,
            services=rule.services,
            notification_channels=rule.notification_channels
        )
        
        success = monitor.add_alert_rule(alert_rule)
        
        if success:
            return {"success": True, "message": f"Alert rule '{rule.name}' added successfully"}
        else:
            return {"success": False, "message": f"Alert rule '{rule.name}' already exists"}
    except Exception as e:
        logger.error(f"Failed to add alert rule: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to add alert rule: {str(e)}")


@app.put("/alerts/rules/{rule_name}", response_model=Dict[str, Any])
async def update_alert_rule(rule_name: str, updates: Dict[str, Any]):
    """Update an alert rule."""
    try:
        monitor = get_health_monitor()
        success = monitor.update_alert_rule(rule_name, updates)
        
        if success:
            return {"success": True, "message": f"Alert rule '{rule_name}' updated successfully"}
        else:
            return {"success": False, "message": f"Alert rule '{rule_name}' not found"}
    except Exception as e:
        logger.error(f"Failed to update alert rule: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update alert rule: {str(e)}")


@app.delete("/alerts/rules/{rule_name}", response_model=Dict[str, Any])
async def delete_alert_rule(rule_name: str):
    """Delete an alert rule."""
    try:
        monitor = get_health_monitor()
        success = monitor.remove_alert_rule(rule_name)
        
        if success:
            return {"success": True, "message": f"Alert rule '{rule_name}' deleted successfully"}
        else:
            return {"success": False, "message": f"Alert rule '{rule_name}' not found"}
    except Exception as e:
        logger.error(f"Failed to delete alert rule: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete alert rule: {str(e)}")


# Testing endpoints
@app.post("/tests/run", response_model=Dict[str, Any])
async def run_tests(request: TestRequest, background_tasks: BackgroundTasks):
    """Run health check tests."""
    try:
        tester = get_health_check_tester()
        
        if request.suite_name:
            # Run specific test suite
            background_tasks.add_task(tester.run_test_suite, request.suite_name)
            return {"message": f"Test suite '{request.suite_name}' started"}
        else:
            # Run all test suites
            background_tasks.add_task(tester.run_all_test_suites)
            return {"message": "All test suites started"}
    except Exception as e:
        logger.error(f"Failed to run tests: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to run tests: {str(e)}")


@app.get("/tests/results", response_model=Dict[str, Any])
async def get_test_results_endpoint(suite_name: Optional[str] = None):
    """Get test results."""
    try:
        from src.common.health_check_testing import get_test_results as _get_results
        return await _get_results(suite_name)
    except Exception as e:
        logger.error(f"Failed to get test results: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get test results: {str(e)}")


@app.get("/tests/summary", response_model=Dict[str, Any])
async def get_test_summary_endpoint():
    """Get test summary."""
    try:
        from src.common.health_check_testing import get_test_summary as _get_summary
        return await _get_summary()
    except Exception as e:
        logger.error(f"Failed to get test summary: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get test summary: {str(e)}")


@app.post("/tests/benchmark", response_model=Dict[str, Any])
async def benchmark_health_check(request: TestRequest):
    """Benchmark health check performance."""
    try:
        performance_tester = get_health_check_performance_tester()
        
        # Create a simple health check function for benchmarking
        async def simple_health_check():
            aggregator = get_health_aggregator()
            return await aggregator.get_system_health_summary()
        
        result = await performance_tester.benchmark_health_check(
            simple_health_check,
            iterations=request.iterations
        )
        
        return result
    except Exception as e:
        logger.error(f"Benchmark failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Benchmark failed: {str(e)}")


@app.post("/tests/load", response_model=Dict[str, Any])
async def load_test_health_aggregator(request: TestRequest):
    """Load test health aggregator."""
    try:
        performance_tester = get_health_check_performance_tester()
        aggregator = get_health_aggregator()
        
        result = await performance_tester.load_test_health_aggregator(
            aggregator,
            concurrent_requests=request.concurrent_requests
        )
        
        return result
    except Exception as e:
        logger.error(f"Load test failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Load test failed: {str(e)}")


# Monitoring status endpoints
@app.get("/monitoring/status", response_model=Dict[str, Any])
async def monitoring_status():
    """Get monitoring status."""
    try:
        monitor = get_health_monitor()
        return monitor.get_monitoring_status()
    except Exception as e:
        logger.error(f"Failed to get monitoring status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get monitoring status: {str(e)}")


# Metrics endpoint for Prometheus
@app.get("/metrics")
async def metrics_endpoint():
    """Prometheus metrics endpoint."""
    try:
        # This would typically integrate with a Prometheus client library
        # For now, return a simple metrics response
        return {
            "service": "health-service",
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": {
                "health_checks_total": 0,
                "alerts_total": 0,
                "monitoring_uptime_seconds": 0
            }
        }
    except Exception as e:
        logger.error(f"Failed to get metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")


# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions."""
    logger.error(f"HTTP exception: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "timestamp": datetime.utcnow().isoformat()}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions."""
    logger.error(f"Unexpected error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "timestamp": datetime.utcnow().isoformat()}
    )


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "MCP Health Check Service",
        "version": "1.0.0",
        "description": "Comprehensive health check and monitoring service for MCP services",
        "endpoints": {
            "health": "/health",
            "liveness": "/health/liveness",
            "readiness": "/health/readiness",
            "system_health": "/health/system",
            "alerts": "/alerts",
            "tests": "/tests/run",
            "monitoring": "/monitoring/status",
            "metrics": "/metrics"
        },
        "timestamp": datetime.utcnow().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    
    # Setup logging
    setup_logging()
    
    # Run the application
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8006,
        reload=True,
        log_level="info"
    )