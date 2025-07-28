"""Simple workflow orchestration logic."""

from .models import Workflow


def start(workflow_id: int) -> Workflow:
    """Kick off a workflow and return its metadata."""
    return Workflow(id=workflow_id)
