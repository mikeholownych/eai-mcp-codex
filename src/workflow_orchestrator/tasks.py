"""Background task utilities."""

import asyncio
from typing import Dict, Any

from src.common.logging import get_logger
from .models import Workflow, WorkflowExecution
from .orchestrator import get_orchestrator

logger = get_logger("workflow_tasks")


async def schedule_workflow_execution(
    workflow_id: str, triggered_by: str = "system", context: Dict[str, Any] = None
) -> WorkflowExecution:
    """Schedules a workflow for asynchronous execution by the orchestrator."""
    orchestrator = get_orchestrator()
    try:
        logger.info(f"Scheduling workflow {workflow_id} for execution.")
        execution = await orchestrator.execute_workflow(
            workflow_id, triggered_by, context
        )
        logger.info(f"Workflow {workflow_id} scheduled. Execution ID: {execution.id}")
        return execution
    except Exception as e:
        logger.error(f"Failed to schedule workflow {workflow_id}: {e}")
        raise


def schedule(
    workflow_id: str,
) -> Workflow:  # Legacy function for backward compatibility
    """Schedule a workflow for asynchronous execution."""
    # This function now calls the async scheduler
    # In a real application, this would typically be called by a background task runner
    # or a message queue consumer.
    logger.warning(
        f"Legacy schedule function called for workflow {workflow_id}. Consider using schedule_workflow_execution."
    )
    # For immediate execution in a synchronous context (e.g., FastAPI route without await)
    # This is a simplification and might block the event loop in a real async app.
    import threading

    threading.Thread(
        target=asyncio.run, args=(schedule_workflow_execution(workflow_id),)
    ).start()

    # Return a placeholder Workflow object for immediate response
    from .models import (
        WorkflowStatus,
    )  # Import here to avoid circular dependency if Workflow is in models.py

    return Workflow(
        id=workflow_id,
        name=f"Workflow {workflow_id} (Scheduled)",
        status=WorkflowStatus.PENDING,
    )
