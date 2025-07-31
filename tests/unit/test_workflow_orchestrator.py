import pytest
from src.workflow_orchestrator.orchestrator import get_orchestrator
from src.workflow_orchestrator.models import WorkflowRequest, WorkflowStatus

# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))


@pytest.mark.asyncio
async def test_create_and_get_workflow() -> None:
    orchestrator = await get_orchestrator()
    request = WorkflowRequest(
        name="Test Workflow", description="A workflow for testing", steps=[]
    )
    workflow = await orchestrator.create_workflow(request)
    assert workflow.id is not None
    assert workflow.name == "Test Workflow"
    assert workflow.status == WorkflowStatus.DRAFT

    retrieved_workflow = await orchestrator.get_workflow(workflow.id)
    assert retrieved_workflow == workflow

    # Clean up (optional, but good practice for unit tests)
    # await orchestrator.delete_workflow(workflow.id) # Assuming a delete method exists
