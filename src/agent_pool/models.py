"""Agent Pool data models."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class AgentType(str, Enum):
    """Types of agents in the pool."""

    PLANNER = "planner"
    ARCHITECT = "architect"
    DEVELOPER = "developer"
    SECURITY = "security"
    QA = "qa"
    DOMAIN_EXPERT = "domain_expert"
    CODE_REVIEWER = "code_reviewer"


class AgentState(str, Enum):
    """Agent execution states."""

    IDLE = "idle"
    WORKING = "working"
    WAITING = "waiting"
    ERROR = "error"
    MAINTENANCE = "maintenance"


class TaskPriority(str, Enum):
    """Task priority levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class AgentInstance(BaseModel):
    """Individual agent instance in the pool."""

    instance_id: UUID = Field(default_factory=uuid4)
    agent_type: AgentType
    agent_name: str
    state: AgentState = AgentState.IDLE
    current_task_id: Optional[UUID] = None
    capabilities: List[str] = Field(default_factory=list)
    workload: int = 0  # Number of active tasks
    max_concurrent_tasks: int = 3
    last_activity: datetime = Field(default_factory=datetime.utcnow)
    performance_metrics: Dict[str, float] = Field(default_factory=dict)
    configuration: Dict[str, Any] = Field(default_factory=dict)


class TaskRequest(BaseModel):
    """Task request for agent execution."""

    task_id: UUID = Field(default_factory=uuid4)
    task_type: str
    description: str
    priority: TaskPriority = TaskPriority.MEDIUM
    required_agent_type: AgentType
    required_capabilities: List[str] = Field(default_factory=list)
    payload: Dict[str, Any]
    deadline: Optional[datetime] = None
    context: Dict[str, Any] = Field(default_factory=dict)
    callback_url: Optional[str] = None


class TaskResult(BaseModel):
    """Task execution result."""

    task_id: UUID
    agent_instance_id: UUID
    status: str  # "completed", "failed", "partial"
    result: Dict[str, Any]
    error_message: Optional[str] = None
    execution_time: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metrics: Dict[str, Any] = Field(default_factory=dict)


class AgentPoolConfig(BaseModel):
    """Agent pool configuration."""

    max_agents_per_type: Dict[AgentType, int] = Field(
        default_factory=lambda: {
            AgentType.PLANNER: 2,
            AgentType.ARCHITECT: 3,
            AgentType.DEVELOPER: 10,
            AgentType.SECURITY: 2,
            AgentType.QA: 3,
            AgentType.DOMAIN_EXPERT: 5,
            AgentType.CODE_REVIEWER: 5,
        }
    )
    auto_scaling_enabled: bool = True
    scale_up_threshold: float = 0.8  # Scale up when utilization > 80%
    scale_down_threshold: float = 0.3  # Scale down when utilization < 30%
    min_idle_agents: int = 1
    task_timeout: int = 1800  # 30 minutes default
    heartbeat_interval: int = 30  # seconds


class WorkloadDistribution(BaseModel):
    """Workload distribution across agent types."""

    agent_type: AgentType
    total_instances: int
    active_instances: int
    idle_instances: int
    working_instances: int
    pending_tasks: int
    utilization_rate: float
    average_response_time: float
