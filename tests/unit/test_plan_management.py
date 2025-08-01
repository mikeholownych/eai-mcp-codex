import pytest
from src.plan_management.plan_manager import (
    create_plan,
    delete_plan,
    get_plan,
    list_plans,
    PlanStatus,
)
from src.common.database import DatabaseManager
from src.common.tenant import tenant_context, async_tenant_context
import os

import pytest_asyncio


@pytest.fixture(autouse=True)
async def setup_and_teardown_db():
    os.environ["TESTING_MODE"] = "true"
    db_manager = DatabaseManager("plan_management_db")
    await db_manager.connect()
    yield
    await db_manager.disconnect()
    os.environ["TESTING_MODE"] = "false"


@pytest.mark.asyncio
async def test_update_plan_multi_tenant() -> None:
    with tenant_context("tenant_update_a"):
        plan = await create_plan("update_me")
        updated = await update_plan(plan.id, {"title": "updated"})
        assert updated is not None
        assert updated.title == "updated"

    with tenant_context("tenant_update_b"):
        # Attempt to update plan from another tenant should fail
        result = await update_plan(plan.id, {"title": "fail"})
        assert result is None

    with tenant_context("tenant_update_a"):
        await delete_plan(plan.id)
        assert await get_plan(plan.id) is None


@pytest.mark.asyncio
async def test_delete_plan_wrong_tenant() -> None:
    with tenant_context("tenant_del_a"):
        plan = await create_plan("to_delete")

    with tenant_context("tenant_del_b"):
        # Delete attempt from non-owner tenant should fail
        result = await delete_plan(plan.id)
        assert result is False

    with tenant_context("tenant_del_a"):
        assert await get_plan(plan.id) is not None
        await delete_plan(plan.id)
        assert await get_plan(plan.id) is None


@pytest.mark.asyncio
async def test_tenant_context_resets() -> None:
    """Ensure tenant_context restores previous tenant."""
    from src.common.tenant import get_current_tenant

    await delete_plan(plan.id)
    assert await get_plan(plan.id) is None
