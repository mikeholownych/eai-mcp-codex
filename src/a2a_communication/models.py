"""A2A Communication data models."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class MessageType(str, Enum):
    """Types of A2A messages."""
    REQUEST = "request"
    RESPONSE = "response"
    COLLABORATION = "collaboration"
    CONSENSUS = "consensus"
    ESCALATION = "escalation"
    NOTIFICATION = "notification"


class MessagePriority(str, Enum):
    """Message priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class AgentStatus(str, Enum):
    """Agent availability status."""
    AVAILABLE = "available"
    BUSY = "busy"
    OFFLINE = "offline"
    MAINTENANCE = "maintenance"


class A2AMessage(BaseModel):
    """Core A2A message structure."""
    id: UUID = Field(default_factory=uuid4)
    conversation_id: Optional[UUID] = None
    sender_agent_id: str
    recipient_agent_id: Optional[str] = None  # None for broadcast
    message_type: MessageType
    priority: MessagePriority = MessagePriority.MEDIUM
    payload: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    requires_response: bool = False
    response_timeout: Optional[int] = None  # seconds


class AgentRegistration(BaseModel):
    """Agent registration information."""
    agent_id: str
    agent_type: str
    capabilities: List[str]
    status: AgentStatus = AgentStatus.AVAILABLE
    endpoint: str
    last_heartbeat: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CollaborationRequest(BaseModel):
    """Request for agent collaboration."""
    task_id: UUID = Field(default_factory=uuid4)
    task_description: str
    required_capabilities: List[str]
    participating_agents: List[str] = Field(default_factory=list)
    max_agents: int = 5
    deadline: Optional[datetime] = None
    context: Dict[str, Any] = Field(default_factory=dict)


class ConsensusItem(BaseModel):
    """Item requiring consensus among agents."""
    item_id: UUID = Field(default_factory=uuid4)
    conversation_id: UUID
    item_type: str  # "decision", "recommendation", "approval"
    description: str
    options: List[str]
    votes: Dict[str, str] = Field(default_factory=dict)  # agent_id -> option
    threshold: float = 0.75  # consensus threshold
    deadline: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AgentCapabilities(BaseModel):
    """Agent capability definition."""
    planning: bool = False
    architecture: bool = False
    development: bool = False
    security: bool = False
    qa: bool = False
    domain_expertise: List[str] = Field(default_factory=list)
    programming_languages: List[str] = Field(default_factory=list)
    frameworks: List[str] = Field(default_factory=list)


class TrustScore(BaseModel):
    """Trust score between agents."""
    evaluating_agent: str
    evaluated_agent: str
    score: float = Field(ge=0.0, le=1.0)
    interactions: int = 0
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    feedback_history: List[Dict[str, Any]] = Field(default_factory=list)