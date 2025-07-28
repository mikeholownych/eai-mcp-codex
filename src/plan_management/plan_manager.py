"""Plan management logic."""

from .models import Plan


def create_plan(name: str) -> Plan:
    return Plan(id=1, name=name)
