from __future__ import annotations

from typing import Dict, List

from src.a2a_communication.message_broker import A2AMessageBroker

from fastapi.testclient import TestClient

from src.backend.websocket_gateway import create_app
from src.a2a_communication.models import A2AMessage, MessageType


class FakePubSub:
    def __init__(self) -> None:
        self.messages: List[str] = []

    def subscribe(self, channel: str) -> None:  # pragma: no cover - simple stub
        pass

    def get_message(self, timeout: float = 0.0):
        if self.messages:
            return {"type": "message", "data": self.messages.pop(0)}
        return None

    def close(self) -> None:  # pragma: no cover - simple stub
        pass


class FakeRedis:
    def __init__(self) -> None:
        self.pubsub_instance = FakePubSub()

    def pubsub(self, ignore_subscribe_messages: bool = True) -> FakePubSub:
        return self.pubsub_instance


class DummyBroker(A2AMessageBroker):
    def __init__(self) -> None:
        # Avoid connecting to a real Redis instance
        self.redis = FakeRedis()
        self.sent: List[A2AMessage] = []
        self.pending: Dict[str, List[A2AMessage]] = {}

    def send_message(self, message: A2AMessage) -> bool:
        self.sent.append(message)
        return True

    def get_messages(self, agent_id: str, limit: int = 10) -> List[A2AMessage]:
        msgs = self.pending.get(agent_id, [])[:limit]
        self.pending[agent_id] = self.pending.get(agent_id, [])[len(msgs) :]
        return msgs


def test_websocket_send_and_receive() -> None:
    broker = DummyBroker()
    app = create_app(broker=broker)

    message = A2AMessage(
        sender_agent_id="system",
        recipient_agent_id="agent1",
        message_type=MessageType.NOTIFICATION,
        payload={"msg": "hello"},
    )
    broker.pending.setdefault("agent1", []).append(message)

    with TestClient(app) as client:
        with client.websocket_connect("/ws/agent1") as ws:
            assert ws.receive_json() == {"status": "connected"}
            ws.send_json(
                {
                    "sender_agent_id": "agent1",
                    "message_type": "notification",
                    "payload": {"foo": "bar"},
                }
            )
            received = ws.receive_json()
            assert received["payload"] == {"msg": "hello"}

    assert broker.sent[0].payload == {"foo": "bar"}
