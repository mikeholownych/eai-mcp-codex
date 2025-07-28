"""API routes for the Workflow Orchestrator service."""

from fastapi import APIRouter

from src.common.metrics import record_request

from .models import Workflow
from .orchestrator import start

router = APIRouter(prefix="/workflow", tags=["workflow-orchestrator"])


@router.post("/{workflow_id}", response_model=Workflow)
def run(workflow_id: int) -> Workflow:
    record_request("workflow-orchestrator")
    return start(workflow_id)
