from src.plan_management.plan_manager import create_plan


def test_plan_manager_scalability():
    plans = [create_plan(f"p{i}") for i in range(100)]
    assert len(plans) == 100
