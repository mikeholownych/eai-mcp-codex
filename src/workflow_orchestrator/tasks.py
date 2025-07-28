"""Background tasks."""

from .models import Workflow


def schedule(workflow_id: int) -> Workflow:
    return Workflow(id=workflow_id)
