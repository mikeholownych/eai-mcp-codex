"""Real-time WebSocket gateway for agent-to-agent communication."""

from __future__ import annotations

import asyncio
from typing import Dict, Optional, List

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from src.a2a_communication.message_broker import A2AMessageBroker
from src.a2a_communication.models import A2AMessage
from src.common.logging import get_logger
from src.backend.metrics_collector import get_backend_collector
from src.common.metrics import MetricsCollector
from src.common.health_check import detailed_health
from src.common.service_registry import ServiceRegistry, ServiceInfo

logger = get_logger("websocket_gateway")


class WebSocketGateway:
    """Manage WebSocket connections and route messages via the message broker.

    Designed to work with both synchronous test doubles and the real async
    broker implementation. All broker calls are funneled through a helper that
    awaits coroutines when necessary, enabling seamless operation in tests and
    production.
    """

    def __init__(
        self,
        broker: Optional[A2AMessageBroker] = None,
        metrics: Optional[MetricsCollector] = None,
    ) -> None:
        self.broker = broker or A2AMessageBroker()
        self.metrics = metrics or get_backend_collector("websocket-gateway")
        self.connections: Dict[str, WebSocket] = {}
        self._tasks: Dict[str, asyncio.Task] = {}

    async def connect(self, agent_id: str, websocket: WebSocket) -> None:
        """Accept a new WebSocket connection."""
        await websocket.accept()
        self.connections[agent_id] = websocket
        self.metrics.set_active_connections(len(self.connections))
        self._tasks[agent_id] = asyncio.create_task(self._deliver(agent_id))
        logger.info("Agent %s connected", agent_id)

    async def disconnect(self, agent_id: str) -> None:
        """Remove a WebSocket connection."""
        task = self._tasks.pop(agent_id, None)
        if task:
            task.cancel()
        websocket = self.connections.pop(agent_id, None)
        self.metrics.set_active_connections(len(self.connections))
        if websocket:
            await websocket.close()
        logger.info("Agent %s disconnected", agent_id)

    async def handle_incoming(self, agent_id: str, data: str) -> None:
        """Handle an incoming message from an agent."""
        message = A2AMessage.model_validate_json(data)
        await _maybe_await(self.broker.send_message(message))
        self.metrics.record_message_received()
        logger.debug("Message %s routed", message.id)

    async def _deliver(self, agent_id: str) -> None:
        """Background task delivering queued messages."""
        websocket = self.connections[agent_id]
        try:
            while True:
                # Retrieve any pending messages for this agent
                messages = await _maybe_await(self.broker.get_messages(agent_id))
                for msg in messages or []:
                    await websocket.send_text(msg.model_dump_json())
                    self.metrics.record_message_sent()

                await asyncio.sleep(0.5)
        except asyncio.CancelledError:
            logger.debug("Delivery task cancelled for %s", agent_id)
        except Exception as exc:  # pragma: no cover - unexpected errors
            logger.error("Delivery loop error for %s: %s", agent_id, exc)


def create_app(
    broker: Optional[A2AMessageBroker] = None,
    service_registry: Optional[ServiceRegistry] = None,
) -> FastAPI:
    """Create FastAPI application with WebSocket and service endpoints."""

    app = FastAPI()
    gateway = WebSocketGateway(broker=broker)

    registry = service_registry

    @app.websocket("/ws/{agent_id}")
    async def websocket_endpoint(websocket: WebSocket, agent_id: str) -> None:
        await gateway.connect(agent_id, websocket)
        await websocket.send_json({"status": "connected"})
        try:
            while True:
                data = await websocket.receive_text()
                await gateway.handle_incoming(agent_id, data)
        except WebSocketDisconnect:
            await gateway.disconnect(agent_id)

    @app.get("/health")
    async def health() -> Dict[str, object]:
        return await detailed_health("websocket-gateway")

    if registry is not None:

        @app.get("/services")
        async def list_services() -> List[ServiceInfo]:
            return await registry.list_services()

        @app.get("/services/{service_name}")
        async def get_service(service_name: str) -> Optional[ServiceInfo]:
            return await registry.get_service(service_name)

        @app.post("/services")
        async def register_service(
            service_name: str,
            service_url: str,
            metadata: Optional[Dict[str, object]] = None,
        ) -> Dict[str, bool]:
            result = await registry.register_service(
                service_name, service_url, metadata
            )
            return {"success": result}

        @app.post("/services/{service_name}/heartbeat")
        async def heartbeat(service_name: str) -> Dict[str, bool]:
            result = await registry.heartbeat(service_name)
            return {"success": result}

    return app


async def _maybe_await(result):
    """Await a value if it is awaitable, otherwise return it directly."""
    if asyncio.iscoroutine(result):
        return await result
    return result
