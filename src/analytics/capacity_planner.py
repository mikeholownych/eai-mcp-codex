from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List

from ..common.logging import get_logger
from ..monitoring.metrics_definitions import Metric, MetricType

logger = get_logger("capacity_planner")


@dataclass
class CapacityEstimate:
    """Represents a capacity forecast."""

    timestamp: datetime
    cpu_percent: float
    memory_percent: float


class CapacityPlanner:
    """Simple capacity forecasting based on historical metrics."""

    def __init__(self, window_hours: int = 24) -> None:
        self.window_hours = window_hours
        self.estimates: List[CapacityEstimate] = []

    def forecast(self, metrics: List[Metric]) -> CapacityEstimate:
        """Generate a capacity forecast from recent metrics."""
        cutoff = datetime.utcnow() - timedelta(hours=self.window_hours)
        cpu = [
            m.value
            for m in metrics
            if m.metric_type is MetricType.RESOURCE_USAGE
            and "cpu" in m.tags
            and m.timestamp >= cutoff
        ]
        mem = [
            m.value
            for m in metrics
            if m.metric_type is MetricType.RESOURCE_USAGE
            and "memory" in m.tags
            and m.timestamp >= cutoff
        ]

        avg_cpu = sum(cpu) / len(cpu) if cpu else 0.0
        avg_mem = sum(mem) / len(mem) if mem else 0.0

        estimate = CapacityEstimate(
            timestamp=datetime.utcnow(), cpu_percent=avg_cpu, memory_percent=avg_mem
        )
        self.estimates.append(estimate)
        logger.debug("Generated capacity estimate %s", estimate)
        return estimate
