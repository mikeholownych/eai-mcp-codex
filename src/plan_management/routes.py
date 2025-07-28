"""API routes for Plan Management."""

from fastapi import APIRouter

from .models import Plan

router = APIRouter()


@router.get("/plans/{plan_id}")
def get_plan(plan_id: int) -> Plan:
    return Plan(id=plan_id, name="sample")
