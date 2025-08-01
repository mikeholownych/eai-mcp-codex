"""Predictive analytics and machine learning module."""

from .prediction_engine import (
    PerformancePredictionEngine,
    PredictionResult,
    HistoricalDataPoint,
    AnomalyDetection,
    RiskLevel,
)
from .user_engagement import EngagementEvent, UserEngagementTracker
from .usage_analyzer import UsageEvent, UsagePatternAnalyzer
from .cost_tracker import CostTracker, CostEvent
from .roi_tracker import ROITracker, ValueEvent
from .capacity_planner import CapacityPlanner, CapacityEstimate
from .cost_optimizer import CostOptimizer
from .escalation_tracker import EscalationAbuseTracker, EscalationEvent
from .consensus_monitor import (
    ConsensusManipulationDetector,
    VoteEvent,
)
from .consensus_insights import ConsensusInsightGenerator, ConsensusSession
from .productivity_benchmark import (
    ProductivityRecord,
    AgentProductivityBenchmark,
)

__all__ = [
    "PerformancePredictionEngine",
    "PredictionResult",
    "HistoricalDataPoint",
    "AnomalyDetection",
    "RiskLevel",
    "EngagementEvent",
    "UserEngagementTracker",
    "UsageEvent",
    "UsagePatternAnalyzer",
    "CostTracker",
    "CostEvent",
    "ROITracker",
    "ValueEvent",
    "CapacityPlanner",
    "CapacityEstimate",
    "CostOptimizer",
    "EscalationAbuseTracker",
    "EscalationEvent",
    "ConsensusManipulationDetector",
    "VoteEvent",
    "ConsensusInsightGenerator",
    "ConsensusSession",
    "ProductivityRecord",
    "AgentProductivityBenchmark",
]
