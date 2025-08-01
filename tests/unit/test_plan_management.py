import pytest
from src.plan_management.plan_manager import (
    create_plan,
    delete_plan,
    get_plan,
    list_plans,
    PlanStatus,
)
from src.common.database import DatabaseManager
import os

# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))


@pytest.fixture(autouse=True)
async def setup_and_teardown_db():
    os.environ["TESTING_MODE"] = "true"
    db_manager = DatabaseManager("plan_management_db")
    await db_manager.connect()
    # In a real test, you might create tables here if not using in-memory
    yield
    await db_manager.disconnect()
    os.environ["TESTING_MODE"] = "false"


@pytest.mark.asyncio
async def test_create_plan() -> None:
    plan = await create_plan("test")
    assert plan.id is not None
    assert plan.title == "test"
    assert plan.status == PlanStatus.DRAFT

    retrieved_plan = await get_plan(plan.id)
    assert retrieved_plan == plan

    all_plans = await list_plans()
    assert plan in all_plans

    await delete_plan(plan.id)
    assert await get_plan(plan.id) is None
