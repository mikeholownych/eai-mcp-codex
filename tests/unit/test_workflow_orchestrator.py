from src.workflow_orchestrator.orchestrator import start


def test_start():
    assert start(1).id == 1
