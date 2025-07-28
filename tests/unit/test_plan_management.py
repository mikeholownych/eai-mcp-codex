from src.plan_management.plan_manager import (
    create_plan,
    delete_plan,
    get_plan,
    list_plans,
)


def test_create_plan() -> None:
    plan = create_plan("test")
    assert get_plan(plan.id) == plan
    assert plan in list_plans()
    delete_plan(plan.id)
    assert get_plan(plan.id) is None
