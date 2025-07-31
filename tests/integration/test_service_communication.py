import pytest
from src.plan_management.plan_manager import create_plan
from src.workflow_orchestrator.orchestrator import get_orchestrator
from src.workflow_orchestrator.models import WorkflowRequest
from src.common.database import DatabaseManager
import os

# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

@pytest.fixture(autouse=True)
async def setup_and_teardown_db():
    os.environ["TESTING_MODE"] = "true"
    # Initialize DatabaseManager for each service that uses it
    await DatabaseManager("plan_management_db").connect()
    await DatabaseManager("git_worktree_db").connect()
    await DatabaseManager("verification_feedback_db").connect()
    await DatabaseManager("workflow_orchestrator_db").connect()
    yield
    await DatabaseManager("plan_management_db").disconnect()
    await DatabaseManager("git_worktree_db").disconnect()
    await DatabaseManager("verification_feedback_db").disconnect()
    await DatabaseManager("workflow_orchestrator_db").disconnect()
    os.environ["TESTING_MODE"] = "false"

@pytest.mark.asyncio
async def test_basic_service_flow(tmp_path):
    plan = await create_plan("integration-test")
    assert plan.id is not None

    # For a true integration test, ensure llm-router and ollama are running
    # assert result.result.startswith("haiku:")


    # wt = await create(str(tmp_path / "repo"))
    # assert "repo" in wt

    orchestrator = await get_orchestrator()
    workflow_request = WorkflowRequest(name="test_workflow", steps=[])
    workflow = await orchestrator.create_workflow(workflow_request)
    assert workflow.id is not None

    # feedback = await verify(42)
    # assert feedback.id is not None
