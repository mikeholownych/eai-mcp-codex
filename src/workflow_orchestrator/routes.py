"""API routes for the Workflow Orchestrator service."""

from typing import List
from fastapi import APIRouter, HTTPException

from src.common.metrics import record_request

from .models import Workflow, WorkflowRequest, WorkflowExecution
from .orchestrator import get_orchestrator

router = APIRouter(prefix="/workflow", tags=["workflow-orchestrator"])


@router.post("/", response_model=Workflow)
async def create_workflow_route(request: WorkflowRequest) -> Workflow:
    record_request("workflow-orchestrator")
    orchestrator = await get_orchestrator()
    return await orchestrator.create_workflow(request)


@router.post("/{workflow_id}/execute", response_model=WorkflowExecution)
async def execute_workflow_route(workflow_id: str) -> WorkflowExecution:
    record_request("workflow-orchestrator")
    orchestrator = await get_orchestrator()
    try:
        execution = await orchestrator.execute_workflow(workflow_id)
        return execution
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to execute workflow: {e}")


@router.get("/{workflow_id}", response_model=Workflow)
async def get_workflow_route(workflow_id: str) -> Workflow:
    orchestrator = await get_orchestrator()
    workflow = await orchestrator.get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow


@router.get("/", response_model=List[Workflow])
async def list_workflows_route() -> List[Workflow]:
    orchestrator = await get_orchestrator()
    return await orchestrator.list_workflows()
