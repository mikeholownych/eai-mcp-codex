"""Plan Management business logic implementation."""

import uuid
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from src.common.logging import get_logger
from src.common.database import (
    DatabaseManager,
    serialize_json_field,
    deserialize_json_field,
    serialize_datetime,
    deserialize_datetime,
)
from src.common.tenant import get_current_tenant
from .models import (
    Plan,
    Task,
    Milestone,
    PlanStatus,
    TaskStatus,
    PlanRequest,
    TaskRequest,
    EstimationResult,
    PlanSummary,
)
from .config import settings

logger = get_logger("plan_manager")


class PlanManager:
    """Core business logic for plan management operations."""

    def __init__(self, dsn: str = settings.database_url):
        self.db_manager = DatabaseManager(dsn)
        self.dsn = dsn  # Store DSN for potential re-initialization if needed
        self._testing_mode = os.getenv("TESTING_MODE") == "true"
        # Simple in-memory store used when running unit tests
        self._plans: Dict[str, Plan] = {}
        # Initialize database connection pool on startup
        # This will be called by the FastAPI app's startup event

    async def initialize_database(self):
        """Initialize database connection and create tables if they don't exist."""
        await self.db_manager.connect()
        await self._ensure_database()

    async def shutdown_database(self):
        """Shutdown database connection pool."""
        await self.db_manager.disconnect()

    async def _ensure_database(self):
        """Create database and tables if they don't exist."""
        script = """
                CREATE TABLE IF NOT EXISTS plans (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    status TEXT DEFAULT 'draft',
                    priority TEXT DEFAULT 'medium',
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    start_date TIMESTAMP WITH TIME ZONE,
                    end_date TIMESTAMP WITH TIME ZONE,
                    estimated_hours REAL,
                    actual_hours REAL,
                    progress REAL DEFAULT 0.0,
                    metadata JSONB DEFAULT '{}',
                    created_by TEXT DEFAULT 'system',
                    assigned_to TEXT,
                    tenant_id TEXT DEFAULT 'public'
                );
                
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    plan_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    status TEXT DEFAULT 'todo',
                    priority TEXT DEFAULT 'medium',
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    start_date TIMESTAMP WITH TIME ZONE,
                    due_date TIMESTAMP WITH TIME ZONE,
                    estimated_hours REAL,
                    actual_hours REAL,
                    progress REAL DEFAULT 0.0,
                    dependencies JSONB DEFAULT '[]',
                    assignee TEXT,
                    tags JSONB DEFAULT '[]',
                    metadata JSONB DEFAULT '{}',
                    FOREIGN KEY (plan_id) REFERENCES plans (id) ON DELETE CASCADE
                );
                
                CREATE TABLE IF NOT EXISTS milestones (
                    id TEXT PRIMARY KEY,
                    plan_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    target_date TIMESTAMP WITH TIME ZONE NOT NULL,
                    completion_date TIMESTAMP WITH TIME ZONE,
                    status TEXT DEFAULT 'pending',
                    criteria JSONB DEFAULT '[]',
                    progress REAL DEFAULT 0.0,
                    metadata JSONB DEFAULT '{}',
                    FOREIGN KEY (plan_id) REFERENCES plans (id) ON DELETE CASCADE
                );
                
                CREATE INDEX IF NOT EXISTS idx_plans_status ON plans(status);
                CREATE INDEX IF NOT EXISTS idx_plans_tenant ON plans(tenant_id);
                CREATE INDEX IF NOT EXISTS idx_tasks_plan_id ON tasks(plan_id);
                CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
                CREATE INDEX IF NOT EXISTS idx_milestones_plan_id ON milestones(plan_id);
            """
        logger.info(f"Attempting to create tables in {self.dsn}")
        await self.db_manager.execute_script(script)
        logger.info("Database tables ensured.")

    async def create_plan(
        self,
        request: PlanRequest,
        created_by: str = "system",
        tenant_id: str | None = None,
    ) -> Plan:
        """Create a new plan."""
        plan_id = str(uuid.uuid4())
        now = datetime.utcnow()

        tenant = tenant_id or request.tenant_id or get_current_tenant()

        plan = Plan(
            id=plan_id,
            title=request.title,
            description=request.description,
            priority=request.priority,
            created_at=now,
            updated_at=now,
            start_date=request.start_date,
            estimated_hours=request.estimated_hours,
            metadata=request.metadata,
            created_by=created_by,
            tenant_id=tenant,
        )

        if self._testing_mode:
            self._plans[plan.id] = plan
        else:
            query = """
                INSERT INTO plans (
                    id, title, description, status, priority, created_at, updated_at,
                    start_date, estimated_hours, metadata, created_by, tenant_id
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
            """
            values = (
                plan.id,
                plan.title,
                plan.description,
                plan.status.value,
                plan.priority,
                serialize_datetime(plan.created_at),
                serialize_datetime(plan.updated_at),
                serialize_datetime(plan.start_date),
                plan.estimated_hours,
                serialize_json_field(plan.metadata),
                plan.created_by,
                plan.tenant_id,
            )
            await self.db_manager.execute_update(query, values)

        logger.info(f"Created plan: {plan.id} - {plan.title}")
        return plan

    async def get_plan(
        self, plan_id: str, tenant_id: str | None = None
    ) -> Optional[Plan]:
        """Get a plan by ID scoped to the current tenant."""
        tenant = tenant_id or get_current_tenant()
        if self._testing_mode:
            plan = self._plans.get(plan_id)
            if plan and plan.tenant_id == tenant:
                return plan
            return None

        query = "SELECT * FROM plans WHERE id = $1 AND tenant_id = $2"
        row = await self.db_manager.execute_query(query, (plan_id, tenant))

        if not row:
            return None

        return self._row_to_plan(row[0])

    async def list_plans(
        self,
        status: Optional[str] = None,
        created_by: Optional[str] = None,
        limit: int = 100,
        tenant_id: str | None = None,
    ) -> List[Plan]:
        """List plans with optional filtering."""
        tenant = tenant_id or get_current_tenant()

        if self._testing_mode:
            plans = [p for p in self._plans.values() if p.tenant_id == tenant]
            if status:
                plans = [p for p in plans if p.status.value == status]
            if created_by:
                plans = [p for p in plans if p.created_by == created_by]
            plans.sort(key=lambda p: p.updated_at, reverse=True)
            return plans[:limit]

        query = "SELECT * FROM plans WHERE tenant_id = $1"
        params = [tenant]
        param_idx = 2

        if status:
            query += f" AND status = ${param_idx}"
            params.append(status)
            param_idx += 1

        if created_by:
            query += f" AND created_by = ${param_idx}"
            params.append(created_by)
            param_idx += 1

        query += f" ORDER BY updated_at DESC LIMIT ${param_idx}"
        params.append(limit)

        rows = await self.db_manager.execute_query(query, tuple(params))
        return [self._row_to_plan(row) for row in rows]

    async def update_plan(
        self, plan_id: str, updates: Dict[str, Any], tenant_id: str | None = None
    ) -> Optional[Plan]:
        """Update a plan with new values."""
        updates["updated_at"] = datetime.utcnow()

        set_clauses = []
        values = []
        param_idx = 1

        for key, value in updates.items():
            if key in ["created_at", "updated_at", "start_date", "end_date"]:
                value = serialize_datetime(value)
            elif key in ["metadata"]:
                value = serialize_json_field(value)
            set_clauses.append(f"{key} = ${param_idx}")
            values.append(value)
            param_idx += 1

        set_clause = ", ".join(set_clauses)

        tenant = tenant_id or get_current_tenant()

        if self._testing_mode:
            plan = self._plans.get(plan_id)
            if not plan or plan.tenant_id != tenant:
                return None
            for key, value in updates.items():
                setattr(plan, key, value)
            self._plans[plan_id] = plan
            return plan

        query = f"UPDATE plans SET {set_clause} WHERE id = ${param_idx} AND tenant_id = ${param_idx + 1}"
        values.extend([plan_id, tenant])

        rows_affected = await self.db_manager.execute_update(query, tuple(values))

        if rows_affected == 0:
            return None

        logger.info(f"Updated plan: {plan_id}")
        return await self.get_plan(plan_id, tenant)

    async def delete_plan(self, plan_id: str, tenant_id: str | None = None) -> bool:
        """Delete a plan and all associated tasks/milestones."""
        # ON DELETE CASCADE in table definition handles tasks and milestones
        tenant = tenant_id or get_current_tenant()

        if self._testing_mode:
            plan = self._plans.get(plan_id)
            if plan and plan.tenant_id == tenant:
                del self._plans[plan_id]
                return True
            return False

        query = "DELETE FROM plans WHERE id = $1 AND tenant_id = $2"
        rows_affected = await self.db_manager.execute_update(query, (plan_id, tenant))

        if rows_affected > 0:
            logger.info(f"Deleted plan: {plan_id}")
            return True

        return False

    async def add_task(self, plan_id: str, request: TaskRequest) -> Optional[Task]:
        """Add a task to a plan."""
        # Verify plan exists
        if not await self.get_plan(plan_id):
            logger.error(f"Plan not found: {plan_id}")
            return None

        task_id = str(uuid.uuid4())
        now = datetime.utcnow()

        task = Task(
            id=task_id,
            plan_id=plan_id,
            title=request.title,
            description=request.description,
            priority=request.priority,
            created_at=now,
            updated_at=now,
            due_date=request.due_date,
            estimated_hours=request.estimated_hours,
            dependencies=request.dependencies,
            assignee=request.assignee,
            tags=request.tags,
            metadata=request.metadata,
        )

        query = """
            INSERT INTO tasks (
                id, plan_id, title, description, status, priority, created_at, updated_at,
                due_date, estimated_hours, dependencies, assignee, tags, metadata
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
        """
        values = (
            task.id,
            task.plan_id,
            task.title,
            task.description,
            task.status.value,
            task.priority,
            serialize_datetime(task.created_at),
            serialize_datetime(task.updated_at),
            serialize_datetime(task.due_date),
            task.estimated_hours,
            serialize_json_field(task.dependencies),
            task.assignee,
            serialize_json_field(task.tags),
            serialize_json_field(task.metadata),
        )
        await self.db_manager.execute_update(query, values)

        logger.info(f"Added task: {task.id} to plan {plan_id}")
        return task

    async def get_plan_tasks(self, plan_id: str) -> List[Task]:
        """Get all tasks for a plan."""
        query = "SELECT * FROM tasks WHERE plan_id = $1 ORDER BY created_at"
        rows = await self.db_manager.execute_query(query, (plan_id,))
        return [self._row_to_task(row) for row in rows]

    async def update_task_status(
        self, task_id: str, status: TaskStatus, progress: Optional[float] = None
    ) -> bool:
        """Update task status and optionally progress."""
        updates = {"status": status.value, "updated_at": datetime.utcnow()}

        if progress is not None:
            updates["progress"] = min(1.0, max(0.0, progress))

        set_clauses = []
        values = []
        param_idx = 1

        for key, value in updates.items():
            if key in ["updated_at"]:
                value = serialize_datetime(value)
            set_clauses.append(f"{key} = ${param_idx}")
            values.append(value)
            param_idx += 1

        set_clause = ", ".join(set_clauses)

        query = f"UPDATE tasks SET {set_clause} WHERE id = ${param_idx}"
        values.append(task_id)

        rows_affected = await self.db_manager.execute_update(query, tuple(values))

        if rows_affected > 0:
            logger.info(f"Updated task status: {task_id} -> {status}")
            return True

        return False

    async def estimate_plan(
        self, plan_id: str, method: str = "simple"
    ) -> Optional[EstimationResult]:
        """Estimate plan completion time using specified method."""
        plan = await self.get_plan(plan_id)
        if not plan:
            return None

        tasks = await self.get_plan_tasks(plan_id)

        if method == "simple":
            return self._simple_estimation(tasks)
        elif method == "three_point":
            return self._three_point_estimation(tasks)
        else:
            logger.warning(f"Unknown estimation method: {method}")
            return self._simple_estimation(tasks)

    async def get_plan_summary(self, plan_id: str) -> Optional[PlanSummary]:
        """Get comprehensive plan summary with metrics."""
        plan = await self.get_plan(plan_id)
        if not plan:
            return None

        tasks = await self.get_plan_tasks(plan_id)
        milestones = await self.get_plan_milestones(plan_id)

        completed_tasks = sum(1 for task in tasks if task.status == TaskStatus.DONE)
        overdue_tasks = sum(
            1
            for task in tasks
            if task.due_date
            and task.due_date < datetime.utcnow()
            and task.status != TaskStatus.DONE
        )

        # Get upcoming milestones (next 30 days)
        upcoming_date = datetime.utcnow() + timedelta(days=30)
        upcoming_milestones = [
            m
            for m in milestones
            if m.target_date <= upcoming_date and m.status == "pending"
        ]

        # Estimate completion date
        remaining_hours = sum(
            task.estimated_hours or 0
            for task in tasks
            if task.status not in [TaskStatus.DONE, TaskStatus.CANCELLED]
        )

        estimated_completion = None
        if remaining_hours > 0:
            # Assume 8 hours per day, 5 days per week
            working_days = remaining_hours / 8
            estimated_completion = datetime.utcnow() + timedelta(
                days=working_days * 1.4
            )

        # Get team members
        team_members = list(set(task.assignee for task in tasks if task.assignee))

        return PlanSummary(
            plan=plan,
            task_count=len(tasks),
            completed_tasks=completed_tasks,
            overdue_tasks=overdue_tasks,
            upcoming_milestones=upcoming_milestones,
            estimated_completion=estimated_completion,
            team_members=team_members,
        )

    async def get_plan_milestones(self, plan_id: str) -> List[Milestone]:
        """Get all milestones for a plan."""
        query = "SELECT * FROM milestones WHERE plan_id = $1 ORDER BY target_date"
        rows = await self.db_manager.execute_query(query, (plan_id,))
        return [self._row_to_milestone(row) for row in rows]

    def _simple_estimation(self, tasks: List[Task]) -> EstimationResult:
        """Simple sum of task estimates."""
        total_hours = sum(task.estimated_hours or 0 for task in tasks)

        task_estimates = {
            task.id: {
                "estimated_hours": task.estimated_hours or 0,
                "method": "user_provided",
            }
            for task in tasks
        }

        return EstimationResult(
            method="simple",
            total_estimated_hours=total_hours,
            task_estimates=task_estimates,
            confidence_level="medium",
            recommendations=[
                "Consider breaking down large tasks (>8 hours)",
                "Add buffer time for unknown complexities",
                "Review estimates with team members",
            ],
        )

    def _three_point_estimation(self, tasks: List[Task]) -> EstimationResult:
        """Three-point estimation (optimistic, most likely, pessimistic)."""
        total_hours = 0
        task_estimates = {}

        for task in tasks:
            base_estimate = task.estimated_hours or 8
            optimistic = base_estimate * 0.7
            most_likely = base_estimate
            pessimistic = base_estimate * 1.5

            # PERT formula: (O + 4M + P) / 6
            pert_estimate = (optimistic + 4 * most_likely + pessimistic) / 6
            total_hours += pert_estimate

            task_estimates[task.id] = {
                "optimistic": optimistic,
                "most_likely": most_likely,
                "pessimistic": pessimistic,
                "pert_estimate": pert_estimate,
            }

        return EstimationResult(
            method="three_point",
            total_estimated_hours=total_hours,
            task_estimates=task_estimates,
            confidence_level="high",
            recommendations=[
                "PERT estimation provides better accuracy",
                "Consider risk factors in pessimistic estimates",
                "Regular re-estimation as work progresses",
            ],
        )

    def _row_to_plan(self, row) -> Plan:
        """Convert database row to Plan object."""
        return Plan(
            id=row["id"],
            title=row["title"],
            description=row["description"] or "",
            status=PlanStatus(row["status"]),
            priority=row["priority"],
            created_at=deserialize_datetime(row["created_at"]),
            updated_at=deserialize_datetime(row["updated_at"]),
            start_date=deserialize_datetime(row["start_date"]),
            end_date=deserialize_datetime(row["end_date"]),
            estimated_hours=row["estimated_hours"],
            actual_hours=row["actual_hours"],
            progress=row["progress"] or 0.0,
            metadata=deserialize_json_field(row["metadata"]),
            created_by=row["created_by"],
            assigned_to=row["assigned_to"],
            tenant_id=row["tenant_id"],
        )

    def _row_to_task(self, row) -> Task:
        """Convert database row to Task object."""
        return Task(
            id=row["id"],
            plan_id=row["plan_id"],
            title=row["title"],
            description=row["description"] or "",
            status=TaskStatus(row["status"]),
            priority=row["priority"],
            created_at=deserialize_datetime(row["created_at"]),
            updated_at=deserialize_datetime(row["updated_at"]),
            start_date=deserialize_datetime(row["start_date"]),
            due_date=deserialize_datetime(row["due_date"]),
            estimated_hours=row["estimated_hours"],
            actual_hours=row["actual_hours"],
            progress=row["progress"] or 0.0,
            dependencies=deserialize_json_field(row["dependencies"]),
            assignee=row["assignee"],
            tags=deserialize_json_field(row["tags"]),
            metadata=deserialize_json_field(row["metadata"]),
        )

    def _row_to_milestone(self, row) -> Milestone:
        """Convert database row to Milestone object."""
        return Milestone(
            id=row["id"],
            plan_id=row["plan_id"],
            title=row["title"],
            description=row["description"] or "",
            target_date=deserialize_datetime(row["target_date"]),
            completion_date=deserialize_datetime(row["completion_date"]),
            status=row["status"],
            criteria=deserialize_json_field(row["criteria"]),
            progress=row["progress"] or 0.0,
            metadata=deserialize_json_field(row["metadata"]),
        )


# Singleton instance
_plan_manager: Optional[PlanManager] = None


async def get_plan_manager() -> PlanManager:
    """Get singleton PlanManager instance."""
    global _plan_manager
    if _plan_manager is None:
        _plan_manager = PlanManager()
        await _plan_manager.initialize_database()
    return _plan_manager


# Convenience functions for backward compatibility
async def create_plan(title: str, description: str = "", **kwargs) -> Plan:
    """Create a new plan."""
    request = PlanRequest(title=title, description=description, **kwargs)
    manager = await get_plan_manager()
    return await manager.create_plan(request)


async def get_plan(plan_id: str) -> Optional[Plan]:
    """Get a plan by ID."""
    manager = await get_plan_manager()
    return await manager.get_plan(plan_id)


async def list_plans() -> List[Plan]:
    """List all plans."""
    manager = await get_plan_manager()
    return await manager.list_plans()


async def delete_plan(plan_id: str) -> bool:
    """Delete a plan."""
    manager = await get_plan_manager()
    return await manager.delete_plan(plan_id)


async def update_plan(plan_id: str, updates: Dict[str, Any]) -> Optional[Plan]:
    """Update a plan."""
    manager = await get_plan_manager()
    return await manager.update_plan(plan_id, updates)
