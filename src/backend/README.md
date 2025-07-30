# Backend Package

This package exposes internal backend utilities used by multiple services. Currently it provides a WebSocket gateway used for agent communication.

## Components

- `websocket_gateway.py` – FastAPI app factory and `WebSocketGateway` class for routing A2A messages.

