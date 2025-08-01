from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List

from ..common.logging import get_logger
from ..collaboration_orchestrator.models import VoteChoice
from .consensus_monitor import VoteEvent

logger = get_logger("consensus_insights")


@dataclass
class ConsensusSession:
    """Capture metadata about a consensus decision."""

    decision_id: str
    start_time: datetime = field(default_factory=datetime.utcnow)
    end_time: datetime | None = None
    votes: List[VoteEvent] = field(default_factory=list)

    def duration_seconds(self) -> float:
        """Return the duration of the session in seconds."""
        end = self.end_time or datetime.utcnow()
        return (end - self.start_time).total_seconds()


class ConsensusInsightGenerator:
    """Generate insights to optimize the consensus building process."""

    def __init__(self, max_duration: float = 300.0, max_changes: int = 2) -> None:
        self.sessions: Dict[str, ConsensusSession] = {}
        self.max_duration = max_duration
        self.max_changes = max_changes

    def start_session(self, decision_id: str) -> None:
        """Start tracking a new consensus session."""
        self.sessions[decision_id] = ConsensusSession(decision_id)
        logger.debug("Started consensus session %s", decision_id)

    def record_vote(self, decision_id: str, agent_id: str, choice: VoteChoice) -> None:
        """Record a vote within the session."""
        session = self.sessions.setdefault(decision_id, ConsensusSession(decision_id))
        session.votes.append(VoteEvent(decision_id, agent_id, choice))
        logger.debug("Recorded vote %s for decision %s", choice.value, decision_id)

    def end_session(self, decision_id: str) -> None:
        """Mark the session as completed."""
        session = self.sessions.get(decision_id)
        if session:
            session.end_time = datetime.utcnow()
            logger.debug("Ended consensus session %s", decision_id)

    def generate_insights(self, decision_id: str) -> List[str]:
        """Return optimization insights for the given session."""
        session = self.sessions.get(decision_id)
        if not session:
            return []

        insights: List[str] = []
        duration = session.duration_seconds()
        if duration > self.max_duration:
            insights.append(
                f"Consensus for {decision_id} took {duration:.1f}s which exceeds the {self.max_duration}s target."
            )

        changes_by_agent: Dict[str, int] = {}
        last_choice: Dict[str, VoteChoice] = {}
        for vote in session.votes:
            prev = last_choice.get(vote.agent_id)
            if prev is not None and prev != vote.choice:
                changes_by_agent[vote.agent_id] = (
                    changes_by_agent.get(vote.agent_id, 0) + 1
                )
            last_choice[vote.agent_id] = vote.choice

        if any(count > self.max_changes for count in changes_by_agent.values()):
            insights.append(
                "Frequent vote changes detected which may indicate uncertainty or miscommunication."
            )

        return insights
