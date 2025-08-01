"""Utilities for analyzing cost data and suggesting optimizations."""

from __future__ import annotations

from typing import Dict, List

from .cost_tracker import CostTracker
from .roi_tracker import ROITracker
from ..common.logging import get_logger

logger = get_logger("cost_optimizer")


class CostOptimizer:
    """Provide cost optimization insights based on tracked spend and ROI."""

    def __init__(
        self,
        cost_tracker: CostTracker | None = None,
        roi_tracker: ROITracker | None = None,
    ) -> None:
        self.cost_tracker = cost_tracker or CostTracker()
        self.roi_tracker = roi_tracker or ROITracker(self.cost_tracker)

    def analyze_costs(self, since_hours: int = 24) -> Dict[str, float]:
        """Return aggregated spend by category over the given window."""
        return self.cost_tracker.cost_by_category(since_hours)

    def generate_recommendations(
        self,
        since_hours: int = 24,
        threshold: float = 100.0,
        roi_threshold: float = 100.0,
    ) -> List[str]:
        """Generate cost optimization recommendations."""
        recommendations: List[str] = []
        costs = self.cost_tracker.cost_by_category(since_hours)
        for category, total in costs.items():
            if total >= threshold:
                recommendations.append(
                    f"Consider optimizing spend for {category}: ${total:.2f} in last {since_hours}h"
                )
        roi = self.roi_tracker.calculate_roi(since_hours)
        if roi < roi_threshold:
            recommendations.append(
                f"ROI is {roi:.1f}% over last {since_hours}h. Increase value or reduce cost"
            )
        logger.debug("Generated cost optimization recommendations: %s", recommendations)
        return recommendations
