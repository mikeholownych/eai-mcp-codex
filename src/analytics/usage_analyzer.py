from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Set

from ..common.logging import get_logger

logger = get_logger("usage_analyzer")


@dataclass
class UsageEvent:
    """Represents a single usage event."""

    user_id: str
    action: str
    timestamp: datetime = field(default_factory=datetime.utcnow)


class UsagePatternAnalyzer:
    """Analyzes user usage patterns for business intelligence."""

    def __init__(self) -> None:
        self.events: List[UsageEvent] = []

    def record_event(self, user_id: str, action: str) -> None:
        """Record a user action."""
        event = UsageEvent(user_id=user_id, action=action)
        self.events.append(event)
        logger.debug("Recorded usage event %s", event)

    def get_daily_active_users(self, days: int = 1) -> int:
        """Return number of unique users active in the timeframe."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        users: Set[str] = {e.user_id for e in self.events if e.timestamp >= cutoff}
        return len(users)

    def get_action_frequency(self, action: str, days: int = 1) -> int:
        """Count occurrences of an action in the timeframe."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        return sum(
            1 for e in self.events if e.action == action and e.timestamp >= cutoff
        )

    def clear_old_events(self, older_than_days: int = 30) -> None:
        """Remove events older than the specified window."""
        cutoff = datetime.utcnow() - timedelta(days=older_than_days)
        self.events = [e for e in self.events if e.timestamp >= cutoff]
