from datetime import timedelta

from src.analytics.consensus_insights import ConsensusInsightGenerator
from src.collaboration_orchestrator.models import VoteChoice


def test_consensus_insights_detects_long_duration_and_changes() -> None:
    gen = ConsensusInsightGenerator(max_duration=60.0, max_changes=1)
    decision_id = "d1"

    gen.start_session(decision_id)
    gen.sessions[decision_id].start_time -= timedelta(seconds=120)
    gen.record_vote(decision_id, "a1", VoteChoice.APPROVE)
    gen.record_vote(decision_id, "a1", VoteChoice.REJECT)
    gen.record_vote(decision_id, "a1", VoteChoice.APPROVE)
    gen.end_session(decision_id)

    insights = gen.generate_insights(decision_id)
    joined = " ".join(insights).lower()
    assert "exceeds" in joined
    assert "vote changes" in joined
