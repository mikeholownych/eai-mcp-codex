from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from ..common.logging import get_logger

logger = get_logger("cost_tracker")


@dataclass
class CostEvent:
    """Represents a single cost event."""

    item_id: str
    cost: float
    category: str = "general"
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


class CostTracker:
    """Tracks cost-related events for optimization analytics."""

    def __init__(self) -> None:
        self.events: List[CostEvent] = []

    def record_cost(
        self,
        item_id: str,
        cost: float,
        category: str = "general",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Record a new cost event."""
        event = CostEvent(
            item_id=item_id, cost=cost, category=category, metadata=metadata or {}
        )
        self.events.append(event)
        logger.debug("Recorded cost event %s", event)

    def total_cost(self, since_hours: int = 24) -> float:
        """Return total cost within the time window."""
        cutoff = datetime.utcnow() - timedelta(hours=since_hours)
        return sum(e.cost for e in self.events if e.timestamp >= cutoff)

    def cost_by_category(self, since_hours: int = 24) -> Dict[str, float]:
        """Aggregate cost by category."""
        cutoff = datetime.utcnow() - timedelta(hours=since_hours)
        totals: Dict[str, float] = {}
        for event in self.events:
            if event.timestamp >= cutoff:
                totals[event.category] = totals.get(event.category, 0.0) + event.cost
        return totals
