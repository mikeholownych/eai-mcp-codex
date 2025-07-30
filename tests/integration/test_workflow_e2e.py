import pytest
from src.workflow_orchestrator.orchestrator import get_orchestrator
from src.workflow_orchestrator.models import WorkflowRequest, ExecutionMode
import sys
import os

# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

@pytest.mark.asyncio
async def test_workflow_execution_e2e():
    orchestrator = await get_orchestrator()
    
    # Create a simple workflow
    request = WorkflowRequest(
        name="E2E Test Workflow",
        description="Workflow for end-to-end testing",
        execution_mode=ExecutionMode.SEQUENTIAL,
        steps=[
            {
                "name": "Step 1: Mock Action",
                "step_type": "custom",
                "service_name": "mock_service", # This service doesn't exist, will fail
                "endpoint": "/mock/endpoint",
                "parameters": {"action": "do_something"}
            }
        ]
    )
    workflow = await orchestrator.create_workflow(request)
    
    # Execute the workflow
    execution = await orchestrator.execute_workflow(workflow.id)
    
    assert execution.status == "failed" # Expecting failure due to mock service
    assert execution.error_message is not None