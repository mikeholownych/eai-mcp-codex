"""Data models for Plan Management."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel, Field


class PlanStatus(str, Enum):
    """Plan status enumeration."""
    DRAFT = "draft"
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TaskStatus(str, Enum):
    """Task status enumeration."""
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    IN_REVIEW = "in_review"
    DONE = "done"
    CANCELLED = "cancelled"


class EstimationMethod(str, Enum):
    """Estimation methodology enumeration."""
    PLANNING_POKER = "planning_poker"
    THREE_POINT = "three_point"
    HISTORICAL = "historical"
    SIMPLE = "simple"


class Plan(BaseModel):
    """Project plan model."""
    id: str
    title: str
    description: str = ""
    status: PlanStatus = PlanStatus.DRAFT
    priority: str = "medium"  # low, medium, high, urgent
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    estimated_hours: Optional[float] = None
    actual_hours: Optional[float] = None
    progress: float = 0.0  # 0.0 to 1.0
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_by: str = "system"
    assigned_to: Optional[str] = None


class Task(BaseModel):
    """Task model."""
    id: str
    plan_id: str
    title: str
    description: str = ""
    status: TaskStatus = TaskStatus.TODO
    priority: str = "medium"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    start_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    estimated_hours: Optional[float] = None
    actual_hours: Optional[float] = None
    progress: float = 0.0  # 0.0 to 1.0
    dependencies: List[str] = Field(default_factory=list)  # task IDs
    assignee: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Milestone(BaseModel):
    """Milestone model."""
    id: str
    plan_id: str
    title: str
    description: str = ""
    target_date: datetime
    completion_date: Optional[datetime] = None
    status: str = "pending"  # pending, achieved, missed
    criteria: List[str] = Field(default_factory=list)
    progress: float = 0.0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PlanRequest(BaseModel):
    """Request model for creating/updating plans."""
    title: str
    description: str = ""
    priority: str = "medium"
    start_date: Optional[datetime] = None
    estimated_hours: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TaskRequest(BaseModel):
    """Request model for creating/updating tasks."""
    title: str
    description: str = ""
    priority: str = "medium"
    estimated_hours: Optional[float] = None
    due_date: Optional[datetime] = None
    dependencies: List[str] = Field(default_factory=list)
    assignee: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class EstimationResult(BaseModel):
    """Result of plan estimation."""
    method: str
    total_estimated_hours: float
    task_estimates: Dict[str, Any]
    confidence_level: str
    recommendations: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PlanSummary(BaseModel):
    """Summary of a plan with key metrics."""
    plan: Plan
    task_count: int
    completed_tasks: int
    overdue_tasks: int
    upcoming_milestones: List[Milestone]
    estimated_completion: Optional[datetime] = None
    team_members: List[str] = Field(default_factory=list)
