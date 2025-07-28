"""Generate tasks for plans."""

from typing import List


def tasks(plan_id: int) -> List[str]:
    return [f"task-{plan_id}"]
