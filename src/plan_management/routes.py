"""API routes for the Plan Management service."""

from fastapi import APIRouter

from src.common.metrics import record_request

from .models import Plan
from .plan_manager import create_plan, list_plans

router = APIRouter(prefix="/plans", tags=["plan-management"])


@router.post("/", response_model=Plan)
def create(name: str) -> Plan:
    record_request("plan-management")
    return create_plan(name)


@router.get("/", response_model=list[Plan])
def get_all() -> list[Plan]:
    return list_plans()
