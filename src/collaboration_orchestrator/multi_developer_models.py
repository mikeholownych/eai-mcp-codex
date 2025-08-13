"""Multi-Developer Coordination data models."""

from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class DeveloperSpecialization(str, Enum):
    """Developer specialization types."""

    FRONTEND = "frontend"
    BACKEND = "backend"
    FULLSTACK = "fullstack"
    DATABASE = "database"
    DEVOPS = "devops"
    SECURITY = "security"
    MOBILE = "mobile"
    DATA_SCIENCE = "data_science"
    ML_AI = "ml_ai"
    ARCHITECTURE = "architecture"
    QA = "qa"
    UI_UX = "ui_ux"


class ExperienceLevel(str, Enum):
    """Developer experience levels."""

    JUNIOR = "junior"
    INTERMEDIATE = "intermediate"
    SENIOR = "senior"
    LEAD = "lead"
    ARCHITECT = "architect"


class TaskType(str, Enum):
    """Types of development tasks."""

    FEATURE_DEVELOPMENT = "feature_development"
    BUG_FIX = "bug_fix"
    REFACTORING = "refactoring"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    CODE_REVIEW = "code_review"
    ARCHITECTURE_DESIGN = "architecture_design"
    DEPLOYMENT = "deployment"
    OPTIMIZATION = "optimization"
    INTEGRATION = "integration"


class TaskStatus(str, Enum):
    """Task execution status."""

    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    UNDER_REVIEW = "under_review"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ConflictType(str, Enum):
    """Types of conflicts in multi-developer scenarios."""

    MERGE_CONFLICT = "merge_conflict"
    DESIGN_CONFLICT = "design_conflict"
    RESOURCE_CONFLICT = "resource_conflict"
    TIMELINE_CONFLICT = "timeline_conflict"
    APPROACH_CONFLICT = "approach_conflict"
    PRIORITY_CONFLICT = "priority_conflict"
    DEPENDENCY_CONFLICT = "dependency_conflict"
    QUALITY_CONFLICT = "quality_conflict"


class ConflictSeverity(str, Enum):
    """Severity levels for conflicts."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ResolutionStrategy(str, Enum):
    """Conflict resolution strategies."""

    CONSENSUS = "consensus"
    LEAD_DECISION = "lead_decision"
    VOTE = "vote"
    EXPERTISE_BASED = "expertise_based"
    AUTOMATED = "automated"
    ESCALATION = "escalation"


class TeamRole(str, Enum):
    """Roles within a development team."""

    TEAM_LEAD = "team_lead"
    SENIOR_DEVELOPER = "senior_developer"
    DEVELOPER = "developer"
    REVIEWER = "reviewer"
    SPECIALIST = "specialist"
    OBSERVER = "observer"


class DeveloperProfile(BaseModel):
    """Comprehensive developer agent profile."""

    agent_id: str
    agent_type: str = "developer"
    specializations: List[DeveloperSpecialization] = Field(default_factory=list)
    programming_languages: List[str] = Field(default_factory=list)
    frameworks: List[str] = Field(default_factory=list)
    experience_level: ExperienceLevel = ExperienceLevel.INTERMEDIATE
    preferred_tasks: List[TaskType] = Field(default_factory=list)
    availability_schedule: Dict[str, Any] = Field(default_factory=dict)
    current_workload: int = 0
    max_concurrent_tasks: int = 3
    performance_metrics: "PerformanceMetrics" = Field(
        default_factory=lambda: PerformanceMetrics()
    )
    collaboration_preferences: Dict[str, Any] = Field(default_factory=dict)
    trust_scores: Dict[str, float] = Field(
        default_factory=dict
    )  # agent_id -> trust_score
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    def get_capability_score(
        self, task_type: TaskType, required_skills: List[str]
    ) -> float:
        """Calculate capability score for a specific task."""
        base_score = 0.45

        # Experience level bonus
        experience_bonus = {
            ExperienceLevel.JUNIOR: 0.0,
            ExperienceLevel.INTERMEDIATE: 0.1,
            ExperienceLevel.SENIOR: 0.15,
            ExperienceLevel.LEAD: 0.2,
            ExperienceLevel.ARCHITECT: 0.25,
        }
        base_score += experience_bonus[self.experience_level]

        # Task preference bonus
        if task_type in self.preferred_tasks:
            base_score += 0.2

        # Skill match bonus (ensure non-matching stays below 0.7 overall)
        skill_matches = len(
            set(required_skills) & set(self.programming_languages + self.frameworks)
        )
        skill_total = len(required_skills) if required_skills else 1
        # Use 0.1 weight so experience/preference don't push non-matches too high
        base_score += (skill_matches / skill_total) * 0.1

        # Note: Performance history is factored by assignment engine,
        # not here. Keep this a pure capability score.

        return min(1.0, base_score)

    def is_available(self, estimated_hours: int = 1) -> bool:
        """Check if developer is available for new tasks."""
        return self.current_workload + estimated_hours <= self.max_concurrent_tasks * 8


class PerformanceMetrics(BaseModel):
    """Performance metrics for a developer agent."""

    tasks_completed: int = 0
    tasks_failed: int = 0
    average_completion_time: Optional[float] = None  # hours
    code_quality_score: float = 0.8
    collaboration_score: float = 0.8
    communication_score: float = 0.8
    reliability_score: float = 0.8
    innovation_score: float = 0.7
    overall_score: float = 0.8
    peer_ratings: List[float] = Field(default_factory=list)
    improvement_areas: List[str] = Field(default_factory=list)
    strengths: List[str] = Field(default_factory=list)
    last_updated: datetime = Field(default_factory=datetime.utcnow)

    @property
    def completion_rate(self) -> float:
        """Calculate task completion rate."""
        total_tasks = self.tasks_completed + self.tasks_failed
        return self.tasks_completed / total_tasks if total_tasks > 0 else 0.0


class TaskAssignment(BaseModel):
    """Individual task assignment within a coordination plan."""

    assignment_id: UUID = Field(default_factory=uuid4)
    plan_id: UUID
    task_name: str
    task_description: str
    task_type: TaskType
    assigned_agent: str
    reviewer_agents: List[str] = Field(default_factory=list)
    dependencies: List[UUID] = Field(default_factory=list)  # other assignment IDs
    requirements: Dict[str, Any] = Field(default_factory=dict)
    deliverables: List[str] = Field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    priority: str = "medium"
    complexity_score: float = 0.5  # 0.0 to 1.0
    estimated_effort: int = 4  # hours
    actual_effort: Optional[int] = None  # hours
    progress_percentage: int = 0
    quality_score: Optional[float] = None
    feedback: List[Dict[str, Any]] = Field(default_factory=list)
    blockers: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    deadline: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    @property
    def is_blocked(self) -> bool:
        """Check if task is currently blocked."""
        return bool(self.blockers) or self.status == TaskStatus.BLOCKED

    @property
    def is_overdue(self) -> bool:
        """Check if task is overdue."""
        return (
            self.deadline
            and datetime.utcnow() > self.deadline
            and self.status != TaskStatus.COMPLETED
        )


class TeamCoordinationPlan(BaseModel):
    """Comprehensive plan for coordinating a development team."""

    plan_id: UUID = Field(default_factory=uuid4)
    session_id: UUID
    project_name: str
    project_description: str
    team_lead: str
    team_members: List[str] = Field(default_factory=list)
    task_assignments: Dict[str, TaskAssignment] = Field(
        default_factory=dict
    )  # assignment_id -> assignment
    dependencies: Dict[str, List[str]] = Field(
        default_factory=dict
    )  # task_id -> [dependency_task_ids]
    communication_plan: "CommunicationPlan" = Field(
        default_factory=lambda: CommunicationPlan()
    )
    conflict_resolution_strategy: ResolutionStrategy = ResolutionStrategy.CONSENSUS
    status: str = "draft"
    priority: str = "medium"
    estimated_duration: Optional[int] = None  # hours
    actual_duration: Optional[int] = None  # hours
    success_metrics: Dict[str, float] = Field(default_factory=dict)
    risk_factors: List[str] = Field(default_factory=list)
    milestone_schedule: List[Dict[str, Any]] = Field(default_factory=list)
    resource_requirements: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    deadline: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

    def get_critical_path(self) -> List[str]:
        """Calculate the critical path through the project tasks."""
        # Simplified critical path calculation
        # In a real implementation, this would use proper CPM algorithm
        critical_tasks = []
        for assignment_id, assignment in self.task_assignments.items():
            if assignment.priority == "high" or assignment.complexity_score > 0.7:
                critical_tasks.append(assignment_id)
        return critical_tasks

    def get_team_workload_distribution(self) -> Dict[str, int]:
        """Get current workload distribution across team members."""
        workload = {member: 0 for member in self.team_members}
        for assignment in self.task_assignments.values():
            if assignment.assigned_agent in workload:
                workload[assignment.assigned_agent] += assignment.estimated_effort or 4
        return workload

    @property
    def completion_percentage(self) -> float:
        """Calculate overall plan completion percentage."""
        if not self.task_assignments:
            return 0.0
        total_progress = sum(
            assignment.progress_percentage
            for assignment in self.task_assignments.values()
        )
        return total_progress / len(self.task_assignments)


class CommunicationPlan(BaseModel):
    """Communication plan for team coordination."""

    daily_standup: bool = True
    standup_time: str = "09:00"
    weekly_reviews: bool = True
    milestone_meetings: bool = True
    conflict_escalation_path: List[str] = Field(default_factory=list)
    communication_channels: Dict[str, str] = Field(default_factory=dict)
    notification_preferences: Dict[str, List[str]] = Field(default_factory=dict)
    response_time_expectations: Dict[str, int] = Field(default_factory=dict)  # minutes


class ConflictResolutionLog(BaseModel):
    """Log entry for conflict resolution."""

    conflict_id: UUID = Field(default_factory=uuid4)
    session_id: UUID
    plan_id: Optional[UUID] = None
    conflict_type: ConflictType
    conflict_description: str
    involved_agents: List[str]
    conflict_severity: ConflictSeverity = ConflictSeverity.MEDIUM
    conflict_context: Dict[str, Any] = Field(default_factory=dict)
    resolution_strategy: Optional[ResolutionStrategy] = None
    resolution_steps: List[str] = Field(default_factory=list)
    resolution_outcome: Optional[str] = None
    resolved_by: Optional[str] = None
    automation_used: bool = False
    human_intervention: bool = False
    learning_points: List[str] = Field(default_factory=list)
    prevention_measures: List[str] = Field(default_factory=list)
    status: str = "open"
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = None

    @property
    def resolution_time(self) -> Optional[timedelta]:
        """Calculate time taken to resolve conflict."""
        if self.resolved_at:
            return self.resolved_at - self.created_at
        return None


class TeamPerformanceMetrics(BaseModel):
    """Performance metrics for a development team."""

    metric_id: UUID = Field(default_factory=uuid4)
    session_id: UUID
    plan_id: Optional[UUID] = None
    team_members: List[str]
    metric_type: str  # "velocity", "quality", "collaboration", "efficiency"
    metric_value: float
    metric_details: Dict[str, Any] = Field(default_factory=dict)
    measurement_period: Dict[str, datetime] = Field(default_factory=dict)
    benchmark_comparison: Optional[float] = None
    trend_data: List[Tuple[datetime, float]] = Field(default_factory=list)
    contributing_factors: List[str] = Field(default_factory=list)
    improvement_suggestions: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    recorded_at: datetime = Field(default_factory=datetime.utcnow)


class AgentCollaborationHistory(BaseModel):
    """Historical collaboration data between two agents."""

    collaboration_id: UUID = Field(default_factory=uuid4)
    session_id: UUID
    agent_1: str
    agent_2: str
    collaboration_type: str
    interaction_count: int = 0
    successful_collaborations: int = 0
    conflict_count: int = 0
    average_response_time: Optional[float] = None  # minutes
    quality_ratings: List[float] = Field(default_factory=list)
    communication_effectiveness: Optional[float] = None
    task_completion_rate: Optional[float] = None
    mutual_trust_score: Optional[float] = None
    collaboration_notes: Optional[str] = None
    improvement_areas: List[str] = Field(default_factory=list)
    strengths: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    first_collaboration: datetime = Field(default_factory=datetime.utcnow)
    last_collaboration: datetime = Field(default_factory=datetime.utcnow)

    def update_trust_score(
        self, success: bool, quality_rating: Optional[float] = None
    ) -> None:
        """Update trust score based on collaboration outcome."""
        self.interaction_count += 1
        if success:
            self.successful_collaborations += 1
        if quality_rating:
            self.quality_ratings.append(quality_rating)

        # Calculate mutual trust score
        success_rate = self.successful_collaborations / self.interaction_count
        avg_quality = (
            sum(self.quality_ratings) / len(self.quality_ratings)
            if self.quality_ratings
            else 0.5
        )

        # Weight recent interactions more heavily
        recency_factor = min(1.0, self.interaction_count / 10)
        self.mutual_trust_score = (
            success_rate * 0.6 + avg_quality * 0.4
        ) * recency_factor

        self.last_collaboration = datetime.utcnow()


class TaskOptimizationSuggestion(BaseModel):
    """Suggestion for optimizing task assignments."""

    suggestion_id: UUID = Field(default_factory=uuid4)
    plan_id: UUID
    suggestion_type: str  # "reassignment", "parallelization", "dependency_optimization"
    current_assignment: str  # assignment_id
    suggested_assignment: Optional[str] = None  # agent_id
    expected_improvement: Dict[str, float] = Field(
        default_factory=dict
    )  # metric -> improvement
    rationale: str
    confidence_score: float = 0.7
    implementation_complexity: str = "low"  # low, medium, high
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class DeveloperWorkload(BaseModel):
    """Current workload for a developer agent."""

    agent_id: str
    current_tasks: List[UUID] = Field(default_factory=list)  # assignment_ids
    total_estimated_hours: int = 0
    total_actual_hours: int = 0
    utilization_percentage: float = 0.0
    upcoming_deadlines: List[Tuple[UUID, datetime]] = Field(default_factory=list)
    availability_forecast: Dict[str, float] = Field(
        default_factory=dict
    )  # date -> availability_percentage
    stress_indicators: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    last_updated: datetime = Field(default_factory=datetime.utcnow)
