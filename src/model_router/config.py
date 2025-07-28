"""Model Router configuration."""

import os

SERVICE_NAME = "model-router"
SERVICE_PORT = int(os.getenv("MODEL_ROUTER_PORT", 8001))
