from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from ..common.logging import get_logger

logger = get_logger("productivity_benchmark")


@dataclass
class ProductivityRecord:
    """Snapshot of agent productivity metrics."""

    agent_id: str
    tasks_completed: int
    tasks_failed: int
    average_execution_time: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Optional[str]] = field(default_factory=dict)


class AgentProductivityBenchmark:
    """Benchmark agent productivity using recorded metrics."""

    def __init__(self) -> None:
        self.records: List[ProductivityRecord] = []

    def record_metrics(self, agent_id: str, metrics: Dict[str, float]) -> None:
        """Record productivity metrics for an agent."""
        record = ProductivityRecord(
            agent_id=agent_id,
            tasks_completed=int(metrics.get("tasks_completed", 0)),
            tasks_failed=int(metrics.get("tasks_failed", 0)),
            average_execution_time=float(metrics.get("average_execution_time", 0.0)),
        )
        self.records.append(record)
        logger.debug("Recorded productivity metrics %s", record)

    def get_productivity_score(self, agent_id: str, since_hours: int = 1) -> float:
        """Return a productivity score (0-100) for the agent."""
        cutoff = datetime.utcnow() - timedelta(hours=since_hours)
        completed = failed = 0
        avg_time_total = 0.0
        count = 0
        for rec in self.records:
            if rec.agent_id == agent_id and rec.timestamp >= cutoff:
                completed += rec.tasks_completed
                failed += rec.tasks_failed
                avg_time_total += rec.average_execution_time
                count += 1

        if completed + failed == 0 or count == 0:
            return 0.0

        success_rate = completed / (completed + failed)
        avg_time = avg_time_total / count
        score = success_rate * 0.7 + (1.0 / (1.0 + avg_time)) * 0.3
        return score * 100

    def clear_old_records(self, older_than_hours: int = 24) -> None:
        """Remove records older than the given window."""
        cutoff = datetime.utcnow() - timedelta(hours=older_than_hours)
        self.records = [r for r in self.records if r.timestamp >= cutoff]
