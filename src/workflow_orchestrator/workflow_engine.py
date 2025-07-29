"""Engine for workflow processing."""

from typing import Dict, Any
from src.common.logging import get_logger
from .models import Workflow, WorkflowExecution, WorkflowStatus, StepStatus
from .orchestrator import get_orchestrator

logger = get_logger("workflow_engine")

async def execute_workflow_engine(workflow_id: str, context: Dict[str, Any] = None) -> WorkflowExecution:
    """Executes a workflow using the orchestrator's core logic."""
    orchestrator = get_orchestrator()
    try:
        logger.info(f"Workflow engine executing workflow: {workflow_id}")
        execution = await orchestrator.execute_workflow(workflow_id, triggered_by="workflow_engine", context=context)
        logger.info(f"Workflow {workflow_id} execution completed with status: {execution.status}")
        return execution
    except Exception as e:
        logger.error(f"Workflow engine failed to execute workflow {workflow_id}: {e}")
        raise

def run(workflow: Workflow) -> str:
    """Legacy function for backward compatibility. Runs a workflow synchronously (blocking)."""
    logger.warning(f"Legacy run function called for workflow {workflow.id}. Consider using execute_workflow_engine.")
    # This is a simplified synchronous execution for compatibility.
    # In a real async application, this would typically be handled by an async worker.
    try:
        orchestrator = get_orchestrator()
        # Simulate synchronous execution by running the async method
        import asyncio
        execution = asyncio.run(orchestrator.execute_workflow(workflow.id, triggered_by="legacy_run"))
        return f"running:{workflow.id} status:{execution.status}"
    except Exception as e:
        logger.error(f"Legacy run failed for workflow {workflow.id}: {e}")
        return f"error:{workflow.id} details:{e}"

def status(workflow: Workflow) -> str:
    """Legacy function for backward compatibility. Returns the status of a workflow."""
    logger.warning(f"Legacy status function called for workflow {workflow.id}. Consider querying orchestrator directly.")
    orchestrator = get_orchestrator()
    workflow_obj = orchestrator.get_workflow(workflow.id)
    if workflow_obj:
        return f"status:{workflow_obj.status.value}"
    return f"status:not_found"