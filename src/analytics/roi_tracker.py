from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from ..common.logging import get_logger
from .cost_tracker import CostTracker

logger = get_logger("roi_tracker")


@dataclass
class ValueEvent:
    """Represents a recorded value event."""

    item_id: str
    value: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


class ROITracker:
    """Calculates return on investment using cost and value events."""

    def __init__(self, cost_tracker: CostTracker | None = None) -> None:
        self.cost_tracker = cost_tracker or CostTracker()
        self.value_events: List[ValueEvent] = []

    def record_value(
        self, item_id: str, value: float, metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Record a new value event."""
        event = ValueEvent(item_id=item_id, value=value, metadata=metadata or {})
        self.value_events.append(event)
        logger.debug("Recorded value event %s", event)

    def total_value(self, since_hours: int = 24) -> float:
        """Return total recorded value within the time window."""
        cutoff = datetime.utcnow() - timedelta(hours=since_hours)
        return sum(e.value for e in self.value_events if e.timestamp >= cutoff)

    def calculate_roi(self, since_hours: int = 24) -> float:
        """Calculate ROI percentage for the given window."""
        total_value = self.total_value(since_hours)
        total_cost = self.cost_tracker.total_cost(since_hours)
        if total_cost == 0:
            return 0.0
        return (total_value - total_cost) / total_cost * 100
