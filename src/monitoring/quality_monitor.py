"""Continuous Quality Monitoring for Real-time System Health and Performance."""

import asyncio
import time
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
import psutil

from ..common.logging import get_logger
from .metrics_definitions import Metric, MetricType
from .slo_manager import SLOManager, SLOResult

logger = get_logger("quality_monitor")


class AlertSeverity(str, Enum):
    """Alert severity levels."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class QualityStatus(str, Enum):
    """Overall quality status."""

    EXCELLENT = "excellent"
    GOOD = "good"
    ACCEPTABLE = "acceptable"
    POOR = "poor"
    CRITICAL = "critical"


@dataclass
class QualityThreshold:
    """Quality threshold configuration."""

    metric_type: MetricType
    warning_threshold: float
    critical_threshold: float
    evaluation_window_minutes: int = 5
    minimum_samples: int = 3
    comparison_operator: str = "greater_than"  # greater_than, less_than, equals


@dataclass
class QualityAlert:
    """Quality alert notification."""

    alert_id: str
    severity: AlertSeverity
    metric_type: MetricType
    message: str
    current_value: float
    threshold_value: float
    triggered_at: datetime = field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    acknowledged: bool = False


@dataclass
class QualityReport:
    """Comprehensive quality report."""

    report_id: str
    period_start: datetime
    period_end: datetime
    overall_score: float
    status: QualityStatus
    metric_summaries: Dict[MetricType, Dict[str, float]]
    active_alerts: List[QualityAlert]
    trends: Dict[MetricType, str]  # "improving", "stable", "degrading"
    slo_results: List[SLOResult] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    generated_at: datetime = field(default_factory=datetime.utcnow)


class MetricCollector:
    """Collects metrics from various system components."""

    def __init__(self):
        self.metrics_buffer: deque = deque(maxlen=10000)
        self.collection_interval = 30.0  # seconds
        self.is_collecting = False

    async def start_collection(self):
        """Start continuous metric collection."""
        self.is_collecting = True
        logger.info("Starting continuous metric collection")

        while self.is_collecting:
            try:
                await self._collect_all_metrics()
                await asyncio.sleep(self.collection_interval)
            except Exception as e:
                logger.error(f"Metric collection error: {e}")
                await asyncio.sleep(self.collection_interval * 2)

    def stop_collection(self):
        """Stop metric collection."""
        self.is_collecting = False
        logger.info("Stopping metric collection")

    async def _collect_all_metrics(self):
        """Collect all types of metrics."""
        # System performance metrics
        await self._collect_system_metrics()

        # Application performance metrics
        await self._collect_application_metrics()

        # Quality metrics
        await self._collect_quality_metrics()

        logger.debug(
            f"Collected metrics batch. Buffer size: {len(self.metrics_buffer)}"
        )

    async def _collect_system_metrics(self):
        """Collect system-level metrics."""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            self._add_metric(
                Metric(
                    metric_id=f"cpu_usage_{time.time()}",
                    metric_type=MetricType.RESOURCE_USAGE,
                    name="cpu_usage",
                    value=cpu_percent,
                    unit="percent",
                    tags=["system", "cpu"],
                )
            )

            # Memory usage
            memory = psutil.virtual_memory()
            self._add_metric(
                Metric(
                    metric_id=f"memory_usage_{time.time()}",
                    metric_type=MetricType.RESOURCE_USAGE,
                    name="memory_usage",
                    value=memory.percent,
                    unit="percent",
                    tags=["system", "memory"],
                )
            )

            # Disk usage
            disk = psutil.disk_usage("/")
            disk_percent = (disk.used / disk.total) * 100
            self._add_metric(
                Metric(
                    metric_id=f"disk_usage_{time.time()}",
                    metric_type=MetricType.RESOURCE_USAGE,
                    name="disk_usage",
                    value=disk_percent,
                    unit="percent",
                    tags=["system", "disk"],
                )
            )

            # Network IO
            network = psutil.net_io_counters()
            self._add_metric(
                Metric(
                    metric_id=f"network_bytes_sent_{time.time()}",
                    metric_type=MetricType.THROUGHPUT,
                    name="network_bytes_sent",
                    value=float(network.bytes_sent),
                    unit="bytes",
                    tags=["system", "network"],
                )
            )

        except Exception as e:
            logger.error(f"System metrics collection failed: {e}")

    async def _collect_application_metrics(self):
        """Collect application-level metrics."""
        try:
            # Mock application metrics - in production, these would come from actual services

            # Model router performance
            self._add_metric(
                Metric(
                    metric_id=f"model_response_time_{time.time()}",
                    metric_type=MetricType.LATENCY,
                    name="model_response_time",
                    value=150.0 + (time.time() % 100),  # Mock latency
                    unit="milliseconds",
                    tags=["application", "model_router"],
                )
            )

            # Plan execution success rate
            self._add_metric(
                Metric(
                    metric_id=f"plan_success_rate_{time.time()}",
                    metric_type=MetricType.RELIABILITY,
                    name="plan_success_rate",
                    value=95.0 + (time.time() % 5),  # Mock success rate
                    unit="percent",
                    tags=["application", "plan_execution"],
                )
            )

            # API request rate
            self._add_metric(
                Metric(
                    metric_id=f"api_request_rate_{time.time()}",
                    metric_type=MetricType.THROUGHPUT,
                    name="api_request_rate",
                    value=25.0 + (time.time() % 10),  # Mock request rate
                    unit="requests_per_second",
                    tags=["application", "api"],
                )
            )

        except Exception as e:
            logger.error(f"Application metrics collection failed: {e}")

    async def _collect_quality_metrics(self):
        """Collect quality-specific metrics."""
        try:
            # Code quality score (mock)
            self._add_metric(
                Metric(
                    metric_id=f"code_quality_score_{time.time()}",
                    metric_type=MetricType.CODE_QUALITY,
                    name="code_quality_score",
                    value=85.0 + (time.time() % 10),  # Mock score
                    unit="score",
                    tags=["quality", "code"],
                )
            )

            # User satisfaction (mock)
            self._add_metric(
                Metric(
                    metric_id=f"user_satisfaction_{time.time()}",
                    metric_type=MetricType.USER_SATISFACTION,
                    name="user_satisfaction",
                    value=4.2 + (time.time() % 0.8),  # Mock rating
                    unit="rating",
                    tags=["quality", "user_experience"],
                )
            )

            # Security score (mock)
            self._add_metric(
                Metric(
                    metric_id=f"security_score_{time.time()}",
                    metric_type=MetricType.SECURITY,
                    name="security_score",
                    value=90.0 + (time.time() % 8),  # Mock score
                    unit="score",
                    tags=["quality", "security"],
                )
            )

        except Exception as e:
            logger.error(f"Quality metrics collection failed: {e}")

    def _add_metric(self, metric: Metric):
        """Add metric to buffer."""
        self.metrics_buffer.append(metric)

    def get_recent_metrics(
        self, metric_type: Optional[MetricType] = None, hours: int = 24
    ) -> List[Metric]:
        """Get recent metrics, optionally filtered by type."""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)

        filtered_metrics = []
        for metric in self.metrics_buffer:
            if metric.timestamp >= cutoff_time:
                if metric_type is None or metric.metric_type == metric_type:
                    filtered_metrics.append(metric)

        return filtered_metrics


class QualityAnalyzer:
    """Analyzes collected metrics to determine quality status."""

    def __init__(self):
        self.thresholds: Dict[MetricType, QualityThreshold] = (
            self._get_default_thresholds()
        )
        self.analysis_cache: Dict[str, Any] = {}

    def _get_default_thresholds(self) -> Dict[MetricType, QualityThreshold]:
        """Get default quality thresholds."""
        return {
            MetricType.PERFORMANCE: QualityThreshold(
                metric_type=MetricType.PERFORMANCE,
                warning_threshold=1000.0,  # 1 second
                critical_threshold=5000.0,  # 5 seconds
                comparison_operator="greater_than",
            ),
            MetricType.RELIABILITY: QualityThreshold(
                metric_type=MetricType.RELIABILITY,
                warning_threshold=95.0,
                critical_threshold=90.0,
                comparison_operator="less_than",
            ),
            MetricType.ERROR_RATE: QualityThreshold(
                metric_type=MetricType.ERROR_RATE,
                warning_threshold=5.0,
                critical_threshold=10.0,
                comparison_operator="greater_than",
            ),
            MetricType.RESOURCE_USAGE: QualityThreshold(
                metric_type=MetricType.RESOURCE_USAGE,
                warning_threshold=80.0,
                critical_threshold=95.0,
                comparison_operator="greater_than",
            ),
            MetricType.LATENCY: QualityThreshold(
                metric_type=MetricType.LATENCY,
                warning_threshold=500.0,  # 500ms
                critical_threshold=2000.0,  # 2s
                comparison_operator="greater_than",
            ),
        }

    async def analyze_metrics(
        self, metrics: List[Metric]
    ) -> Dict[MetricType, Dict[str, float]]:
        """Analyze metrics and calculate summaries."""
        summaries = {}

        # Group metrics by type
        grouped_metrics = defaultdict(list)
        for metric in metrics:
            grouped_metrics[metric.metric_type].append(metric)

        for metric_type, type_metrics in grouped_metrics.items():
            values = [m.value for m in type_metrics]

            if values:
                summary = {
                    "mean": statistics.mean(values),
                    "median": statistics.median(values),
                    "min": min(values),
                    "max": max(values),
                    "count": len(values),
                    "current": values[-1] if values else 0.0,
                }

                if len(values) > 1:
                    summary["std_dev"] = statistics.stdev(values)
                else:
                    summary["std_dev"] = 0.0

                summaries[metric_type] = summary

        return summaries

    async def calculate_quality_score(
        self, metric_summaries: Dict[MetricType, Dict[str, float]]
    ) -> float:
        """Calculate overall quality score."""
        if not metric_summaries:
            return 0.0

        total_score = 0.0
        total_weight = 0.0

        # Weights for different metric types
        weights = {
            MetricType.PERFORMANCE: 0.25,
            MetricType.RELIABILITY: 0.25,
            MetricType.ACCURACY: 0.20,
            MetricType.RESOURCE_USAGE: 0.15,
            MetricType.ERROR_RATE: 0.15,
        }

        for metric_type, summary in metric_summaries.items():
            weight = weights.get(metric_type, 0.1)
            current_value = summary.get("current", 0.0)

            # Calculate score based on metric type
            if metric_type == MetricType.RELIABILITY:
                score = min(100.0, current_value)  # Higher is better
            elif metric_type == MetricType.ERROR_RATE:
                score = max(0.0, 100.0 - current_value)  # Lower is better
            elif metric_type == MetricType.RESOURCE_USAGE:
                score = max(0.0, 100.0 - current_value)  # Lower is better
            elif metric_type == MetricType.LATENCY:
                # Convert latency to score (lower is better)
                if current_value <= 100:
                    score = 100.0
                elif current_value <= 500:
                    score = 90.0
                elif current_value <= 1000:
                    score = 70.0
                elif current_value <= 2000:
                    score = 50.0
                else:
                    score = 20.0
            else:
                # Default scoring
                score = min(100.0, max(0.0, current_value))

            total_score += score * weight
            total_weight += weight

        return total_score / total_weight if total_weight > 0 else 0.0

    def determine_quality_status(self, quality_score: float) -> QualityStatus:
        """Determine quality status from score."""
        if quality_score >= 90:
            return QualityStatus.EXCELLENT
        elif quality_score >= 80:
            return QualityStatus.GOOD
        elif quality_score >= 70:
            return QualityStatus.ACCEPTABLE
        elif quality_score >= 50:
            return QualityStatus.POOR
        else:
            return QualityStatus.CRITICAL

    async def analyze_trends(
        self, metrics: List[Metric], hours: int = 24
    ) -> Dict[MetricType, str]:
        """Analyze metric trends over time."""
        trends = {}

        # Group metrics by type
        grouped_metrics = defaultdict(list)
        for metric in metrics:
            grouped_metrics[metric.metric_type].append(metric)

        for metric_type, type_metrics in grouped_metrics.items():
            if len(type_metrics) < 3:
                trends[metric_type] = "insufficient_data"
                continue

            # Sort by timestamp
            type_metrics.sort(key=lambda m: m.timestamp)

            # Calculate trend over time
            values = [m.value for m in type_metrics]

            # Simple linear trend analysis
            if len(values) >= 5:
                # Compare first and last quartiles
                first_quarter = statistics.mean(values[: len(values) // 4])
                last_quarter = statistics.mean(values[-len(values) // 4 :])

                change_percent = (
                    ((last_quarter - first_quarter) / first_quarter * 100)
                    if first_quarter != 0
                    else 0
                )

                if abs(change_percent) < 5:
                    trends[metric_type] = "stable"
                elif change_percent > 5:
                    if metric_type in [MetricType.RELIABILITY, MetricType.ACCURACY]:
                        trends[metric_type] = "improving"
                    else:
                        trends[metric_type] = "degrading"
                else:
                    if metric_type in [MetricType.RELIABILITY, MetricType.ACCURACY]:
                        trends[metric_type] = "degrading"
                    else:
                        trends[metric_type] = "improving"
            else:
                trends[metric_type] = "stable"

        return trends


class AlertManager:
    """Manages quality alerts and notifications."""

    def __init__(self):
        self.active_alerts: List[QualityAlert] = []
        self.alert_history: List[QualityAlert] = []
        self.notification_handlers: List[Callable] = []

    def add_notification_handler(self, handler: Callable):
        """Add notification handler for alerts."""
        self.notification_handlers.append(handler)
        logger.info("Added notification handler")

    async def check_thresholds(
        self,
        metric_summaries: Dict[MetricType, Dict[str, float]],
        thresholds: Dict[MetricType, QualityThreshold],
    ) -> List[QualityAlert]:
        """Check metrics against thresholds and generate alerts."""
        new_alerts = []

        for metric_type, summary in metric_summaries.items():
            threshold = thresholds.get(metric_type)
            if not threshold:
                continue

            current_value = summary.get("current", 0.0)

            # Check thresholds
            alert_severity = None
            threshold_value = None

            if self._exceeds_threshold(
                current_value,
                threshold.critical_threshold,
                threshold.comparison_operator,
            ):
                alert_severity = AlertSeverity.CRITICAL
                threshold_value = threshold.critical_threshold
            elif self._exceeds_threshold(
                current_value,
                threshold.warning_threshold,
                threshold.comparison_operator,
            ):
                alert_severity = AlertSeverity.HIGH
                threshold_value = threshold.warning_threshold

            if alert_severity:
                # Check if similar alert already exists
                existing_alert = self._find_existing_alert(metric_type, alert_severity)
                if not existing_alert:
                    alert = QualityAlert(
                        alert_id=f"alert_{metric_type.value}_{time.time()}",
                        severity=alert_severity,
                        metric_type=metric_type,
                        message=f"{metric_type.value} {threshold.comparison_operator} threshold: {current_value:.2f} {threshold.comparison_operator} {threshold_value:.2f}",
                        current_value=current_value,
                        threshold_value=threshold_value,
                        metadata={"summary": summary},
                    )

                    new_alerts.append(alert)
                    self.active_alerts.append(alert)

                    # Send notifications
                    await self._send_notifications(alert)

        return new_alerts

    async def check_trends(self, trends: Dict[MetricType, str]) -> List[QualityAlert]:
        """Generate alerts for degrading metric trends."""
        new_alerts: List[QualityAlert] = []
        for metric_type, trend in trends.items():
            if trend != "degrading":
                continue

            existing_alert = self._find_existing_alert(
                metric_type, AlertSeverity.MEDIUM
            )
            if existing_alert:
                continue

            alert = QualityAlert(
                alert_id=f"trend_{metric_type.value}_{time.time()}",
                severity=AlertSeverity.MEDIUM,
                metric_type=metric_type,
                message=f"{metric_type.value} trend degrading",
                current_value=0.0,
                threshold_value=0.0,
                metadata={"trend": trend},
            )
            new_alerts.append(alert)
            self.active_alerts.append(alert)
            await self._send_notifications(alert)

        return new_alerts

    def _exceeds_threshold(self, value: float, threshold: float, operator: str) -> bool:
        """Check if value exceeds threshold based on operator."""
        if operator == "greater_than":
            return value > threshold
        elif operator == "less_than":
            return value < threshold
        elif operator == "equals":
            return abs(value - threshold) < 0.001
        return False

    def _find_existing_alert(
        self, metric_type: MetricType, severity: AlertSeverity
    ) -> Optional[QualityAlert]:
        """Find existing unresolved alert for metric type and severity."""
        for alert in self.active_alerts:
            if (
                alert.metric_type == metric_type
                and alert.severity == severity
                and alert.resolved_at is None
            ):
                return alert
        return None

    async def _send_notifications(self, alert: QualityAlert):
        """Send alert notifications to registered handlers."""
        for handler in self.notification_handlers:
            try:
                await handler(alert)
            except Exception as e:
                logger.error(f"Notification handler failed: {e}")

    async def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an active alert."""
        for alert in self.active_alerts:
            if alert.alert_id == alert_id and alert.resolved_at is None:
                alert.resolved_at = datetime.utcnow()
                self.alert_history.append(alert)
                self.active_alerts.remove(alert)
                logger.info(f"Resolved alert: {alert_id}")
                return True
        return False

    async def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge an alert."""
        for alert in self.active_alerts:
            if alert.alert_id == alert_id:
                alert.acknowledged = True
                logger.info(f"Acknowledged alert: {alert_id}")
                return True
        return False

    def get_active_alerts(
        self, severity: Optional[AlertSeverity] = None
    ) -> List[QualityAlert]:
        """Get active alerts, optionally filtered by severity."""
        if severity:
            return [alert for alert in self.active_alerts if alert.severity == severity]
        return self.active_alerts.copy()


class ContinuousQualityMonitor:
    """Main continuous quality monitoring system."""

    def __init__(self):
        self.metric_collector = MetricCollector()
        self.quality_analyzer = QualityAnalyzer()
        self.alert_manager = AlertManager()
        self.slo_manager = SLOManager()

        self.monitoring_enabled = False
        self.monitoring_interval = 60.0  # seconds
        self.report_generation_interval = 3600.0  # 1 hour

        self.reports: List[QualityReport] = []

    async def start_monitoring(self):
        """Start continuous quality monitoring."""
        if self.monitoring_enabled:
            logger.warning("Monitoring already started")
            return

        self.monitoring_enabled = True
        logger.info("Starting continuous quality monitoring")

        # Start metric collection
        collection_task = asyncio.create_task(self.metric_collector.start_collection())

        # Start monitoring loop
        monitoring_task = asyncio.create_task(self._monitoring_loop())

        # Start report generation
        report_task = asyncio.create_task(self._report_generation_loop())

        await asyncio.gather(
            collection_task, monitoring_task, report_task, return_exceptions=True
        )

    def stop_monitoring(self):
        """Stop continuous quality monitoring."""
        self.monitoring_enabled = False
        self.metric_collector.stop_collection()
        logger.info("Stopped continuous quality monitoring")

    async def _monitoring_loop(self):
        """Main monitoring loop."""
        while self.monitoring_enabled:
            try:
                await self._perform_quality_check()
                await asyncio.sleep(self.monitoring_interval)
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                await asyncio.sleep(self.monitoring_interval * 2)

    async def _report_generation_loop(self):
        """Generate periodic quality reports."""
        while self.monitoring_enabled:
            try:
                await self._generate_quality_report()
                await asyncio.sleep(self.report_generation_interval)
            except Exception as e:
                logger.error(f"Report generation error: {e}")
                await asyncio.sleep(self.report_generation_interval)

    async def _perform_quality_check(self):
        """Perform quality check and alert generation."""
        # Get recent metrics
        recent_metrics = self.metric_collector.get_recent_metrics(hours=1)

        if not recent_metrics:
            logger.debug("No recent metrics available for quality check")
            return

        # Analyze metrics
        metric_summaries = await self.quality_analyzer.analyze_metrics(recent_metrics)

        # Detect metric trends
        trends = await self.quality_analyzer.analyze_trends(recent_metrics)

        # Generate trend alerts
        trend_alerts = await self.alert_manager.check_trends(trends)

        # Check thresholds and generate alerts
        new_alerts = await self.alert_manager.check_thresholds(
            metric_summaries, self.quality_analyzer.thresholds
        )

        total_new = len(new_alerts) + len(trend_alerts)
        if total_new:
            logger.warning(f"Generated {total_new} new quality alerts")

        logger.debug(f"Quality check completed. Analyzed {len(recent_metrics)} metrics")

    async def _generate_quality_report(self):
        """Generate comprehensive quality report."""
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=24)

        # Get metrics for the period
        metrics = self.metric_collector.get_recent_metrics(hours=24)

        if not metrics:
            logger.warning("No metrics available for report generation")
            return

        # Analyze metrics
        metric_summaries = await self.quality_analyzer.analyze_metrics(metrics)

        # Calculate quality score
        quality_score = await self.quality_analyzer.calculate_quality_score(
            metric_summaries
        )

        # Determine status
        status = self.quality_analyzer.determine_quality_status(quality_score)

        # Analyze trends
        trends = await self.quality_analyzer.analyze_trends(metrics)

        # Evaluate SLOs
        slo_results = self.slo_manager.evaluate_slos(metrics)

        # Generate recommendations
        recommendations = self._generate_recommendations(
            metric_summaries, trends, quality_score
        )

        # Create report
        report = QualityReport(
            report_id=f"report_{int(time.time())}",
            period_start=start_time,
            period_end=end_time,
            overall_score=quality_score,
            status=status,
            metric_summaries=metric_summaries,
            active_alerts=self.alert_manager.get_active_alerts(),
            trends=trends,
            slo_results=slo_results,
            recommendations=recommendations,
        )

        self.reports.append(report)

        # Keep only last 100 reports
        if len(self.reports) > 100:
            self.reports = self.reports[-100:]

        logger.info(
            f"Generated quality report: {report.report_id} (Score: {quality_score:.1f}, Status: {status.value})"
        )

    def _generate_recommendations(
        self,
        metric_summaries: Dict[MetricType, Dict[str, float]],
        trends: Dict[MetricType, str],
        quality_score: float,
    ) -> List[str]:
        """Generate actionable recommendations based on analysis."""
        recommendations = []

        # Score-based recommendations
        if quality_score < 70:
            recommendations.append(
                "Quality score is below acceptable level - immediate attention required"
            )
        elif quality_score < 80:
            recommendations.append(
                "Quality score has room for improvement - consider optimization"
            )

        # Metric-specific recommendations
        for metric_type, summary in metric_summaries.items():
            current_value = summary.get("current", 0.0)

            if metric_type == MetricType.RESOURCE_USAGE and current_value > 85:
                recommendations.append(
                    f"High {metric_type.value}: Consider scaling resources or optimizing usage"
                )
            elif metric_type == MetricType.LATENCY and current_value > 1000:  # 1 second
                recommendations.append(
                    "High latency detected: Investigate performance bottlenecks"
                )
            elif metric_type == MetricType.ERROR_RATE and current_value > 5:
                recommendations.append(
                    "Error rate is elevated: Review logs and fix underlying issues"
                )
            elif metric_type == MetricType.RELIABILITY and current_value < 95:
                recommendations.append(
                    "Reliability below target: Implement fault tolerance improvements"
                )

        # Trend-based recommendations
        for metric_type, trend in trends.items():
            if trend == "degrading":
                recommendations.append(
                    f"{metric_type.value} is degrading: Monitor closely and investigate root cause"
                )

        # Alert-based recommendations
        critical_alerts = self.alert_manager.get_active_alerts(AlertSeverity.CRITICAL)
        if critical_alerts:
            recommendations.append(
                f"Address {len(critical_alerts)} critical alerts immediately"
            )

        high_alerts = self.alert_manager.get_active_alerts(AlertSeverity.HIGH)
        if high_alerts:
            recommendations.append(
                f"Review and resolve {len(high_alerts)} high-priority alerts"
            )

        return recommendations

    async def get_current_status(self) -> Dict[str, Any]:
        """Get current quality monitoring status."""
        recent_metrics = self.metric_collector.get_recent_metrics(hours=1)
        metric_summaries = await self.quality_analyzer.analyze_metrics(recent_metrics)
        quality_score = await self.quality_analyzer.calculate_quality_score(
            metric_summaries
        )
        status = self.quality_analyzer.determine_quality_status(quality_score)
        slo_results = self.slo_manager.evaluate_slos(recent_metrics)

        return {
            "monitoring_enabled": self.monitoring_enabled,
            "quality_score": round(quality_score, 2),
            "status": status.value,
            "active_alerts": len(self.alert_manager.get_active_alerts()),
            "critical_alerts": len(
                self.alert_manager.get_active_alerts(AlertSeverity.CRITICAL)
            ),
            "metrics_collected": len(recent_metrics),
            "slo_compliance": {res.slo.name: res.met for res in slo_results},
            "last_report": self.reports[-1].report_id if self.reports else None,
            "uptime_hours": "continuous" if self.monitoring_enabled else "stopped",
        }

    async def get_quality_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive quality dashboard data."""
        recent_metrics = self.metric_collector.get_recent_metrics(hours=24)
        metric_summaries = await self.quality_analyzer.analyze_metrics(recent_metrics)
        quality_score = await self.quality_analyzer.calculate_quality_score(
            metric_summaries
        )
        trends = await self.quality_analyzer.analyze_trends(recent_metrics)

        slo_results = self.slo_manager.evaluate_slos(recent_metrics)

        # Get metric trends for charts
        metric_trends = {}
        for metric_type in MetricType:
            type_metrics = [m for m in recent_metrics if m.metric_type == metric_type]
            if type_metrics:
                # Sort by timestamp and get last 20 points
                type_metrics.sort(key=lambda m: m.timestamp)
                metric_trends[metric_type.value] = [
                    {"timestamp": m.timestamp.isoformat(), "value": m.value}
                    for m in type_metrics[-20:]
                ]

        return {
            "overview": {
                "quality_score": round(quality_score, 2),
                "status": self.quality_analyzer.determine_quality_status(
                    quality_score
                ).value,
                "total_metrics": len(recent_metrics),
                "active_alerts": len(self.alert_manager.get_active_alerts()),
                "monitoring_uptime": "24/7" if self.monitoring_enabled else "offline",
            },
            "metric_summaries": {
                metric_type.value: summary
                for metric_type, summary in metric_summaries.items()
            },
            "trends": {
                metric_type.value: trend for metric_type, trend in trends.items()
            },
            "metric_trends": metric_trends,
            "slo_results": [
                {
                    "name": res.slo.name,
                    "met": res.met,
                    "percentage": res.percentage,
                }
                for res in slo_results
            ],
            "alerts": [
                {
                    "alert_id": alert.alert_id,
                    "severity": alert.severity.value,
                    "metric_type": alert.metric_type.value,
                    "message": alert.message,
                    "triggered_at": alert.triggered_at.isoformat(),
                    "acknowledged": alert.acknowledged,
                }
                for alert in self.alert_manager.get_active_alerts()
            ],
            "latest_report": (
                {
                    "report_id": self.reports[-1].report_id,
                    "overall_score": self.reports[-1].overall_score,
                    "status": self.reports[-1].status.value,
                    "recommendations_count": len(self.reports[-1].recommendations),
                    "generated_at": self.reports[-1].generated_at.isoformat(),
                }
                if self.reports
                else None
            ),
        }

    def add_custom_metric(self, metric: Metric):
        """Add custom metric from external source."""
        self.metric_collector._add_metric(metric)
        logger.debug(f"Added custom metric: {metric.name}")

    def register_alert_handler(self, handler: Callable):
        """Register custom alert notification handler."""
        self.alert_manager.add_notification_handler(handler)


# Default notification handlers
async def log_alert_handler(alert: QualityAlert):
    """Default alert handler that logs alerts."""
    logger.warning(f"QUALITY ALERT [{alert.severity.value.upper()}]: {alert.message}")


async def console_alert_handler(alert: QualityAlert):
    """Alert handler that prints to console."""
    print(f"🚨 QUALITY ALERT: {alert.message} (Severity: {alert.severity.value})")


# Global instance
quality_monitor = ContinuousQualityMonitor()

# Register default handlers
quality_monitor.register_alert_handler(log_alert_handler)
quality_monitor.register_alert_handler(console_alert_handler)
