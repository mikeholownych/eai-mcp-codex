"""API routes for continuous quality monitoring."""

from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from datetime import datetime

from .quality_monitor import (
    quality_monitor,
    Metric,
    MetricType,
    AlertSeverity,
    QualityThreshold,
)
from ..common.logging import get_logger

router = APIRouter(prefix="/monitoring", tags=["quality-monitoring"])
logger = get_logger("monitoring_routes")


class CustomMetricRequest(BaseModel):
    """Request model for adding custom metrics."""

    name: str
    metric_type: str
    value: float
    unit: str
    tags: List[str] = []
    metadata: Dict[str, Any] = {}


class ThresholdConfigRequest(BaseModel):
    """Request model for configuring quality thresholds."""

    metric_type: str
    warning_threshold: float
    critical_threshold: float
    evaluation_window_minutes: int = 5
    minimum_samples: int = 3
    comparison_operator: str = "greater_than"


class AlertActionRequest(BaseModel):
    """Request model for alert actions."""

    alert_id: str
    action: str  # "acknowledge" or "resolve"


@router.get("/status", response_model=Dict[str, Any])
async def get_monitoring_status() -> Dict[str, Any]:
    """Get current quality monitoring status."""
    try:
        status = await quality_monitor.get_current_status()
        return {
            "monitoring_status": status,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "active" if status["monitoring_enabled"] else "inactive",
        }

    except Exception as e:
        logger.error(f"Failed to get monitoring status: {e}")
        raise HTTPException(
            status_code=500, detail=f"Status retrieval failed: {str(e)}"
        )


@router.post("/start")
async def start_monitoring(background_tasks: BackgroundTasks) -> Dict[str, Any]:
    """Start continuous quality monitoring."""
    try:
        if quality_monitor.monitoring_enabled:
            return {
                "message": "Monitoring is already running",
                "status": "already_active",
            }

        # Start monitoring in background
        background_tasks.add_task(quality_monitor.start_monitoring)

        logger.info("Quality monitoring started")

        return {
            "message": "Quality monitoring started successfully",
            "monitoring_interval": quality_monitor.monitoring_interval,
            "report_interval": quality_monitor.report_generation_interval,
            "status": "started",
        }

    except Exception as e:
        logger.error(f"Failed to start monitoring: {e}")
        raise HTTPException(
            status_code=500, detail=f"Monitoring start failed: {str(e)}"
        )


@router.post("/stop")
async def stop_monitoring() -> Dict[str, Any]:
    """Stop continuous quality monitoring."""
    try:
        quality_monitor.stop_monitoring()

        logger.info("Quality monitoring stopped")

        return {
            "message": "Quality monitoring stopped successfully",
            "status": "stopped",
        }

    except Exception as e:
        logger.error(f"Failed to stop monitoring: {e}")
        raise HTTPException(status_code=500, detail=f"Monitoring stop failed: {str(e)}")


@router.get("/dashboard", response_model=Dict[str, Any])
async def get_quality_dashboard() -> Dict[str, Any]:
    """Get comprehensive quality dashboard data."""
    try:
        dashboard_data = await quality_monitor.get_quality_dashboard()
        return {
            "dashboard": dashboard_data,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "retrieved",
        }

    except Exception as e:
        logger.error(f"Failed to get dashboard data: {e}")
        raise HTTPException(
            status_code=500, detail=f"Dashboard retrieval failed: {str(e)}"
        )


@router.get("/metrics", response_model=Dict[str, Any])
async def get_recent_metrics(
    metric_type: Optional[str] = None, hours: int = 24
) -> Dict[str, Any]:
    """Get recent metrics, optionally filtered by type."""
    try:
        # Convert metric type string to enum if provided
        metric_type_enum = None
        if metric_type:
            try:
                metric_type_enum = MetricType(metric_type.lower())
            except ValueError:
                raise HTTPException(
                    status_code=400, detail=f"Invalid metric type: {metric_type}"
                )

        # Get metrics
        metrics = quality_monitor.metric_collector.get_recent_metrics(
            metric_type=metric_type_enum, hours=hours
        )

        # Convert to serializable format
        metrics_data = []
        for metric in metrics:
            metrics_data.append(
                {
                    "metric_id": metric.metric_id,
                    "metric_type": metric.metric_type.value,
                    "name": metric.name,
                    "value": metric.value,
                    "unit": metric.unit,
                    "timestamp": metric.timestamp.isoformat(),
                    "tags": metric.tags,
                    "metadata": metric.metadata,
                }
            )

        return {
            "metrics": metrics_data,
            "total_count": len(metrics_data),
            "filter_applied": {"metric_type": metric_type, "hours": hours},
            "timestamp": datetime.utcnow().isoformat(),
            "status": "retrieved",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get metrics: {e}")
        raise HTTPException(
            status_code=500, detail=f"Metrics retrieval failed: {str(e)}"
        )


@router.post("/metrics/custom")
async def add_custom_metric(request: CustomMetricRequest) -> Dict[str, Any]:
    """Add custom metric to monitoring system."""
    try:
        # Convert metric type string to enum
        try:
            metric_type_enum = MetricType(request.metric_type.lower())
        except ValueError:
            raise HTTPException(
                status_code=400, detail=f"Invalid metric type: {request.metric_type}"
            )

        # Create metric
        metric = Metric(
            metric_id=f"custom_{request.name}_{datetime.utcnow().timestamp()}",
            metric_type=metric_type_enum,
            name=request.name,
            value=request.value,
            unit=request.unit,
            tags=request.tags + ["custom"],
            metadata=request.metadata,
        )

        # Add to monitoring system
        quality_monitor.add_custom_metric(metric)

        logger.info(f"Added custom metric: {request.name}")

        return {
            "message": f"Custom metric '{request.name}' added successfully",
            "metric_id": metric.metric_id,
            "status": "added",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to add custom metric: {e}")
        raise HTTPException(
            status_code=500, detail=f"Custom metric addition failed: {str(e)}"
        )


@router.get("/alerts", response_model=Dict[str, Any])
async def get_active_alerts(severity: Optional[str] = None) -> Dict[str, Any]:
    """Get active quality alerts."""
    try:
        # Convert severity string to enum if provided
        severity_enum = None
        if severity:
            try:
                severity_enum = AlertSeverity(severity.lower())
            except ValueError:
                raise HTTPException(
                    status_code=400, detail=f"Invalid severity level: {severity}"
                )

        # Get alerts
        alerts = quality_monitor.alert_manager.get_active_alerts(severity_enum)

        # Convert to serializable format
        alerts_data = []
        for alert in alerts:
            alerts_data.append(
                {
                    "alert_id": alert.alert_id,
                    "severity": alert.severity.value,
                    "metric_type": alert.metric_type.value,
                    "message": alert.message,
                    "current_value": alert.current_value,
                    "threshold_value": alert.threshold_value,
                    "triggered_at": alert.triggered_at.isoformat(),
                    "resolved_at": (
                        alert.resolved_at.isoformat() if alert.resolved_at else None
                    ),
                    "acknowledged": alert.acknowledged,
                    "metadata": alert.metadata,
                }
            )

        return {
            "alerts": alerts_data,
            "total_count": len(alerts_data),
            "filter_applied": {"severity": severity},
            "timestamp": datetime.utcnow().isoformat(),
            "status": "retrieved",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get alerts: {e}")
        raise HTTPException(
            status_code=500, detail=f"Alerts retrieval failed: {str(e)}"
        )


@router.post("/alerts/action")
async def handle_alert_action(request: AlertActionRequest) -> Dict[str, Any]:
    """Handle alert actions (acknowledge or resolve)."""
    try:
        if request.action == "acknowledge":
            success = await quality_monitor.alert_manager.acknowledge_alert(
                request.alert_id
            )
            action_name = "acknowledged"
        elif request.action == "resolve":
            success = await quality_monitor.alert_manager.resolve_alert(
                request.alert_id
            )
            action_name = "resolved"
        else:
            raise HTTPException(
                status_code=400, detail=f"Invalid action: {request.action}"
            )

        if success:
            return {
                "message": f"Alert {request.alert_id} {action_name} successfully",
                "alert_id": request.alert_id,
                "action": request.action,
                "status": "success",
            }
        else:
            raise HTTPException(
                status_code=404, detail="Alert not found or already resolved"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to handle alert action: {e}")
        raise HTTPException(status_code=500, detail=f"Alert action failed: {str(e)}")


@router.get("/thresholds", response_model=Dict[str, Any])
async def get_quality_thresholds() -> Dict[str, Any]:
    """Get current quality thresholds configuration."""
    try:
        thresholds_data = {}

        for (
            metric_type,
            threshold,
        ) in quality_monitor.quality_analyzer.thresholds.items():
            thresholds_data[metric_type.value] = {
                "warning_threshold": threshold.warning_threshold,
                "critical_threshold": threshold.critical_threshold,
                "evaluation_window_minutes": threshold.evaluation_window_minutes,
                "minimum_samples": threshold.minimum_samples,
                "comparison_operator": threshold.comparison_operator,
            }

        return {
            "thresholds": thresholds_data,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "retrieved",
        }

    except Exception as e:
        logger.error(f"Failed to get thresholds: {e}")
        raise HTTPException(
            status_code=500, detail=f"Thresholds retrieval failed: {str(e)}"
        )


@router.post("/thresholds/configure")
async def configure_threshold(request: ThresholdConfigRequest) -> Dict[str, Any]:
    """Configure quality threshold for a metric type."""
    try:
        # Convert metric type string to enum
        try:
            metric_type_enum = MetricType(request.metric_type.lower())
        except ValueError:
            raise HTTPException(
                status_code=400, detail=f"Invalid metric type: {request.metric_type}"
            )

        # Validate comparison operator
        valid_operators = ["greater_than", "less_than", "equals"]
        if request.comparison_operator not in valid_operators:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid comparison operator: {request.comparison_operator}",
            )

        # Create threshold configuration
        threshold = QualityThreshold(
            metric_type=metric_type_enum,
            warning_threshold=request.warning_threshold,
            critical_threshold=request.critical_threshold,
            evaluation_window_minutes=request.evaluation_window_minutes,
            minimum_samples=request.minimum_samples,
            comparison_operator=request.comparison_operator,
        )

        # Update threshold in analyzer
        quality_monitor.quality_analyzer.thresholds[metric_type_enum] = threshold

        logger.info(f"Configured threshold for {request.metric_type}")

        return {
            "message": f"Threshold configured for {request.metric_type}",
            "metric_type": request.metric_type,
            "configuration": {
                "warning_threshold": request.warning_threshold,
                "critical_threshold": request.critical_threshold,
                "evaluation_window_minutes": request.evaluation_window_minutes,
                "comparison_operator": request.comparison_operator,
            },
            "status": "configured",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to configure threshold: {e}")
        raise HTTPException(
            status_code=500, detail=f"Threshold configuration failed: {str(e)}"
        )


@router.get("/reports", response_model=Dict[str, Any])
async def get_quality_reports(limit: int = 10) -> Dict[str, Any]:
    """Get recent quality reports."""
    try:
        reports = quality_monitor.reports[-limit:] if quality_monitor.reports else []

        # Convert to serializable format
        reports_data = []
        for report in reports:
            reports_data.append(
                {
                    "report_id": report.report_id,
                    "period_start": report.period_start.isoformat(),
                    "period_end": report.period_end.isoformat(),
                    "overall_score": report.overall_score,
                    "status": report.status.value,
                    "active_alerts_count": len(report.active_alerts),
                    "recommendations_count": len(report.recommendations),
                    "generated_at": report.generated_at.isoformat(),
                }
            )

        return {
            "reports": reports_data,
            "total_available": len(quality_monitor.reports),
            "limit_applied": limit,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "retrieved",
        }

    except Exception as e:
        logger.error(f"Failed to get reports: {e}")
        raise HTTPException(
            status_code=500, detail=f"Reports retrieval failed: {str(e)}"
        )


@router.get("/reports/{report_id}", response_model=Dict[str, Any])
async def get_quality_report_details(report_id: str) -> Dict[str, Any]:
    """Get detailed quality report by ID."""
    try:
        # Find report by ID
        report = None
        for r in quality_monitor.reports:
            if r.report_id == report_id:
                report = r
                break

        if not report:
            raise HTTPException(status_code=404, detail="Report not found")

        # Convert metric summaries to serializable format
        metric_summaries_data = {}
        for metric_type, summary in report.metric_summaries.items():
            metric_summaries_data[metric_type.value] = summary

        # Convert trends to serializable format
        trends_data = {}
        for metric_type, trend in report.trends.items():
            trends_data[metric_type.value] = trend

        return {
            "report": {
                "report_id": report.report_id,
                "period_start": report.period_start.isoformat(),
                "period_end": report.period_end.isoformat(),
                "overall_score": report.overall_score,
                "status": report.status.value,
                "metric_summaries": metric_summaries_data,
                "trends": trends_data,
                "recommendations": report.recommendations,
                "active_alerts_count": len(report.active_alerts),
                "generated_at": report.generated_at.isoformat(),
            },
            "timestamp": datetime.utcnow().isoformat(),
            "status": "retrieved",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get report details: {e}")
        raise HTTPException(
            status_code=500, detail=f"Report details retrieval failed: {str(e)}"
        )


@router.get("/health", response_model=Dict[str, Any])
async def get_monitoring_health() -> Dict[str, Any]:
    """Get health status of the monitoring system itself."""
    try:
        current_status = await quality_monitor.get_current_status()

        # Check system health indicators
        health_indicators = {
            "monitoring_active": quality_monitor.monitoring_enabled,
            "metric_collection": len(
                quality_monitor.metric_collector.get_recent_metrics(hours=1)
            )
            > 0,
            "alert_system": len(quality_monitor.alert_manager.notification_handlers)
            > 0,
            "report_generation": len(quality_monitor.reports) > 0,
        }

        overall_health = all(health_indicators.values())

        return {
            "monitoring_health": {
                "overall_status": "healthy" if overall_health else "degraded",
                "components": health_indicators,
                "current_quality_score": current_status.get("quality_score", 0),
                "active_alerts": current_status.get("active_alerts", 0),
                "uptime": (
                    "continuous" if quality_monitor.monitoring_enabled else "stopped"
                ),
            },
            "timestamp": datetime.utcnow().isoformat(),
            "status": "healthy" if overall_health else "degraded",
        }

    except Exception as e:
        logger.error(f"Failed to get monitoring health: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@router.get("/supported-metrics", response_model=Dict[str, Any])
async def get_supported_metrics() -> Dict[str, Any]:
    """Get list of supported metric types and alert severities."""
    return {
        "metric_types": [metric_type.value for metric_type in MetricType],
        "alert_severities": [severity.value for severity in AlertSeverity],
        "comparison_operators": ["greater_than", "less_than", "equals"],
        "default_units": {
            "performance": "milliseconds",
            "reliability": "percent",
            "accuracy": "percent",
            "resource_usage": "percent",
            "error_rate": "percent",
            "latency": "milliseconds",
            "throughput": "requests_per_second",
            "user_satisfaction": "rating",
            "code_quality": "score",
            "security": "score",
        },
        "status": "retrieved",
    }
