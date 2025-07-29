"""Collaboration Orchestrator data models."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class CollaborationStatus(str, Enum):
    """Status of a collaboration session."""
    INITIATED = "initiated"
    ACTIVE = "active"
    CONSENSUS_BUILDING = "consensus_building"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


class ParticipantRole(str, Enum):
    """Roles participants can have in collaboration."""
    LEAD = "lead"
    CONTRIBUTOR = "contributor"
    REVIEWER = "reviewer"
    OBSERVER = "observer"


class DecisionType(str, Enum):
    """Types of decisions requiring consensus."""
    ARCHITECTURE = "architecture"
    TECHNOLOGY = "technology"
    APPROACH = "approach"
    PRIORITY = "priority"
    APPROVAL = "approval"


class VoteChoice(str, Enum):
    """Vote choices for consensus items."""
    APPROVE = "approve"
    REJECT = "reject"
    ABSTAIN = "abstain"
    NEEDS_REVISION = "needs_revision"


class CollaborationSession(BaseModel):
    """A collaboration session between multiple agents."""
    session_id: UUID = Field(default_factory=uuid4)
    title: str
    description: str
    status: CollaborationStatus = CollaborationStatus.INITIATED
    participants: List[str] = Field(default_factory=list)  # agent IDs
    participant_roles: Dict[str, ParticipantRole] = Field(default_factory=dict)
    lead_agent: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    deadline: Optional[datetime] = None
    context: Dict[str, Any] = Field(default_factory=dict)
    outputs: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CollaborationInvitation(BaseModel):
    """Invitation to participate in a collaboration."""
    invitation_id: UUID = Field(default_factory=uuid4)
    session_id: UUID
    invited_agent: str
    invited_by: str
    role: ParticipantRole = ParticipantRole.CONTRIBUTOR
    message: str
    capabilities_required: List[str] = Field(default_factory=list)
    expected_contribution: str
    deadline: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class CollaborationResponse(BaseModel):
    """Response to a collaboration invitation."""
    invitation_id: UUID
    agent_id: str
    accepted: bool
    message: Optional[str] = None
    available_capabilities: List[str] = Field(default_factory=list)
    availability_window: Optional[Dict[str, datetime]] = None
    conditions: List[str] = Field(default_factory=list)
    responded_at: datetime = Field(default_factory=datetime.utcnow)


class ConsensusDecision(BaseModel):
    """A decision requiring consensus among participants."""
    decision_id: UUID = Field(default_factory=uuid4)
    session_id: UUID
    decision_type: DecisionType
    title: str
    description: str
    options: List[str]
    votes: Dict[str, VoteChoice] = Field(default_factory=dict)  # agent_id -> vote
    comments: Dict[str, str] = Field(default_factory=dict)  # agent_id -> comment
    required_consensus: float = 0.75  # 75% consensus required
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    voting_deadline: Optional[datetime] = None
    resolved: bool = False
    resolution: Optional[str] = None
    resolved_at: Optional[datetime] = None


class WorkflowStep(BaseModel):
    """A step in a collaborative workflow."""
    step_id: UUID = Field(default_factory=uuid4)
    session_id: UUID
    step_number: int
    title: str
    description: str
    assigned_agent: Optional[str] = None
    required_capabilities: List[str] = Field(default_factory=list)
    dependencies: List[UUID] = Field(default_factory=list)  # other step IDs
    status: str = "pending"  # pending, in_progress, completed, blocked
    inputs: Dict[str, Any] = Field(default_factory=dict)
    outputs: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    estimated_duration: Optional[int] = None  # minutes


class CollaborationMetrics(BaseModel):
    """Metrics for a collaboration session."""
    session_id: UUID
    total_participants: int
    active_participants: int
    messages_exchanged: int
    decisions_made: int
    consensus_achieved: int
    consensus_rate: float
    average_response_time: float  # minutes
    total_duration: Optional[float] = None  # minutes
    efficiency_score: float = 0.0
    quality_score: float = 0.0
    participant_satisfaction: Dict[str, float] = Field(default_factory=dict)


class EscalationRequest(BaseModel):
    """Request to escalate an issue to higher-level agents."""
    escalation_id: UUID = Field(default_factory=uuid4)
    session_id: UUID
    issue_type: str  # "consensus_failure", "technical_dispute", "resource_conflict"
    description: str
    affected_participants: List[str]
    escalated_by: str
    escalated_to: Optional[str] = None  # target agent or "management"
    priority: str = "medium"  # low, medium, high, urgent
    context: Dict[str, Any] = Field(default_factory=dict)
    resolution_deadline: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    resolved: bool = False
    resolution: Optional[str] = None
    resolved_at: Optional[datetime] = None


class CollaborationTemplate(BaseModel):
    """Template for common collaboration patterns."""
    template_id: UUID = Field(default_factory=uuid4)
    name: str
    description: str
    category: str  # "code_review", "architecture_design", "planning", "problem_solving"
    required_roles: List[ParticipantRole]
    workflow_steps: List[Dict[str, Any]]
    consensus_items: List[Dict[str, Any]]
    estimated_duration: int  # minutes
    success_criteria: List[str]
    best_practices: List[str]
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    usage_count: int = 0
    success_rate: float = 0.0