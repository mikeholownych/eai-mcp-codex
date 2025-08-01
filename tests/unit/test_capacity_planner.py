from datetime import datetime, timedelta

from src.analytics.capacity_planner import CapacityPlanner
from src.monitoring.metrics_definitions import Metric, MetricType


def test_capacity_forecast() -> None:
    planner = CapacityPlanner()
    now = datetime.utcnow()
    metrics = [
        Metric(
            metric_id="cpu1",
            metric_type=MetricType.RESOURCE_USAGE,
            name="cpu_usage",
            value=50.0,
            unit="percent",
            timestamp=now - timedelta(hours=1),
            metadata={},
            tags=["system", "cpu"],
        ),
        Metric(
            metric_id="mem1",
            metric_type=MetricType.RESOURCE_USAGE,
            name="memory_usage",
            value=60.0,
            unit="percent",
            timestamp=now - timedelta(hours=1),
            metadata={},
            tags=["system", "memory"],
        ),
    ]

    estimate = planner.forecast(metrics)
    assert 49.0 < estimate.cpu_percent < 51.0
    assert 59.0 < estimate.memory_percent < 61.0
