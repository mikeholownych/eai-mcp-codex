import asyncio

from src.monitoring.quality_monitor import AlertManager, AlertSeverity
from src.monitoring.metrics_definitions import MetricType


def test_trend_alert_generation() -> None:
    manager = AlertManager()
    trends = {MetricType.LATENCY: "degrading", MetricType.ACCURACY: "improving"}
    alerts = asyncio.run(manager.check_trends(trends))
    assert len(alerts) == 1
    alert = alerts[0]
    assert alert.metric_type is MetricType.LATENCY
    assert alert.severity is AlertSeverity.MEDIUM
