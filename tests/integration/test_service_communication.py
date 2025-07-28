from src.model_router.router import route
from src.model_router.models import ModelRequest
from src.plan_management.plan_manager import create_plan
from src.git_worktree.worktree_manager import create
from src.verification_feedback.verification_engine import verify
from src.workflow_orchestrator.orchestrator import start


def test_basic_service_flow(tmp_path):
    plan = create_plan("integration-test")
    assert plan.id > 0

    result = route(ModelRequest(text="hello"))
    assert result.result.startswith("haiku:")

    wt = create(str(tmp_path / "repo"))
    assert "repo" in wt

    workflow = start(42)
    assert workflow.id == 42

    feedback = verify(42)
    assert feedback.id == 42
