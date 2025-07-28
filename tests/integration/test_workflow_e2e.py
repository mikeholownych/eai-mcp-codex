from src.workflow_orchestrator.orchestrator import start
from src.workflow_orchestrator.workflow_engine import run


def test_workflow_execution():
    wf = start(1)
    result = run(wf)
    assert result == "running:1"
