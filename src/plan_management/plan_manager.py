"""Business logic for plan management."""

from itertools import count
from typing import Dict, List

from .models import Plan


_counter = count(1)
_plans: Dict[int, Plan] = {}


def create_plan(name: str) -> Plan:
    """Create and store a new plan."""
    plan = Plan(id=next(_counter), name=name)
    _plans[plan.id] = plan
    return plan


def list_plans() -> List[Plan]:
    """Return all known plans."""
    return list(_plans.values())
