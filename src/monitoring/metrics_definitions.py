from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, Any, List


class MetricType(str, Enum):
    """Types of metrics to monitor."""

    PERFORMANCE = "performance"
    RELIABILITY = "reliability"
    ACCURACY = "accuracy"
    RESOURCE_USAGE = "resource_usage"
    ERROR_RATE = "error_rate"
    LATENCY = "latency"
    THROUGHPUT = "throughput"
    USER_SATISFACTION = "user_satisfaction"
    CODE_QUALITY = "code_quality"
    SECURITY = "security"


@dataclass
class Metric:
    """Individual metric measurement."""

    metric_id: str
    metric_type: MetricType
    name: str
    value: float
    unit: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
