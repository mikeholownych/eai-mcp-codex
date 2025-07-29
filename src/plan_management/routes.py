"""API routes for the Plan Management service."""

from fastapi import APIRouter

from src.common.metrics import record_request

from .models import Plan, PlanRequest
from .plan_manager import get_plan_manager

router = APIRouter(prefix="/plans", tags=["plan-management"])


@router.post("/", response_model=Plan)
async def create_plan_route(request: PlanRequest) -> Plan:
    record_request("plan-management")
    manager = await get_plan_manager()
    return await manager.create_plan(request)


@router.get("/", response_model=list[Plan])
async def get_all_plans_route() -> list[Plan]:
    manager = await get_plan_manager()
    return await manager.list_plans()