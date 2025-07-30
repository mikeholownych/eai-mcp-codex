# Backend Package

This package exposes internal backend utilities used by multiple services. It provides
both a WebSocket gateway for agent communication and a helper to share metrics
collectors across services.

## Components

- `websocket_gateway.py` – FastAPI app factory and `WebSocketGateway` class for routing A2A messages.
- `metrics_collector.py` – `get_backend_collector` helper returning a singleton
  `MetricsCollector` per service.

