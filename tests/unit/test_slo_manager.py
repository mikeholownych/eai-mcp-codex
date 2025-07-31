from datetime import datetime, timedelta

from src.monitoring.slo_manager import SLOManager, SLO
from src.monitoring.metrics_definitions import Metric, MetricType


def test_slo_evaluation() -> None:
    mgr = SLOManager()
    slo = SLO(
        name="latency",
        metric_type=MetricType.LATENCY,
        threshold=100.0,
        comparison="less_than",
        target_percentage=90.0,
        window_minutes=60,
    )
    mgr.add_slo(slo)

    now = datetime.utcnow()
    metrics = [
        Metric(
            metric_id=f"m{i}",
            metric_type=MetricType.LATENCY,
            name="latency",
            value=50.0 if i < 9 else 150.0,
            unit="ms",
            timestamp=now - timedelta(minutes=5),
            metadata={},
            tags=[],
        )
        for i in range(10)
    ]

    results = mgr.evaluate_slos(metrics)
    assert len(results) == 1
    res = results[0]
    assert res.met is True
    assert res.percentage == 90.0
