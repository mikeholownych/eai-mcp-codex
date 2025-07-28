from src.plan_management.plan_manager import create_plan, list_plans


def test_create_plan() -> None:
    plan = create_plan("test")
    assert plan in list_plans()
