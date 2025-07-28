"""Engine for workflow processing."""

from .models import Workflow


def run(workflow: Workflow) -> str:
    return f"running:{workflow.id}"
