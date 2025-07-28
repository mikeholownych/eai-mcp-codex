"""Business logic for plan management."""

from itertools import count
from typing import Dict, List, Optional

from .models import Plan


_counter = count(1)
_plans: Dict[int, Plan] = {}


def create_plan(name: str) -> Plan:
    """Create and store a new plan."""
    plan = Plan(id=next(_counter), name=name)
    _plans[plan.id] = plan
    return plan


def get_plan(plan_id: int) -> Optional[Plan]:
    """Retrieve a plan by ID if it exists."""
    return _plans.get(plan_id)


def list_plans() -> List[Plan]:
    """Return all known plans."""
    return list(_plans.values())


def delete_plan(plan_id: int) -> None:
    """Remove a plan from the store."""
    _plans.pop(plan_id, None)
