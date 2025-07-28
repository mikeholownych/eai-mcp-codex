"""Plan Management configuration."""

import os

SERVICE_NAME = "plan-management"
SERVICE_PORT = int(os.getenv("PLAN_MANAGEMENT_PORT", 8002))
