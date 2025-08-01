"""Collaboration Orchestrator API routes."""

from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, Depends, Request
from src.common.logging import get_logger

from .models import (
    CollaborationSession,
    CollaborationInvitation,
    ConsensusDecision,
    DecisionType,
    VoteChoice,
    ParticipantRole,
    EscalationRequest,
    CollaborationMetrics,
    WorkflowStep,
)
from .orchestrator import CollaborationOrchestrator


router = APIRouter()
logger = get_logger("collaboration_orchestrator")


async def get_orchestrator(request: Request) -> CollaborationOrchestrator:
    return request.app.state.orchestrator


@router.post("/sessions/create")
async def create_collaboration_session(
    title: str,
    description: str,
    lead_agent: str,
    orchestrator: CollaborationOrchestrator = Depends(get_orchestrator),
    deadline: Optional[datetime] = None,
    context: Optional[Dict] = None,
) -> CollaborationSession:
    """Create a new collaboration session."""
    try:
        session = await orchestrator.create_collaboration_session(
            title=title,
            description=description,
            lead_agent=lead_agent,
            deadline=deadline,
            context=context or {},
        )
        return session
    except Exception as e:
        logger.error(f"Failed to create collaboration session: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to create collaboration session"
        )


@router.post("/sessions/{session_id}/invite")
async def invite_agent_to_collaboration(
    session_id: UUID,
    agent_id: str,
    inviting_agent: str,
    orchestrator: CollaborationOrchestrator = Depends(get_orchestrator),
    role: ParticipantRole = ParticipantRole.CONTRIBUTOR,
    capabilities_required: Optional[List[str]] = None,
    expected_contribution: str = "",
) -> CollaborationInvitation:
    """Invite an agent to participate in a collaboration."""
    try:
        invitation = await orchestrator.invite_agent_to_collaboration(
            session_id=session_id,
            agent_id=agent_id,
            inviting_agent=inviting_agent,
            role=role,
            capabilities_required=capabilities_required or [],
            expected_contribution=expected_contribution,
        )
        return invitation
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to invite agent: {e}")
        raise HTTPException(status_code=500, detail="Failed to invite agent")


@router.post("/invitations/{invitation_id}/respond")
async def respond_to_invitation(
    invitation_id: UUID,
    agent_id: str,
    accepted: bool,
    orchestrator: CollaborationOrchestrator = Depends(get_orchestrator),
    message: Optional[str] = None,
    conditions: Optional[List[str]] = None,
) -> dict:
    """Respond to a collaboration invitation."""
    try:
        success = await orchestrator.respond_to_invitation(
            invitation_id=invitation_id,
            agent_id=agent_id,
            accepted=accepted,
            message=message,
            conditions=conditions or [],
        )

        if not success:
            raise HTTPException(status_code=500, detail="Failed to process response")

        return {
            "status": "response_recorded",
            "invitation_id": str(invitation_id),
            "accepted": accepted,
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to respond to invitation: {e}")
        raise HTTPException(status_code=500, detail="Failed to process response")


@router.post("/sessions/{session_id}/start")
async def start_collaboration(
    session_id: UUID,
    orchestrator: CollaborationOrchestrator = Depends(get_orchestrator),
) -> dict:
    """Start an active collaboration session."""
    success = await orchestrator.start_collaboration(session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")

    return {"status": "started", "session_id": str(session_id)}


@router.get("/sessions/{session_id}")
async def get_collaboration_session(
    session_id: UUID,
    orchestrator: CollaborationOrchestrator = Depends(get_orchestrator),
) -> CollaborationSession:
    """Get details of a collaboration session."""
    session = orchestrator.active_sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return session


@router.get("/sessions")
async def list_collaboration_sessions(
    orchestrator: CollaborationOrchestrator = Depends(get_orchestrator),
    status: Optional[str] = None,
    lead_agent: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
) -> List[CollaborationSession]:
    """List collaboration sessions with optional filtering."""
    sessions = list(orchestrator.active_sessions.values())

    if status:
        sessions = [s for s in sessions if s.status.value == status]

    if lead_agent:
        sessions = [s for s in sessions if s.lead_agent == lead_agent]

    # Sort by creation time (most recent first)
    sessions.sort(key=lambda s: s.created_at, reverse=True)

    return sessions[:limit]


@router.post("/decisions/create")
async def create_consensus_decision(
    session_id: UUID,
    decision_type: DecisionType,
    title: str,
    description: str,
    options: List[str],
    created_by: str,
    orchestrator: CollaborationOrchestrator = Depends(get_orchestrator),
    required_consensus: float = 0.75,
    voting_deadline: Optional[datetime] = None,
) -> ConsensusDecision:
    """Create a decision requiring consensus."""
    try:
        decision = await orchestrator.create_consensus_decision(
            session_id=session_id,
            decision_type=decision_type,
            title=title,
            description=description,
            options=options,
            created_by=created_by,
            required_consensus=required_consensus,
            voting_deadline=voting_deadline,
        )
        return decision
    except Exception as e:
        logger.error(f"Failed to create consensus decision: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to create consensus decision"
        )


@router.post("/decisions/{decision_id}/vote")
async def submit_vote(
    decision_id: UUID,
    agent_id: str,
    vote: VoteChoice,
    orchestrator: CollaborationOrchestrator = Depends(get_orchestrator),
    comment: Optional[str] = None,
) -> dict:
    """Submit a vote for a consensus decision."""
    success = await orchestrator.submit_vote(
        decision_id=decision_id, agent_id=agent_id, vote=vote, comment=comment
    )

    if not success:
        raise HTTPException(status_code=400, detail="Invalid vote or decision")

    return {
        "status": "vote_recorded",
        "decision_id": str(decision_id),
        "vote": vote.value,
    }


@router.get("/decisions/{decision_id}")
async def get_consensus_decision(
    decision_id: UUID,
    orchestrator: CollaborationOrchestrator = Depends(get_orchestrator),
) -> ConsensusDecision:
    """Get details of a consensus decision."""
    decision = orchestrator.consensus_decisions.get(decision_id)
    if not decision:
        raise HTTPException(status_code=404, detail="Decision not found")

    return decision


@router.get("/sessions/{session_id}/decisions")
async def get_session_decisions(
    session_id: UUID,
    orchestrator: CollaborationOrchestrator = Depends(get_orchestrator),
) -> List[ConsensusDecision]:
    """Get all consensus decisions for a session."""
    decisions = [
        d
        for d in orchestrator.consensus_decisions.values()
        if d.session_id == session_id
    ]

    # Sort by creation time
    decisions.sort(key=lambda d: d.created_at)

    return decisions


@router.post("/sessions/{session_id}/escalate")
async def escalate_issue(
    session_id: UUID,
    issue_type: str,
    description: str,
    escalated_by: str,
    orchestrator: CollaborationOrchestrator = Depends(get_orchestrator),
    affected_participants: Optional[List[str]] = None,
    priority: str = "medium",
) -> EscalationRequest:
    """Escalate an issue that cannot be resolved through normal collaboration."""
    try:
        escalation = await orchestrator.escalate_issue(
            session_id=session_id,
            issue_type=issue_type,
            description=description,
            escalated_by=escalated_by,
            affected_participants=affected_participants or [],
            priority=priority,
        )
        return escalation
    except Exception as e:
        logger.error(f"Failed to escalate issue: {e}")
        raise HTTPException(status_code=500, detail="Failed to escalate issue")


@router.post("/sessions/{session_id}/complete")
async def complete_collaboration(
    session_id: UUID,
    orchestrator: CollaborationOrchestrator = Depends(get_orchestrator),
    outputs: Optional[Dict] = None,
) -> dict:
    """Complete a collaboration session."""
    success = await orchestrator.complete_collaboration(
        session_id=session_id, outputs=outputs or {}
    )

    if not success:
        raise HTTPException(status_code=404, detail="Session not found")

    return {"status": "completed", "session_id": str(session_id)}


@router.get("/sessions/{session_id}/metrics")
async def get_session_metrics(
    session_id: UUID,
    orchestrator: CollaborationOrchestrator = Depends(get_orchestrator),
) -> CollaborationMetrics:
    """Get metrics for a collaboration session."""
    session = orchestrator.active_sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # For completed sessions, get stored metrics
    metrics_key = f"collaboration:metrics:{session_id}"
    metrics_data = orchestrator.redis.get(metrics_key)

    if metrics_data:
        import json

        return CollaborationMetrics(**json.loads(metrics_data))

    # For active sessions, calculate current metrics
    metrics = await orchestrator._calculate_session_metrics(session)
    return metrics


@router.get("/system/stats")
async def get_system_stats(
    orchestrator: CollaborationOrchestrator = Depends(get_orchestrator),
) -> dict:
    """Get collaboration system statistics."""
    try:
        total_sessions = len(orchestrator.active_sessions)
        active_sessions = len(
            [
                s
                for s in orchestrator.active_sessions.values()
                if s.status.value == "active"
            ]
        )
        completed_sessions = len(
            [
                s
                for s in orchestrator.active_sessions.values()
                if s.status.value == "completed"
            ]
        )

        total_decisions = len(orchestrator.consensus_decisions)
        resolved_decisions = len(
            [d for d in orchestrator.consensus_decisions.values() if d.resolved]
        )

        # Calculate success rate
        success_rate = resolved_decisions / max(1, total_decisions)

        return {
            "total_sessions": total_sessions,
            "active_sessions": active_sessions,
            "completed_sessions": completed_sessions,
            "total_decisions": total_decisions,
            "resolved_decisions": resolved_decisions,
            "consensus_success_rate": success_rate,
            "system_status": "operational",
            "timestamp": datetime.utcnow(),
        }
    except Exception as e:
        logger.error(f"Failed to get system stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get system stats")


@router.get("/templates")
async def list_collaboration_templates() -> List[dict]:
    """List available collaboration templates."""
    # Return hardcoded templates for now
    templates = [
        {
            "name": "Code Review Session",
            "description": "Multi-agent code review with security and performance analysis",
            "category": "code_review",
            "required_roles": ["developer", "security", "qa"],
            "estimated_duration": 60,
        },
        {
            "name": "Architecture Design",
            "description": "Collaborative system architecture design and consensus",
            "category": "architecture_design",
            "required_roles": ["architect", "developer", "security"],
            "estimated_duration": 120,
        },
        {
            "name": "Sprint Planning",
            "description": "Collaborative sprint planning with task breakdown",
            "category": "planning",
            "required_roles": ["planner", "developer", "qa"],
            "estimated_duration": 90,
        },
        {
            "name": "Problem Solving",
            "description": "Multi-agent problem analysis and solution design",
            "category": "problem_solving",
            "required_roles": ["domain_expert", "architect", "developer"],
            "estimated_duration": 45,
        },
    ]

    return templates


@router.post("/sessions/{session_id}/workflow/add-step")
async def add_workflow_step(
    session_id: UUID,
    title: str,
    description: str,
    step_number: int,
    orchestrator: CollaborationOrchestrator = Depends(get_orchestrator),
    assigned_agent: Optional[str] = None,
    required_capabilities: Optional[List[str]] = None,
    dependencies: Optional[List[UUID]] = None,
) -> WorkflowStep:
    """Add a workflow step to a collaboration session."""
    session = orchestrator.active_sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    step = WorkflowStep(
        session_id=session_id,
        step_number=step_number,
        title=title,
        description=description,
        assigned_agent=assigned_agent,
        required_capabilities=required_capabilities or [],
        dependencies=dependencies or [],
    )

    # Store workflow step
    step_key = f"collaboration:step:{step.step_id}"
    orchestrator.redis.setex(step_key, 86400, step.model_dump_json())

    return step


@router.get("/sessions/{session_id}/workflow")
async def get_workflow_steps(
    session_id: UUID,
    orchestrator: CollaborationOrchestrator = Depends(get_orchestrator),
) -> List[WorkflowStep]:
    """Get workflow steps for a collaboration session."""
    # Search for workflow steps in Redis
    pattern = "collaboration:step:*"
    steps = []

    for key in orchestrator.redis.scan_iter(match=pattern):
        step_data = orchestrator.redis.get(key)
        if step_data:
            import json

            step = WorkflowStep(**json.loads(step_data))
            if step.session_id == session_id:
                steps.append(step)

    # Sort by step number
    steps.sort(key=lambda s: s.step_number)

    return steps
