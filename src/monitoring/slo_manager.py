"""Service Level Objective management utilities."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List

from .quality_monitor import Metric, MetricType
from ..common.logging import get_logger

logger = get_logger("slo_manager")


@dataclass
class SLO:
    """Definition of a Service Level Objective."""

    name: str
    metric_type: MetricType
    threshold: float
    comparison: str = "less_than"  # less_than, greater_than, equal
    target_percentage: float = 99.0
    window_minutes: int = 60


@dataclass
class SLOResult:
    """Result of evaluating a Service Level Objective."""

    slo: SLO
    percentage: float
    met: bool


class SLOManager:
    """Manage a collection of SLOs and evaluate them."""

    def __init__(self) -> None:
        self.slos: List[SLO] = []

    def add_slo(self, slo: SLO) -> None:
        """Register a new SLO."""
        self.slos.append(slo)
        logger.debug(f"Added SLO {slo.name}")

    def evaluate_slos(self, metrics: List[Metric]) -> List[SLOResult]:
        """Evaluate all SLOs against provided metrics."""
        results: List[SLOResult] = []
        now = datetime.utcnow()

        for slo in self.slos:
            cutoff = now - timedelta(minutes=slo.window_minutes)
            relevant = [
                m
                for m in metrics
                if m.metric_type == slo.metric_type and m.timestamp >= cutoff
            ]

            if not relevant:
                results.append(SLOResult(slo=slo, percentage=0.0, met=False))
                continue

            satisfied = 0
            for m in relevant:
                if self._check_metric(m.value, slo.threshold, slo.comparison):
                    satisfied += 1

            pct = (satisfied / len(relevant)) * 100.0
            met = pct >= slo.target_percentage
            results.append(SLOResult(slo=slo, percentage=pct, met=met))

        return results

    @staticmethod
    def _check_metric(value: float, threshold: float, comparison: str) -> bool:
        if comparison == "less_than":
            return value < threshold
        if comparison == "greater_than":
            return value > threshold
        if comparison == "equal":
            return value == threshold
        return False
