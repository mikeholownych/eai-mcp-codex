import pytest
from src.plan_management.plan_manager import create_plan

# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))


@pytest.mark.asyncio
async def test_plan_manager_scalability():
    plans = [await create_plan(f"p{i}") for i in range(100)]
    assert len(plans) == 100
