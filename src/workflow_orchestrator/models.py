"""Data models for Workflow Orchestration."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class WorkflowStatus(str, Enum):
    """Workflow status enumeration."""

    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StepStatus(str, Enum):
    """Workflow step status enumeration."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"


class StepType(str, Enum):
    """Workflow step type enumeration."""

    MODEL_ROUTER = "model_router"
    PLAN_MANAGEMENT = "plan_management"
    GIT_WORKTREE = "git_worktree"
    VERIFICATION = "verification"
    FEEDBACK = "feedback"
    CUSTOM = "custom"


class ExecutionMode(str, Enum):
    """Workflow execution mode enumeration."""

    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    CONDITIONAL = "conditional"


class WorkflowStep(BaseModel):
    """Individual step in a workflow."""

    id: str
    workflow_id: str
    name: str
    description: str = ""
    step_type: StepType
    service_name: str  # Which microservice to call
    endpoint: str  # Which endpoint to call
    parameters: Dict[str, Any] = Field(default_factory=dict)
    expected_output: Optional[str] = None
    timeout_seconds: int = 300
    retry_count: int = 0
    max_retries: int = 3
    status: StepStatus = StepStatus.PENDING
    order: int = 0
    depends_on: List[str] = Field(default_factory=list)  # Step IDs this depends on
    conditions: Dict[str, Any] = Field(default_factory=dict)  # Conditional execution
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Workflow(BaseModel):
    """Complete workflow definition."""

    id: str
    name: str
    description: str = ""
    status: WorkflowStatus = WorkflowStatus.DRAFT
    execution_mode: ExecutionMode = ExecutionMode.SEQUENTIAL
    priority: str = "medium"  # low, medium, high, urgent
    created_by: str = "system"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    steps: List[WorkflowStep] = Field(default_factory=list)
    global_parameters: Dict[str, Any] = Field(default_factory=dict)
    success_criteria: Dict[str, Any] = Field(default_factory=dict)
    failure_handling: Dict[str, Any] = Field(default_factory=dict)
    notifications: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class WorkflowExecution(BaseModel):
    """Workflow execution record."""

    id: str
    workflow_id: str
    execution_number: int  # Incremental execution number
    status: WorkflowStatus
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    triggered_by: str = "system"
    execution_context: Dict[str, Any] = Field(default_factory=dict)
    step_results: Dict[str, Any] = Field(default_factory=dict)  # step_id -> result
    total_steps: int = 0
    completed_steps: int = 0
    failed_steps: int = 0
    skipped_steps: int = 0
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class WorkflowRequest(BaseModel):
    """Request to create or execute a workflow."""

    name: str
    description: str = ""
    execution_mode: ExecutionMode = ExecutionMode.SEQUENTIAL
    priority: str = "medium"
    steps: List[Dict[str, Any]] = Field(default_factory=list)
    global_parameters: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class StepExecutionResult(BaseModel):
    """Result of executing a workflow step."""

    step_id: str
    status: StepStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    execution_time_ms: Optional[float] = None
    output_data: Optional[Any] = None
    logs: List[str] = Field(default_factory=list)


class WorkflowTemplate(BaseModel):
    """Reusable workflow template."""

    id: str
    name: str
    description: str = ""
    category: str = "general"
    template_version: str = "1.0"
    author: str = "system"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    step_templates: List[Dict[str, Any]] = Field(default_factory=list)
    default_parameters: Dict[str, Any] = Field(default_factory=dict)
    required_parameters: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    usage_count: int = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)
