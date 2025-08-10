import pytest
import sys
import types
from datetime import datetime, timedelta

# ruff: noqa: E402

# Stub out src.common and redis client to avoid heavy dependencies during tests
dummy_common = types.ModuleType("src.common")
redis_client_mod = types.ModuleType("src.common.redis_client")


class DatabaseManager:  # pragma: no cover - simple stub
    ...


class DummyRedis:
    def __init__(self) -> None:
        self.store = {}

    def setex(self, key: str, ttl: int, value: str) -> None:
        self.store[key] = value

    def get(self, key: str):
        return self.store.get(key)


def get_redis_connection(
    url: str | None = None,
) -> DummyRedis:  # noqa: D401 - simple stub
    return DummyRedis()


redis_client_mod.get_redis_connection = get_redis_connection
dummy_common.redis_client = redis_client_mod
dummy_common.database = types.ModuleType("database")
dummy_common.database.DatabaseManager = DatabaseManager
sys.modules.setdefault("src.common", dummy_common)
sys.modules.setdefault("src.common.redis_client", redis_client_mod)
sys.modules.setdefault("src.common.database", dummy_common.database)

from src.collaboration_orchestrator.orchestrator import CollaborationOrchestrator
from src.collaboration_orchestrator.models import (
    CollaborationMetrics,
    DecisionType,
    VoteChoice,
)
from src.a2a_communication.message_broker import A2AMessageBroker
from src.a2a_communication.models import A2AMessage, MessageType


class DummyBroker(A2AMessageBroker):
    def __init__(self) -> None:
        self.sent = []
        self.history: dict[str, list] = {}

    async def send_message(self, message) -> bool:  # type: ignore[override]
        self.sent.append(message)
        return True

    async def get_conversation_history(self, conversation_id, limit: int = 50):
        return self.history.get(str(conversation_id), [])


@pytest.mark.asyncio
async def test_session_invite_and_consensus() -> None:
    orchestrator = CollaborationOrchestrator()
    # Mock the redis and message_broker for testing
    orchestrator.redis = DummyRedis()
    orchestrator.message_broker = DummyBroker()
    
    session = await orchestrator.create_collaboration_session(
        title="Test", description="test", lead_agent="agent1"
    )
    invitation = await orchestrator.invite_agent_to_collaboration(
        session.session_id, "agent2", "agent1"
    )
    await orchestrator.respond_to_invitation(invitation.invitation_id, "agent2", True)
    assert "agent2" in orchestrator.active_sessions[session.session_id].participants

    decision = await orchestrator.create_consensus_decision(
        session.session_id,
        DecisionType.APPROVAL,
        "Ship",
        "Release",
        ["yes", "no"],
        "agent1",
    )
    await orchestrator.submit_vote(decision.decision_id, "agent1", VoteChoice.APPROVE)
    await orchestrator.submit_vote(decision.decision_id, "agent2", VoteChoice.APPROVE)
    assert decision.resolved
    assert decision.resolution == "approved"


@pytest.mark.asyncio
async def test_session_metrics_efficiency_scoring() -> None:
    broker = DummyBroker()
    orchestrator = CollaborationOrchestrator()
    # Mock the redis and message_broker for testing
    orchestrator.redis = DummyRedis()
    orchestrator.message_broker = broker

    session = await orchestrator.create_collaboration_session(
        title="Metrics", description="m", lead_agent="agent1"
    )
    invitation = await orchestrator.invite_agent_to_collaboration(
        session.session_id, "agent2", "agent1"
    )
    await orchestrator.respond_to_invitation(invitation.invitation_id, "agent2", True)

    start = datetime.utcnow()
    broker.history[str(session.session_id)] = [
        A2AMessage(
            conversation_id=session.session_id,
            sender_agent_id="agent1",
            recipient_agent_id="agent2",
            message_type=MessageType.NOTIFICATION,
            payload={},
            timestamp=start,
        ),
        A2AMessage(
            conversation_id=session.session_id,
            sender_agent_id="agent2",
            recipient_agent_id="agent1",
            message_type=MessageType.NOTIFICATION,
            payload={},
            timestamp=start + timedelta(minutes=5),
        ),
    ]

    decision = await orchestrator.create_consensus_decision(
        session.session_id,
        DecisionType.APPROVAL,
        "Launch",
        "Release",
        ["yes", "no"],
        "agent1",
    )
    await orchestrator.submit_vote(decision.decision_id, "agent1", VoteChoice.APPROVE)
    await orchestrator.submit_vote(decision.decision_id, "agent2", VoteChoice.APPROVE)

    await orchestrator.complete_collaboration(session.session_id)
    metrics_json = orchestrator.redis.get(f"collaboration:metrics:{session.session_id}")
    metrics = CollaborationMetrics.model_validate_json(metrics_json)

    assert metrics.average_response_time == pytest.approx(5.0)
    assert 0.0 < metrics.efficiency_score <= 1.0
