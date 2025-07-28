"""Background task utilities."""

from .models import Workflow


def schedule(workflow_id: int) -> Workflow:
    """Schedule a workflow for asynchronous execution."""
    return Workflow(id=workflow_id)
