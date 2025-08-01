from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from ..agent_pool.models import AgentPoolConfig, AgentType, WorkloadDistribution
from ..common.logging import get_logger

logger = get_logger("workload_optimizer")


@dataclass
class ScalingRecommendation:
    """Recommended scaling actions for an agent type."""

    scale_up: int = 0
    scale_down: int = 0


class AgentWorkloadOptimizer:
    """Analyze workload distribution and recommend scaling actions."""

    def __init__(
        self, scale_up_threshold: float = 0.8, scale_down_threshold: float = 0.3
    ) -> None:
        self.scale_up_threshold = scale_up_threshold
        self.scale_down_threshold = scale_down_threshold

    def recommend_scaling(
        self, distributions: List[WorkloadDistribution], config: AgentPoolConfig
    ) -> Dict[AgentType, ScalingRecommendation]:
        """Return scaling recommendations by agent type."""
        recs: Dict[AgentType, ScalingRecommendation] = {}
        for dist in distributions:
            rec = recs.setdefault(dist.agent_type, ScalingRecommendation())
            max_allowed = config.max_agents_per_type.get(dist.agent_type, 1)
            if (
                dist.utilization_rate > self.scale_up_threshold
                and dist.total_instances < max_allowed
            ):
                rec.scale_up += 1
            elif (
                dist.utilization_rate < self.scale_down_threshold
                and dist.idle_instances > config.min_idle_agents
            ):
                rec.scale_down += 1
        logger.debug("Generated workload scaling recommendations: %s", recs)
        return recs
