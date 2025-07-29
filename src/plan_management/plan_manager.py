"""Plan Management business logic implementation."""

import sqlite3
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path

from src.common.logging import get_logger
from .models import (
    Plan, Task, Milestone, PlanStatus, TaskStatus, 
    PlanRequest, TaskRequest, EstimationResult, PlanSummary
)

logger = get_logger("plan_manager")


class PlanManager:
    """Core business logic for plan management operations."""
    
    def __init__(self, db_path: str = "data/plans.db"):
        self.db_path = db_path
        self._ensure_database()
    
    def _ensure_database(self):
        """Create database and tables if they don't exist."""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS plans (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    status TEXT DEFAULT 'draft',
                    priority TEXT DEFAULT 'medium',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    start_date TIMESTAMP,
                    end_date TIMESTAMP,
                    estimated_hours REAL,
                    actual_hours REAL,
                    progress REAL DEFAULT 0.0,
                    metadata TEXT DEFAULT '{}',
                    created_by TEXT DEFAULT 'system',
                    assigned_to TEXT
                );
                
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    plan_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    status TEXT DEFAULT 'todo',
                    priority TEXT DEFAULT 'medium',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    start_date TIMESTAMP,
                    due_date TIMESTAMP,
                    estimated_hours REAL,
                    actual_hours REAL,
                    progress REAL DEFAULT 0.0,
                    dependencies TEXT DEFAULT '[]',
                    assignee TEXT,
                    tags TEXT DEFAULT '[]',
                    metadata TEXT DEFAULT '{}',
                    FOREIGN KEY (plan_id) REFERENCES plans (id)
                );
                
                CREATE TABLE IF NOT EXISTS milestones (
                    id TEXT PRIMARY KEY,
                    plan_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    target_date TIMESTAMP NOT NULL,
                    completion_date TIMESTAMP,
                    status TEXT DEFAULT 'pending',
                    criteria TEXT DEFAULT '[]',
                    progress REAL DEFAULT 0.0,
                    metadata TEXT DEFAULT '{}',
                    FOREIGN KEY (plan_id) REFERENCES plans (id)
                );
                
                CREATE INDEX IF NOT EXISTS idx_plans_status ON plans(status);
                CREATE INDEX IF NOT EXISTS idx_tasks_plan_id ON tasks(plan_id);
                CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
                CREATE INDEX IF NOT EXISTS idx_milestones_plan_id ON milestones(plan_id);
            """)
        
        logger.info(f"Database initialized at {self.db_path}")
    
    def create_plan(self, request: PlanRequest, created_by: str = "system") -> Plan:
        """Create a new plan."""
        plan_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
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
            created_by=created_by
        )
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO plans (
                    id, title, description, priority, created_at, updated_at,
                    start_date, estimated_hours, metadata, created_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                plan.id, plan.title, plan.description, plan.priority,
                plan.created_at.isoformat(), plan.updated_at.isoformat(),
                plan.start_date.isoformat() if plan.start_date else None,
                plan.estimated_hours, str(plan.metadata), plan.created_by
            ))
        
        logger.info(f"Created plan: {plan.id} - {plan.title}")
        return plan
    
    def get_plan(self, plan_id: str) -> Optional[Plan]:
        """Get a plan by ID."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM plans WHERE id = ?", (plan_id,))
            row = cursor.fetchone()
            
            if not row:
                return None
            
            return self._row_to_plan(row)
    
    def list_plans(
        self, 
        status: Optional[str] = None,
        created_by: Optional[str] = None,
        limit: int = 100
    ) -> List[Plan]:
        """List plans with optional filtering."""
        query = "SELECT * FROM plans WHERE 1=1"
        params = []
        
        if status:
            query += " AND status = ?"
            params.append(status)
        
        if created_by:
            query += " AND created_by = ?"
            params.append(created_by)
        
        query += " ORDER BY updated_at DESC LIMIT ?"
        params.append(limit)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)
            return [self._row_to_plan(row) for row in cursor.fetchall()]
    
    def update_plan(self, plan_id: str, updates: Dict[str, Any]) -> Optional[Plan]:
        """Update a plan with new values."""
        updates["updated_at"] = datetime.utcnow().isoformat()
        
        # Build dynamic update query
        set_clause = ", ".join(f"{key} = ?" for key in updates.keys())
        values = list(updates.values()) + [plan_id]
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(f"UPDATE plans SET {set_clause} WHERE id = ?", values)
            
            if conn.total_changes == 0:
                return None
        
        logger.info(f"Updated plan: {plan_id}")
        return self.get_plan(plan_id)
    
    def delete_plan(self, plan_id: str) -> bool:
        """Delete a plan and all associated tasks/milestones."""
        with sqlite3.connect(self.db_path) as conn:
            # Delete associated records first
            conn.execute("DELETE FROM tasks WHERE plan_id = ?", (plan_id,))
            conn.execute("DELETE FROM milestones WHERE plan_id = ?", (plan_id,))
            
            # Delete the plan
            cursor = conn.execute("DELETE FROM plans WHERE id = ?", (plan_id,))
            
            if cursor.rowcount > 0:
                logger.info(f"Deleted plan: {plan_id}")
                return True
            
            return False
    
    def add_task(self, plan_id: str, request: TaskRequest) -> Optional[Task]:
        """Add a task to a plan."""
        # Verify plan exists
        if not self.get_plan(plan_id):
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
            metadata=request.metadata
        )
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO tasks (
                    id, plan_id, title, description, priority, created_at, updated_at,
                    due_date, estimated_hours, dependencies, assignee, tags, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                task.id, task.plan_id, task.title, task.description, task.priority,
                task.created_at.isoformat(), task.updated_at.isoformat(),
                task.due_date.isoformat() if task.due_date else None,
                task.estimated_hours, str(task.dependencies), task.assignee,
                str(task.tags), str(task.metadata)
            ))
        
        logger.info(f"Added task: {task.id} to plan {plan_id}")
        return task
    
    def get_plan_tasks(self, plan_id: str) -> List[Task]:
        """Get all tasks for a plan."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM tasks WHERE plan_id = ? ORDER BY created_at",
                (plan_id,)
            )
            return [self._row_to_task(row) for row in cursor.fetchall()]
    
    def update_task_status(self, task_id: str, status: TaskStatus, progress: float = None) -> bool:
        """Update task status and optionally progress."""
        updates = {
            "status": status.value,
            "updated_at": datetime.utcnow().isoformat()
        }
        
        if progress is not None:
            updates["progress"] = min(1.0, max(0.0, progress))
        
        set_clause = ", ".join(f"{key} = ?" for key in updates.keys())
        values = list(updates.values()) + [task_id]
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(f"UPDATE tasks SET {set_clause} WHERE id = ?", values)
            
            if cursor.rowcount > 0:
                logger.info(f"Updated task status: {task_id} -> {status}")
                return True
            
            return False
    
    def estimate_plan(self, plan_id: str, method: str = "simple") -> Optional[EstimationResult]:
        """Estimate plan completion time using specified method."""
        plan = self.get_plan(plan_id)
        if not plan:
            return None
        
        tasks = self.get_plan_tasks(plan_id)
        
        if method == "simple":
            return self._simple_estimation(tasks)
        elif method == "three_point":
            return self._three_point_estimation(tasks)
        else:
            logger.warning(f"Unknown estimation method: {method}")
            return self._simple_estimation(tasks)
    
    def get_plan_summary(self, plan_id: str) -> Optional[PlanSummary]:
        """Get comprehensive plan summary with metrics."""
        plan = self.get_plan(plan_id)
        if not plan:
            return None
        
        tasks = self.get_plan_tasks(plan_id)
        milestones = self.get_plan_milestones(plan_id)
        
        completed_tasks = sum(1 for task in tasks if task.status == TaskStatus.DONE)
        overdue_tasks = sum(
            1 for task in tasks 
            if task.due_date and task.due_date < datetime.utcnow() and task.status != TaskStatus.DONE
        )
        
        # Get upcoming milestones (next 30 days)
        upcoming_date = datetime.utcnow() + timedelta(days=30)
        upcoming_milestones = [
            m for m in milestones 
            if m.target_date <= upcoming_date and m.status == "pending"
        ]
        
        # Estimate completion date
        remaining_hours = sum(
            task.estimated_hours or 0 for task in tasks 
            if task.status not in [TaskStatus.DONE, TaskStatus.CANCELLED]
        )
        
        estimated_completion = None
        if remaining_hours > 0:
            # Assume 8 hours per day, 5 days per week
            working_days = remaining_hours / 8
            estimated_completion = datetime.utcnow() + timedelta(days=working_days * 1.4)
        
        # Get team members
        team_members = list(set(
            task.assignee for task in tasks 
            if task.assignee
        ))
        
        return PlanSummary(
            plan=plan,
            task_count=len(tasks),
            completed_tasks=completed_tasks,
            overdue_tasks=overdue_tasks,
            upcoming_milestones=upcoming_milestones,
            estimated_completion=estimated_completion,
            team_members=team_members
        )
    
    def get_plan_milestones(self, plan_id: str) -> List[Milestone]:
        """Get all milestones for a plan."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM milestones WHERE plan_id = ? ORDER BY target_date",
                (plan_id,)
            )
            return [self._row_to_milestone(row) for row in cursor.fetchall()]
    
    def _simple_estimation(self, tasks: List[Task]) -> EstimationResult:
        """Simple sum of task estimates."""
        total_hours = sum(task.estimated_hours or 0 for task in tasks)
        
        task_estimates = {
            task.id: {
                "estimated_hours": task.estimated_hours or 0,
                "method": "user_provided"
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
                "Review estimates with team members"
            ]
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
                "pert_estimate": pert_estimate
            }
        
        return EstimationResult(
            method="three_point",
            total_estimated_hours=total_hours,
            task_estimates=task_estimates,
            confidence_level="high",
            recommendations=[
                "PERT estimation provides better accuracy",
                "Consider risk factors in pessimistic estimates",
                "Regular re-estimation as work progresses"
            ]
        )
    
    def _row_to_plan(self, row) -> Plan:
        """Convert database row to Plan object."""
        import json
        
        return Plan(
            id=row["id"],
            title=row["title"],
            description=row["description"] or "",
            status=PlanStatus(row["status"]),
            priority=row["priority"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
            start_date=datetime.fromisoformat(row["start_date"]) if row["start_date"] else None,
            end_date=datetime.fromisoformat(row["end_date"]) if row["end_date"] else None,
            estimated_hours=row["estimated_hours"],
            actual_hours=row["actual_hours"],
            progress=row["progress"] or 0.0,
            metadata=json.loads(row["metadata"] or "{}"),
            created_by=row["created_by"],
            assigned_to=row["assigned_to"]
        )
    
    def _row_to_task(self, row) -> Task:
        """Convert database row to Task object."""
        import json
        
        return Task(
            id=row["id"],
            plan_id=row["plan_id"],
            title=row["title"],
            description=row["description"] or "",
            status=TaskStatus(row["status"]),
            priority=row["priority"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
            start_date=datetime.fromisoformat(row["start_date"]) if row["start_date"] else None,
            due_date=datetime.fromisoformat(row["due_date"]) if row["due_date"] else None,
            estimated_hours=row["estimated_hours"],
            actual_hours=row["actual_hours"],
            progress=row["progress"] or 0.0,
            dependencies=json.loads(row["dependencies"] or "[]"),
            assignee=row["assignee"],
            tags=json.loads(row["tags"] or "[]"),
            metadata=json.loads(row["metadata"] or "{}")
        )
    
    def _row_to_milestone(self, row) -> Milestone:
        """Convert database row to Milestone object."""
        import json
        
        return Milestone(
            id=row["id"],
            plan_id=row["plan_id"],
            title=row["title"],
            description=row["description"] or "",
            target_date=datetime.fromisoformat(row["target_date"]),
            completion_date=datetime.fromisoformat(row["completion_date"]) if row["completion_date"] else None,
            status=row["status"],
            criteria=json.loads(row["criteria"] or "[]"),
            progress=row["progress"] or 0.0,
            metadata=json.loads(row["metadata"] or "{}")
        )


# Singleton instance
_plan_manager: Optional[PlanManager] = None


def get_plan_manager() -> PlanManager:
    """Get singleton PlanManager instance."""
    global _plan_manager
    if _plan_manager is None:
        _plan_manager = PlanManager()
    return _plan_manager
