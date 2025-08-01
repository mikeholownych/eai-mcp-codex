"""Multi-Developer Coordination API routes."""

from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, Body
from pydantic import BaseModel

from src.common.logging import get_logger
from .multi_developer_models import (
    DeveloperProfile,
    DeveloperSpecialization,
    ExperienceLevel,
    TaskType,
    TaskStatus,
    TaskAssignment,
    TeamCoordinationPlan,
    ResolutionStrategy,
    ConflictResolutionLog,
    DeveloperWorkload,
)
from .multi_developer_orchestrator import MultiDeveloperOrchestrator
from .developer_profile_manager import DeveloperProfileManager
from .intelligent_conflict_resolver import IntelligentConflictResolver

logger = get_logger("multi_developer_orchestrator")

# Initialize global components
orchestrator = MultiDeveloperOrchestrator()
profile_manager = DeveloperProfileManager()
conflict_resolver = IntelligentConflictResolver(profile_manager)

router = APIRouter(prefix="/multi-dev", tags=["Multi-Developer Coordination"])


# Pydantic models for API requests
class CreateDeveloperProfileRequest(BaseModel):
    agent_id: str
    agent_type: str = "developer"
    specializations: List[DeveloperSpecialization] = []
    programming_languages: List[str] = []
    frameworks: List[str] = []
    experience_level: ExperienceLevel = ExperienceLevel.INTERMEDIATE
    preferred_tasks: List[TaskType] = []
    max_concurrent_tasks: int = 3
    metadata: Dict[str, Any] = {}


class CreateTeamPlanRequest(BaseModel):
    session_id: UUID
    project_name: str
    project_description: str
    team_lead: str
    team_members: List[str]
    tasks: List[Dict[str, Any]]
    deadline: Optional[datetime] = None
    conflict_resolution_strategy: ResolutionStrategy = ResolutionStrategy.CONSENSUS


class TaskProgressUpdateRequest(BaseModel):
    progress_percentage: int
    status: Optional[TaskStatus] = None
    blockers: List[str] = []
    feedback: Dict[str, Any] = {}


class ConflictDetectionRequest(BaseModel):
    conflict_description: str
    involved_agents: List[str]
    context: Dict[str, Any] = {}
    detected_by: Optional[str] = None


# Developer Profile Management Endpoints


@router.post("/profiles", response_model=DeveloperProfile)
async def create_developer_profile(
    request: CreateDeveloperProfileRequest,
) -> DeveloperProfile:
    """Create a new developer profile."""
    try:
        profile = await profile_manager.create_developer_profile(
            agent_id=request.agent_id,
            agent_type=request.agent_type,
            specializations=request.specializations,
            programming_languages=request.programming_languages,
            frameworks=request.frameworks,
            experience_level=request.experience_level,
            preferred_tasks=request.preferred_tasks,
            max_concurrent_tasks=request.max_concurrent_tasks,
            metadata=request.metadata,
        )
        return profile
    except Exception as e:
        logger.error(f"Failed to create developer profile: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to create developer profile"
        )


@router.get("/profiles/{agent_id}", response_model=DeveloperProfile)
async def get_developer_profile(agent_id: str) -> DeveloperProfile:
    """Get developer profile by agent ID."""
    profile = await profile_manager.get_developer_profile(agent_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Developer profile not found")
    return profile


@router.put("/profiles/{agent_id}")
async def update_developer_profile(
    agent_id: str, updates: Dict[str, Any] = Body(...)
) -> dict:
    """Update developer profile."""
    success = await profile_manager.update_developer_profile(agent_id, updates)
    if not success:
        raise HTTPException(status_code=404, detail="Developer profile not found")
    return {"status": "updated", "agent_id": agent_id}


@router.get("/profiles/{agent_id}/workload", response_model=DeveloperWorkload)
async def get_agent_workload(agent_id: str) -> DeveloperWorkload:
    """Get current workload for an agent."""
    workload = await profile_manager.get_agent_workload(agent_id)
    if not workload:
        raise HTTPException(status_code=404, detail="Agent workload not found")
    return workload


@router.get("/profiles/available")
async def get_available_agents(
    specialization: Optional[DeveloperSpecialization] = None,
    min_experience: Optional[ExperienceLevel] = None,
    required_skills: List[str] = Query([]),
) -> List[DeveloperProfile]:
    """Get list of available agents matching criteria."""
    try:
        agents = await profile_manager.get_available_agents(
            specialization=specialization,
            min_experience=min_experience,
            required_skills=required_skills,
        )
        return agents
    except Exception as e:
        logger.error(f"Failed to get available agents: {e}")
        raise HTTPException(status_code=500, detail="Failed to get available agents")


@router.post("/profiles/{agent_id}/performance")
async def update_performance_metrics(
    agent_id: str,
    task_completed: bool = True,
    completion_time: Optional[float] = None,
    quality_score: Optional[float] = None,
    peer_rating: Optional[float] = None,
) -> dict:
    """Update performance metrics for a developer."""
    success = await profile_manager.update_performance_metrics(
        agent_id=agent_id,
        task_completed=task_completed,
        completion_time=completion_time,
        quality_score=quality_score,
        peer_rating=peer_rating,
    )
    if not success:
        raise HTTPException(status_code=404, detail="Developer profile not found")
    return {"status": "updated", "agent_id": agent_id}


@router.get("/profiles/find-for-task")
async def find_best_agents_for_task(
    task_type: TaskType,
    required_skills: List[str] = Query([]),
    max_agents: int = 3,
    exclude_agents: List[str] = Query([]),
) -> List[Dict[str, Any]]:
    """Find best agents for a specific task."""
    try:
        candidates = await profile_manager.find_best_agents_for_task(
            task_type=task_type,
            required_skills=required_skills,
            max_agents=max_agents,
            exclude_agents=exclude_agents,
        )
        return [
            {"agent_id": agent_id, "score": score} for agent_id, score in candidates
        ]
    except Exception as e:
        logger.error(f"Failed to find agents for task: {e}")
        raise HTTPException(status_code=500, detail="Failed to find agents for task")


# Team Coordination Plan Endpoints


@router.post("/plans", response_model=TeamCoordinationPlan)
async def create_team_coordination_plan(
    request: CreateTeamPlanRequest,
) -> TeamCoordinationPlan:
    """Create a comprehensive team coordination plan."""
    try:
        plan = await orchestrator.create_team_coordination_plan(
            session_id=request.session_id,
            project_name=request.project_name,
            project_description=request.project_description,
            team_lead=request.team_lead,
            team_members=request.team_members,
            tasks=request.tasks,
            deadline=request.deadline,
            conflict_resolution_strategy=request.conflict_resolution_strategy,
        )
        return plan
    except Exception as e:
        logger.error(f"Failed to create team coordination plan: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to create team coordination plan"
        )


@router.get("/plans/{plan_id}", response_model=TeamCoordinationPlan)
async def get_coordination_plan(plan_id: UUID) -> TeamCoordinationPlan:
    """Get coordination plan by ID."""
    plan = await orchestrator.get_coordination_plan(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Coordination plan not found")
    return plan


@router.get("/plans/{plan_id}/performance-report")
async def get_team_performance_report(plan_id: UUID) -> Dict[str, Any]:
    """Generate comprehensive team performance report."""
    try:
        report = await orchestrator.generate_team_performance_report(plan_id)
        if not report:
            raise HTTPException(status_code=404, detail="Plan not found")
        return report
    except Exception as e:
        logger.error(f"Failed to generate performance report: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to generate performance report"
        )


@router.post("/plans/{plan_id}/optimize")
async def optimize_task_assignments(plan_id: UUID) -> Dict[str, Any]:
    """Optimize task assignments in a coordination plan."""
    try:
        plan = await orchestrator.get_coordination_plan(plan_id)
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")

        # Get available agents
        available_agents = []
        for agent_id in plan.team_members:
            profile = await profile_manager.get_developer_profile(agent_id)
            if profile:
                available_agents.append(profile)

        # Generate optimization suggestions
        agent_profiles = {agent.agent_id: agent for agent in available_agents}
        suggestions = orchestrator.assignment_engine.suggest_task_optimizations(
            plan, agent_profiles
        )

        return {
            "plan_id": str(plan_id),
            "optimization_suggestions": [s.model_dump() for s in suggestions],
            "generated_at": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"Failed to optimize task assignments: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to optimize task assignments"
        )


# Task Assignment Endpoints


@router.post("/plans/{plan_id}/tasks/{assignment_id}/assign")
async def assign_task_to_agent(
    plan_id: UUID,
    assignment_id: UUID,
    agent_id: str,
    reviewer_agents: List[str] = Query([]),
) -> dict:
    """Assign a specific task to an agent."""
    success = await orchestrator.assign_task_to_agent(
        plan_id=plan_id,
        assignment_id=assignment_id,
        agent_id=agent_id,
        reviewer_agents=reviewer_agents,
    )
    if not success:
        raise HTTPException(status_code=400, detail="Failed to assign task")

    return {
        "status": "assigned",
        "plan_id": str(plan_id),
        "assignment_id": str(assignment_id),
        "agent_id": agent_id,
    }


@router.put("/tasks/{assignment_id}/progress")
async def update_task_progress(
    assignment_id: UUID, agent_id: str, request: TaskProgressUpdateRequest
) -> dict:
    """Update task progress."""
    success = await orchestrator.handle_task_progress_update(
        assignment_id=assignment_id,
        agent_id=agent_id,
        progress_percentage=request.progress_percentage,
        status=request.status,
        blockers=request.blockers,
        feedback=request.feedback,
    )
    if not success:
        raise HTTPException(status_code=400, detail="Failed to update task progress")

    return {
        "status": "updated",
        "assignment_id": str(assignment_id),
        "progress": request.progress_percentage,
    }


@router.get("/tasks/{assignment_id}")
async def get_task_assignment(assignment_id: UUID) -> TaskAssignment:
    """Get task assignment by ID."""
    assignment = await orchestrator._get_task_assignment(assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Task assignment not found")
    return assignment


# Conflict Resolution Endpoints


@router.post("/plans/{plan_id}/conflicts/detect", response_model=ConflictResolutionLog)
async def detect_conflict(
    plan_id: UUID, request: ConflictDetectionRequest
) -> ConflictResolutionLog:
    """Detect and analyze a conflict."""
    try:
        # Get the plan to find session_id
        plan = await orchestrator.get_coordination_plan(plan_id)
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")

        conflict = await conflict_resolver.detect_conflict(
            session_id=plan.session_id,
            plan_id=plan_id,
            conflict_description=request.conflict_description,
            involved_agents=request.involved_agents,
            context=request.context,
            detected_by=request.detected_by,
        )
        return conflict
    except Exception as e:
        logger.error(f"Failed to detect conflict: {e}")
        raise HTTPException(status_code=500, detail="Failed to detect conflict")


@router.post("/conflicts/{conflict_id}/resolve")
async def resolve_conflict(conflict_id: UUID) -> dict:
    """Attempt to resolve a conflict."""
    try:
        resolved = await conflict_resolver.resolve_conflict(conflict_id)
        return {
            "status": "resolved" if resolved else "resolution_in_progress",
            "conflict_id": str(conflict_id),
        }
    except Exception as e:
        logger.error(f"Failed to resolve conflict: {e}")
        raise HTTPException(status_code=500, detail="Failed to resolve conflict")


@router.get("/conflicts/{conflict_id}", response_model=ConflictResolutionLog)
async def get_conflict(conflict_id: UUID) -> ConflictResolutionLog:
    """Get conflict by ID."""
    conflict = await conflict_resolver.get_conflict(conflict_id)
    if not conflict:
        raise HTTPException(status_code=404, detail="Conflict not found")
    return conflict


@router.get("/sessions/{session_id}/conflicts")
async def get_session_conflicts(session_id: UUID) -> List[ConflictResolutionLog]:
    """Get all conflicts for a session."""
    try:
        conflicts = await conflict_resolver.get_conflicts_for_session(session_id)
        return conflicts
    except Exception as e:
        logger.error(f"Failed to get session conflicts: {e}")
        raise HTTPException(status_code=500, detail="Failed to get session conflicts")


@router.get("/conflicts/statistics")
async def get_conflict_statistics(session_id: Optional[UUID] = None) -> Dict[str, Any]:
    """Get conflict resolution statistics."""
    try:
        stats = await conflict_resolver.get_conflict_statistics(session_id)
        return stats
    except Exception as e:
        logger.error(f"Failed to get conflict statistics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get conflict statistics")


@router.post("/plans/{plan_id}/conflicts/auto-detect")
async def auto_detect_conflicts(plan_id: UUID) -> List[Dict[str, Any]]:
    """Proactively detect and resolve conflicts in a coordination plan."""
    try:
        conflicts = await orchestrator.detect_and_resolve_conflicts(plan_id)
        return conflicts
    except Exception as e:
        logger.error(f"Failed to auto-detect conflicts: {e}")
        raise HTTPException(status_code=500, detail="Failed to auto-detect conflicts")


# Analytics and Reporting Endpoints


@router.get("/analytics/team-compatibility")
async def calculate_team_compatibility(
    agent_ids: List[str] = Query(...),
) -> Dict[str, Any]:
    """Calculate compatibility score for a team of agents."""
    try:
        if len(agent_ids) < 2:
            raise HTTPException(status_code=400, detail="At least 2 agents required")

        compatibility_score = await profile_manager.get_team_compatibility_score(
            agent_ids
        )
        return {
            "team_agents": agent_ids,
            "compatibility_score": compatibility_score,
            "recommendation": (
                "high"
                if compatibility_score > 0.8
                else "medium" if compatibility_score > 0.6 else "low"
            ),
        }
    except Exception as e:
        logger.error(f"Failed to calculate team compatibility: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to calculate team compatibility"
        )


@router.get("/analytics/agent-collaboration/{agent_1}/{agent_2}")
async def get_collaboration_history(
    agent_1: str, agent_2: str, session_id: Optional[UUID] = None
):
    """Get collaboration history between two agents."""
    try:
        history = await profile_manager.get_collaboration_history(
            agent_1, agent_2, session_id
        )
        if not history:
            return {"message": "No collaboration history found"}
        return history
    except Exception as e:
        logger.error(f"Failed to get collaboration history: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to get collaboration history"
        )


@router.get("/analytics/workload-distribution")
async def get_workload_distribution(
    agent_ids: List[str] = Query(...),
) -> Dict[str, Any]:
    """Get workload distribution across multiple agents."""
    try:
        workload_data = {}
        total_workload = 0

        for agent_id in agent_ids:
            workload = await profile_manager.get_agent_workload(agent_id)
            if workload:
                workload_data[agent_id] = {
                    "current_tasks": len(workload.current_tasks),
                    "total_hours": workload.total_estimated_hours,
                    "utilization": workload.utilization_percentage,
                    "stress_indicators": workload.stress_indicators,
                    "recommendations": workload.recommendations,
                }
                total_workload += workload.total_estimated_hours

        # Calculate balance metrics
        if workload_data:
            utilizations = [data["utilization"] for data in workload_data.values()]
            avg_utilization = sum(utilizations) / len(utilizations)
            max_utilization = max(utilizations)
            min_utilization = min(utilizations)
            balance_score = 1.0 - (max_utilization - min_utilization) / 100.0
        else:
            avg_utilization = 0
            balance_score = 1.0

        return {
            "agents": workload_data,
            "total_workload_hours": total_workload,
            "average_utilization": avg_utilization,
            "workload_balance_score": max(0.0, balance_score),
            "recommendations": [
                (
                    "Consider redistributing tasks"
                    if balance_score < 0.7
                    else "Workload is well balanced"
                )
            ],
        }
    except Exception as e:
        logger.error(f"Failed to get workload distribution: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to get workload distribution"
        )


# System Health and Monitoring


@router.get("/system/health")
async def get_system_health() -> Dict[str, Any]:
    """Get multi-developer coordination system health."""
    try:
        # Get basic counts from the orchestrator
        active_plans = len(orchestrator.active_plans)
        active_conflicts = len(conflict_resolver.active_conflicts)

        # Get database connection status
        try:
            conn = await orchestrator._get_db_connection()
            db_status = "healthy"
            if not orchestrator.postgres_pool:
                await conn.close()
            else:
                await orchestrator.postgres_pool.release(conn)
        except Exception:
            db_status = "unhealthy"

        # Get Redis status
        try:
            orchestrator.redis.ping()
            redis_status = "healthy"
        except Exception:
            redis_status = "unhealthy"

        overall_status = (
            "healthy"
            if db_status == "healthy" and redis_status == "healthy"
            else "degraded"
        )

        return {
            "status": overall_status,
            "components": {
                "database": db_status,
                "redis": redis_status,
                "orchestrator": "healthy",
                "conflict_resolver": "healthy",
            },
            "metrics": {
                "active_coordination_plans": active_plans,
                "active_conflicts": active_conflicts,
            },
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"Failed to get system health: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
        }


@router.get("/system/metrics")
async def get_system_metrics() -> Dict[str, Any]:
    """Get comprehensive system metrics."""
    try:
        # This would be expanded with real metrics collection
        return {
            "coordination_plans": {
                "total": len(orchestrator.active_plans),
                "by_status": {},  # Would be populated with real data
            },
            "conflicts": {
                "total_detected": len(conflict_resolver.active_conflicts),
                "resolved_today": 0,  # Would be calculated from database
                "average_resolution_time": 0.0,  # Would be calculated from database
            },
            "agents": {
                "registered": 0,  # Would be counted from database
                "active": 0,  # Would be calculated based on recent activity
                "average_performance": 0.0,  # Would be calculated from performance metrics
            },
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"Failed to get system metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get system metrics")
