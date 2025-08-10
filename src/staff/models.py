"""Data models for the Staff Management service."""

from typing import Any, Dict, List, Optional
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, EmailStr


class UserRole(str, Enum):
    """User role enumeration."""

    CUSTOMER = "customer"
    ADMIN = "admin"
    MANAGER = "manager"
    SUPPORT = "support"
    CONTENT = "content"


class UserStatus(str, Enum):
    """User status enumeration."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


class TicketStatus(str, Enum):
    """Support ticket status enumeration."""

    OPEN = "open"
    IN_PROGRESS = "in-progress"
    WAITING_CUSTOMER = "waiting-customer"
    RESOLVED = "resolved"
    CLOSED = "closed"


class TicketPriority(str, Enum):
    """Support ticket priority enumeration."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


# User Management Models
class UserBase(BaseModel):
    """Base user model."""

    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    role: UserRole
    status: UserStatus = UserStatus.ACTIVE


class UserCreate(UserBase):
    """User creation model."""

    password: str = Field(..., min_length=8)


class UserUpdate(BaseModel):
    """User update model."""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    role: Optional[UserRole] = None
    status: Optional[UserStatus] = None


class User(UserBase):
    """Full user model with database fields."""

    id: str
    plan: str = "Standard"
    last_active: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    total_spent: float = 0.0
    api_calls: int = 0

    # Pydantic v2 model config
    model_config = {
        "from_attributes": True,
    }


class UserListResponse(BaseModel):
    """Response model for user list endpoint."""

    users: List[User]
    total: int
    page: int
    per_page: int


# Support Ticket Models
class TicketCustomer(BaseModel):
    """Customer information in ticket."""

    name: str
    email: EmailStr
    plan: str


class TicketBase(BaseModel):
    """Base ticket model."""

    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1)
    status: TicketStatus = TicketStatus.OPEN
    priority: TicketPriority = TicketPriority.MEDIUM
    category: str = Field(..., min_length=1, max_length=50)


class TicketCreate(TicketBase):
    """Ticket creation model."""

    customer_id: str


class TicketUpdate(BaseModel):
    """Ticket update model."""

    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, min_length=1)
    status: Optional[TicketStatus] = None
    priority: Optional[TicketPriority] = None
    category: Optional[str] = Field(None, min_length=1, max_length=50)
    assigned_to: Optional[str] = None


class Ticket(TicketBase):
    """Full ticket model with database fields."""

    id: str
    customer: TicketCustomer
    assigned_to: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    response_time: Optional[float] = None  # in hours
    message_count: int = 1

    model_config = {
        "from_attributes": True,
    }


class TicketListResponse(BaseModel):
    """Response model for ticket list endpoint."""

    tickets: List[Ticket]
    total: int
    page: int
    per_page: int


# System Statistics Models
class SystemStats(BaseModel):
    """System statistics model."""

    total_users: int
    active_users: int
    total_subscriptions: int
    active_subscriptions: int
    open_tickets: int
    closed_tickets: int
    system_uptime: str
    avg_response_time: float


class SystemHealth(BaseModel):
    """System health metrics."""

    api_performance: Dict[str, Any]
    database_status: Dict[str, Any]
    memory_usage: Dict[str, Any]
    service_status: Dict[str, str]


# Dashboard Models
class DashboardStats(BaseModel):
    """Dashboard statistics model."""

    system_stats: SystemStats
    recent_tickets: List[Ticket]
    system_alerts: List[Dict[str, Any]]
    quick_actions: List[Dict[str, Any]]


# Request/Response Models
class StaffResponse(BaseModel):
    """Standard staff API response."""

    success: bool = True
    message: str = "Operation completed successfully"
    data: Optional[Any] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ErrorResponse(BaseModel):
    """Error response model."""

    success: bool = False
    message: str
    error_code: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
