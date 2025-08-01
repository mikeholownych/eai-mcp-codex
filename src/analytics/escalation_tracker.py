from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List

from ..common.logging import get_logger

logger = get_logger("escalation_tracker")


@dataclass
class EscalationEvent:
    """Single escalation event."""

    session_id: str
    user_id: str
    issue_type: str
    timestamp: datetime = field(default_factory=datetime.utcnow)


class EscalationAbuseTracker:
    """Track escalation events and detect abuse patterns."""

    def __init__(self, threshold: int = 3, window_minutes: int = 60) -> None:
        self.threshold = threshold
        self.window_minutes = window_minutes
        self.events: List[EscalationEvent] = []

    def record_escalation(self, session_id: str, user_id: str, issue_type: str) -> None:
        """Record a new escalation event."""
        event = EscalationEvent(
            session_id=session_id, user_id=user_id, issue_type=issue_type
        )
        self.events.append(event)
        logger.debug("Recorded escalation event %s", event)

    def is_abuse(self, user_id: str) -> bool:
        """Check if the user exceeds the escalation threshold within the window."""
        cutoff = datetime.utcnow() - timedelta(minutes=self.window_minutes)
        recent = [
            e for e in self.events if e.user_id == user_id and e.timestamp >= cutoff
        ]
        return len(recent) >= self.threshold

    def clear_old_events(self) -> None:
        """Remove events older than the time window."""
        cutoff = datetime.utcnow() - timedelta(minutes=self.window_minutes)
        self.events = [e for e in self.events if e.timestamp >= cutoff]
