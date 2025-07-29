"""Data models for Verification and Feedback processing."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class VerificationStatus(str, Enum):
    """Verification status enumeration."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    PASSED = "passed"
    FAILED = "failed"
    REQUIRES_MANUAL_REVIEW = "requires_manual_review"
    CANCELLED = "cancelled"


class FeedbackType(str, Enum):
    """Feedback type enumeration."""

    USER_FEEDBACK = "user_feedback"
    SYSTEM_FEEDBACK = "system_feedback"
    AUTOMATED_TEST = "automated_test"
    PERFORMANCE_METRIC = "performance_metric"
    ERROR_REPORT = "error_report"
    QUALITY_ASSESSMENT = "quality_assessment"


class FeedbackSeverity(str, Enum):
    """Feedback severity enumeration."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class VerificationRule(BaseModel):
    """Rule for verification checks."""

    id: str
    name: str
    description: str = ""
    rule_type: str  # syntax, semantic, performance, security, etc.
    pattern: Optional[str] = None  # regex pattern for pattern-based rules
    threshold: Optional[float] = None  # numeric threshold for metric-based rules
    parameters: Dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True
    severity: FeedbackSeverity = FeedbackSeverity.MEDIUM
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class VerificationResult(BaseModel):
    """Result of a verification check."""

    rule_id: str
    status: VerificationStatus
    passed: bool
    score: Optional[float] = None  # Confidence or quality score
    message: str = ""
    details: Dict[str, Any] = Field(default_factory=dict)
    suggestions: List[str] = Field(default_factory=list)
    evidence: List[str] = Field(default_factory=list)  # Supporting evidence
    execution_time_ms: Optional[float] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class Verification(BaseModel):
    """Complete verification session."""

    id: str
    name: str
    description: str = ""
    target_type: str  # code, plan, workflow, etc.
    target_id: str  # ID of the target being verified
    target_content: Optional[str] = None  # Content being verified
    status: VerificationStatus = VerificationStatus.PENDING
    rules_applied: List[str] = Field(default_factory=list)  # Rule IDs
    results: List[VerificationResult] = Field(default_factory=list)
    overall_score: Optional[float] = None
    passed_checks: int = 0
    failed_checks: int = 0
    total_checks: int = 0
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    created_by: str = "system"
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Feedback(BaseModel):
    """Feedback record."""

    id: str
    verification_id: Optional[str] = None  # Associated verification if any
    feedback_type: FeedbackType
    severity: FeedbackSeverity = FeedbackSeverity.MEDIUM
    title: str
    content: str
    source: str = "system"  # Source of feedback (user, system, test, etc.)
    target_type: Optional[str] = None  # What this feedback is about
    target_id: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    attachments: List[str] = Field(default_factory=list)  # File paths or URLs
    is_resolved: bool = False
    resolution_notes: Optional[str] = None
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class FeedbackSummary(BaseModel):
    """Summary of feedback for a target."""

    target_type: str
    target_id: str
    total_feedback: int = 0
    by_type: Dict[str, int] = Field(default_factory=dict)
    by_severity: Dict[str, int] = Field(default_factory=dict)
    resolved_count: int = 0
    unresolved_count: int = 0
    latest_feedback: Optional[Feedback] = None
    average_resolution_time_hours: Optional[float] = None


class VerificationRequest(BaseModel):
    """Request to perform verification."""

    name: str
    description: str = ""
    target_type: str
    target_id: str
    target_content: Optional[str] = None
    rule_ids: List[str] = Field(default_factory=list)  # Specific rules to apply
    rule_categories: List[str] = Field(default_factory=list)  # Rule categories
    parameters: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class FeedbackRequest(BaseModel):
    """Request to submit feedback."""

    feedback_type: FeedbackType
    severity: FeedbackSeverity = FeedbackSeverity.MEDIUM
    title: str
    content: str
    target_type: Optional[str] = None
    target_id: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class QualityMetrics(BaseModel):
    """Quality metrics for verification."""

    target_type: str
    target_id: str
    overall_score: float  # 0.0 to 1.0
    individual_scores: Dict[str, float] = Field(default_factory=dict)
    trends: Dict[str, List[float]] = Field(default_factory=dict)  # Historical trends
    benchmarks: Dict[str, float] = Field(default_factory=dict)  # Comparison benchmarks
    recommendations: List[str] = Field(default_factory=list)
    last_updated: datetime = Field(default_factory=datetime.utcnow)


class ProcessingResult(BaseModel):
    """Result of processing feedback or verification."""

    success: bool
    message: str = ""
    processed_items: int = 0
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    execution_time_ms: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
