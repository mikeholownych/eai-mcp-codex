"""Task generation utilities for plans."""

from typing import List


def tasks(plan_id: int) -> List[str]:
    """Return the list of tasks required for a plan."""
    return [f"{plan_id}-build", f"{plan_id}-test", f"{plan_id}-deploy"]
