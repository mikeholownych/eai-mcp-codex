from src.analytics.consensus_monitor import ConsensusManipulationDetector
from src.collaboration_orchestrator.models import VoteChoice


def test_detects_vote_manipulation() -> None:
    detector = ConsensusManipulationDetector(max_changes=1)
    decision = "d1"
    detector.record_vote(decision, "u1", VoteChoice.APPROVE)
    detector.record_vote(decision, "u1", VoteChoice.REJECT)
    detector.record_vote(decision, "u1", VoteChoice.APPROVE)
    assert "u1" in detector.detect_manipulators(decision)


def test_allows_single_change() -> None:
    detector = ConsensusManipulationDetector(max_changes=1)
    decision = "d2"
    detector.record_vote(decision, "u2", VoteChoice.APPROVE)
    detector.record_vote(decision, "u2", VoteChoice.REJECT)
    assert detector.detect_manipulators(decision) == []
