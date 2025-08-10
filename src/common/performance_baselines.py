"""
Performance baselines and anomaly detection utilities.

Provides lightweight baseline computation suitable for runtime use and
post-hoc analysis. This module is intentionally dependency-light and
deterministic to be safe in critical paths.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class PerformanceBaseline:
    metric_name: str
    service_name: str
    operation_name: str = ""
    sample_count: int = 0
    mean: float = 0.0
    median: float = 0.0
    std_dev: float = 0.0
    min_value: float = 0.0
    max_value: float = 0.0
    p25: float = 0.0
    p75: float = 0.0
    p95: float = 0.0
    p99: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


def _percentile(sorted_samples: List[float], pct: float) -> float:
    if not sorted_samples:
        return 0.0
    k = (len(sorted_samples) - 1) * pct
    f = int(k)
    c = min(f + 1, len(sorted_samples) - 1)
    if f == c:
        return sorted_samples[f]
    d0 = sorted_samples[f] * (c - k)
    d1 = sorted_samples[c] * (k - f)
    return d0 + d1


class PerformanceBaselineManager:
    def establish_baseline(
        self, metric_name: str, service_name: str, samples: List[float], operation_name: str = ""
    ) -> Optional[PerformanceBaseline]:
        if not samples:
            return None
        sorted_samples = sorted(samples)
        mean = statistics.mean(sorted_samples)
        median = statistics.median(sorted_samples)
        std_dev = statistics.stdev(sorted_samples) if len(sorted_samples) > 1 else 0.0
        return PerformanceBaseline(
            metric_name=metric_name,
            service_name=service_name,
            operation_name=operation_name,
            sample_count=len(sorted_samples),
            mean=mean,
            median=median,
            std_dev=std_dev,
            min_value=sorted_samples[0],
            max_value=sorted_samples[-1],
            p25=_percentile(sorted_samples, 0.25),
            p75=_percentile(sorted_samples, 0.75),
            p95=_percentile(sorted_samples, 0.95),
            p99=_percentile(sorted_samples, 0.99),
        )

    def is_anomalous(self, value: float, baseline: PerformanceBaseline, multiplier: float = 3.0) -> Tuple[bool, str]:
        if baseline.std_dev == 0:
            return False, "no_variance"
        upper = baseline.mean + multiplier * baseline.std_dev
        lower = max(0.0, baseline.mean - multiplier * baseline.std_dev)
        if value > upper:
            return True, "high_spike"
        if value < lower:
            return True, "low_dip"
        return False, "normal"

