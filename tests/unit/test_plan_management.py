from src.plan_management.plan_manager import create_plan


def test_create_plan():
    assert create_plan("test").name == "test"
