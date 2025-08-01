from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List

from ..common.logging import get_logger
from ..collaboration_orchestrator.models import VoteChoice

logger = get_logger("consensus_monitor")


@dataclass
class VoteEvent:
    """Record of a single vote action."""

    decision_id: str
    agent_id: str
    choice: VoteChoice
    timestamp: datetime = field(default_factory=datetime.utcnow)


class ConsensusManipulationDetector:
    """Detect suspicious voting patterns in consensus decisions."""

    def __init__(self, max_changes: int = 1) -> None:
        self.max_changes = max_changes
        self.vote_history: Dict[str, List[VoteEvent]] = {}

    def record_vote(self, decision_id: str, agent_id: str, choice: VoteChoice) -> None:
        """Record a vote for a decision."""
        history = self.vote_history.setdefault(decision_id, [])
        history.append(VoteEvent(decision_id, agent_id, choice))
        logger.debug("Recorded vote %s for decision %s", choice.value, decision_id)

    def detect_manipulators(self, decision_id: str) -> List[str]:
        """Return agents that changed their vote more than allowed."""
        history = self.vote_history.get(decision_id, [])
        by_agent: Dict[str, List[VoteChoice]] = {}
        for event in history:
            by_agent.setdefault(event.agent_id, []).append(event.choice)

        manipulators: List[str] = []
        for agent_id, choices in by_agent.items():
            unique: List[VoteChoice] = []
            for ch in choices:
                if not unique or unique[-1] is not ch:
                    unique.append(ch)
            # number of changes is len(unique)-1
            if len(unique) - 1 > self.max_changes:
                manipulators.append(agent_id)
                logger.debug(
                    "Agent %s changed vote %d times on decision %s",
                    agent_id,
                    len(unique) - 1,
                    decision_id,
                )
        return manipulators
