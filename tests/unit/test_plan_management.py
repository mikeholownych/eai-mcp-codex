import pytest
from src.plan_management.plan_manager import (
    create_plan,
    delete_plan,
    get_plan,
    list_plans,
    update_plan,
)
from src.common.database import DatabaseManager
from src.common.tenant import tenant_context, async_tenant_context
import os

import pytest_asyncio


@pytest_asyncio.fixture(autouse=True)
async def setup_and_teardown_db() -> None:
    os.environ["TESTING_MODE"] = "true"
    db_manager = DatabaseManager("plan_management_db")
    await db_manager.connect()
    yield
    await db_manager.disconnect()
    os.environ["TESTING_MODE"] = "false"


@pytest.mark.asyncio
async def test_create_plan_multi_tenant() -> None:
    with tenant_context("tenant_a"):
        plan_a = await create_plan("test_a")
    with tenant_context("tenant_b"):
        plan_b = await create_plan("test_b")

    with tenant_context("tenant_a"):
        assert await get_plan(plan_a.id) == plan_a
        plans_a = await list_plans()
        assert plan_a in plans_a
        assert plan_b not in plans_a

    with tenant_context("tenant_b"):
        assert await get_plan(plan_b.id) == plan_b
        plans_b = await list_plans()
        assert plan_b in plans_b
        assert plan_a not in plans_b

    with tenant_context("tenant_a"):
        await delete_plan(plan_a.id)
        assert await get_plan(plan_a.id) is None
    with tenant_context("tenant_b"):
        await delete_plan(plan_b.id)
        assert await get_plan(plan_b.id) is None


@pytest.mark.asyncio
async def test_async_tenant_context() -> None:
    async with async_tenant_context("tenant_async"):
        plan = await create_plan("async_plan")
        assert plan.tenant_id == "tenant_async"
        assert await get_plan(plan.id) == plan
    assert await get_plan(plan.id) is None
    async with async_tenant_context("tenant_async"):
        await delete_plan(plan.id)


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


def test_tenant_context_resets() -> None:
    """Ensure tenant_context restores previous tenant."""
    from src.common.tenant import get_current_tenant

    assert get_current_tenant() == "public"
    with tenant_context("tenant_reset"):
        assert get_current_tenant() == "tenant_reset"
    assert get_current_tenant() == "public"
