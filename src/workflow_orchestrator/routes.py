"""Routes for Workflow Orchestrator."""

from fastapi import APIRouter

from .models import Workflow

router = APIRouter()


@router.get("/workflows/{workflow_id}")
def get_workflow(workflow_id: int) -> Workflow:
    return Workflow(id=workflow_id)
