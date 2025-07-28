"""Workflow Orchestrator configuration."""

import os

SERVICE_NAME = "workflow-orchestrator"
SERVICE_PORT = int(os.getenv("WORKFLOW_ORCHESTRATOR_PORT", 8004))
