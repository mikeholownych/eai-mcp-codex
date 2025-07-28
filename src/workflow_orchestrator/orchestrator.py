"""Workflow orchestrator logic."""

from .models import Workflow


def start(workflow_id: int) -> Workflow:
    return Workflow(id=workflow_id)
