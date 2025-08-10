from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Set

from ..common.logging import get_logger

logger = get_logger("user_engagement")


@dataclass
class EngagementEvent:
    """Represents a single user engagement event."""

    user_id: str
    event_type: str
    timestamp: datetime = field(default_factory=datetime.utcnow)


class UserEngagementTracker:
    """Tracks user engagement events for analytics purposes."""

    def __init__(self) -> None:
        self.events: List[EngagementEvent] = []

    def record_event(self, user_id: str, event_type: str) -> None:
        """Record a new engagement event."""
        event = EngagementEvent(user_id=user_id, event_type=event_type)
        self.events.append(event)
        logger.debug("Recorded engagement event %s", event)

    def get_active_users(self, since_minutes: int = 60) -> int:
        """Return number of unique users active within the time window."""
        cutoff = datetime.utcnow() - timedelta(minutes=since_minutes)
        users: Set[str] = {e.user_id for e in self.events if e.timestamp >= cutoff}
        return len(users)

    def get_event_count(self, event_type: str, since_minutes: int = 60) -> int:
        """Count occurrences of an event type in the time window."""
        cutoff = datetime.utcnow() - timedelta(minutes=since_minutes)
        return sum(
            1
            for e in self.events
            if e.event_type == event_type and e.timestamp >= cutoff
        )

    def get_user_engagement_score(self, user_id: str, since_minutes: int = 60) -> float:
        """Calculate a simple engagement score for a user."""
        cutoff = datetime.utcnow() - timedelta(minutes=since_minutes)
        user_events = [
            e for e in self.events if e.user_id == user_id and e.timestamp >= cutoff
        ]
        if not user_events:
            return 0.0
        event_types = {e.event_type for e in user_events}
        # Base scoring: unique event types + quarter-weight per event
        # With two events (login, view) this yields 2 + 0.5 = 2.5
        return float(len(event_types) + 0.25 * (len(user_events)))

    def clear_old_events(self, older_than_minutes: int = 1440) -> None:
        """Remove events older than the specified time window."""
        cutoff = datetime.utcnow() - timedelta(minutes=older_than_minutes)
        self.events = [e for e in self.events if e.timestamp >= cutoff]
