"""Core collaboration orchestration logic."""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from uuid import UUID

from src.common.redis_client import get_redis_connection
from src.a2a_communication.models import A2AMessage, MessageType, MessagePriority
from src.a2a_communication.message_broker import A2AMessageBroker

from .models import (
    CollaborationSession,
    CollaborationStatus,
    CollaborationInvitation,
    CollaborationResponse,
    ConsensusDecision,
    DecisionType,
    VoteChoice,
    ParticipantRole,
    EscalationRequest,
    CollaborationMetrics,
)


logger = logging.getLogger(__name__)


class CollaborationOrchestrator:
    """Orchestrates multi-agent collaborations and consensus building."""

    def __init__(self):
        self.redis = get_redis_connection()
        self.message_broker = A2AMessageBroker()
        self.active_sessions: Dict[UUID, CollaborationSession] = {}
        self.consensus_decisions: Dict[UUID, ConsensusDecision] = {}

    async def create_collaboration_session(
        self,
        title: str,
        description: str,
        lead_agent: str,
        deadline: Optional[datetime] = None,
        context: Dict = None,
    ) -> CollaborationSession:
        """Create a new collaboration session."""
        session = CollaborationSession(
            title=title,
            description=description,
            lead_agent=lead_agent,
            deadline=deadline,
            context=context or {},
            participants=[lead_agent],
            participant_roles={lead_agent: ParticipantRole.LEAD},
        )

        self.active_sessions[session.session_id] = session

        # Store in Redis
        session_key = f"collaboration:session:{session.session_id}"
        self.redis.setex(session_key, 86400, session.model_dump_json())  # 24 hours TTL

        logger.info(f"Created collaboration session {session.session_id}: {title}")
        return session

    async def invite_agent_to_collaboration(
        self,
        session_id: UUID,
        agent_id: str,
        inviting_agent: str,
        role: ParticipantRole = ParticipantRole.CONTRIBUTOR,
        capabilities_required: List[str] = None,
        expected_contribution: str = "",
    ) -> CollaborationInvitation:
        """Invite an agent to participate in a collaboration."""
        session = self.active_sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        invitation = CollaborationInvitation(
            session_id=session_id,
            invited_agent=agent_id,
            invited_by=inviting_agent,
            role=role,
            message=f"You're invited to collaborate on: {session.title}",
            capabilities_required=capabilities_required or [],
            expected_contribution=expected_contribution,
            deadline=session.deadline,
        )

        # Send invitation message
        invitation_message = A2AMessage(
            sender_agent_id=inviting_agent,
            recipient_agent_id=agent_id,
            message_type=MessageType.COLLABORATION,
            priority=MessagePriority.HIGH,
            payload={
                "invitation_id": str(invitation.invitation_id),
                "session_id": str(session_id),
                "title": session.title,
                "description": session.description,
                "role": role.value,
                "capabilities_required": capabilities_required or [],
                "expected_contribution": expected_contribution,
                "deadline": (
                    invitation.deadline.isoformat() if invitation.deadline else None
                ),
            },
            requires_response=True,
            response_timeout=1800,  # 30 minutes
        )

        await self.message_broker.send_message(invitation_message)

        # Store invitation
        invitation_key = f"collaboration:invitation:{invitation.invitation_id}"
        self.redis.setex(invitation_key, 3600, invitation.model_dump_json())

        logger.info(
            f"Sent collaboration invitation to {agent_id} for session {session_id}"
        )
        return invitation

    async def respond_to_invitation(
        self,
        invitation_id: UUID,
        agent_id: str,
        accepted: bool,
        message: str = None,
        conditions: List[str] = None,
    ) -> bool:
        """Respond to a collaboration invitation."""
        # Get invitation
        invitation_key = f"collaboration:invitation:{invitation_id}"
        invitation_data = self.redis.get(invitation_key)

        if not invitation_data:
            raise ValueError(f"Invitation {invitation_id} not found")

        invitation = CollaborationInvitation(**json.loads(invitation_data))

        response = CollaborationResponse(
            invitation_id=invitation_id,
            agent_id=agent_id,
            accepted=accepted,
            message=message,
            conditions=conditions or [],
        )

        # Store response
        response_key = f"collaboration:response:{invitation_id}"
        self.redis.setex(response_key, 3600, response.model_dump_json())

        if accepted:
            # Add agent to session
            session = self.active_sessions.get(invitation.session_id)
            if session:
                if agent_id not in session.participants:
                    session.participants.append(agent_id)
                    session.participant_roles[agent_id] = invitation.role

                    # Update session in Redis
                    session_key = f"collaboration:session:{session.session_id}"
                    self.redis.setex(session_key, 86400, session.model_dump_json())

                    # Notify other participants
                    await self._notify_participants(
                        session,
                        f"Agent {agent_id} joined the collaboration as {invitation.role.value}",
                        exclude_agent=agent_id,
                    )

        # Notify inviting agent
        response_message = A2AMessage(
            sender_agent_id=agent_id,
            recipient_agent_id=invitation.invited_by,
            message_type=MessageType.RESPONSE,
            payload={
                "invitation_id": str(invitation_id),
                "accepted": accepted,
                "message": message,
                "conditions": conditions or [],
            },
        )

        await self.message_broker.send_message(response_message)

        logger.info(
            f"Agent {agent_id} {'accepted' if accepted else 'declined'} invitation {invitation_id}"
        )
        return True

    async def start_collaboration(self, session_id: UUID) -> bool:
        """Start an active collaboration session."""
        session = self.active_sessions.get(session_id)
        if not session:
            return False

        session.status = CollaborationStatus.ACTIVE
        session.started_at = datetime.utcnow()

        # Update in Redis
        session_key = f"collaboration:session:{session_id}"
        self.redis.setex(session_key, 86400, session.model_dump_json())

        # Notify all participants
        await self._notify_participants(
            session, f"Collaboration '{session.title}' has started!"
        )

        logger.info(f"Started collaboration session {session_id}")
        return True

    async def create_consensus_decision(
        self,
        session_id: UUID,
        decision_type: DecisionType,
        title: str,
        description: str,
        options: List[str],
        created_by: str,
        required_consensus: float = 0.75,
        voting_deadline: Optional[datetime] = None,
    ) -> ConsensusDecision:
        """Create a decision requiring consensus."""
        decision = ConsensusDecision(
            session_id=session_id,
            decision_type=decision_type,
            title=title,
            description=description,
            options=options,
            required_consensus=required_consensus,
            created_by=created_by,
            voting_deadline=voting_deadline,
        )

        self.consensus_decisions[decision.decision_id] = decision

        # Store in Redis
        decision_key = f"collaboration:decision:{decision.decision_id}"
        self.redis.setex(decision_key, 86400, decision.model_dump_json())

        # Notify session participants
        session = self.active_sessions.get(session_id)
        if session:
            consensus_message = A2AMessage(
                sender_agent_id=created_by,
                message_type=MessageType.CONSENSUS,
                payload={
                    "decision_id": str(decision.decision_id),
                    "decision_type": decision_type.value,
                    "title": title,
                    "description": description,
                    "options": options,
                    "voting_deadline": (
                        voting_deadline.isoformat() if voting_deadline else None
                    ),
                },
                requires_response=True,
                response_timeout=3600,  # 1 hour
            )

            for participant in session.participants:
                if participant != created_by:
                    consensus_message.recipient_agent_id = participant
                    await self.message_broker.send_message(consensus_message)

        logger.info(f"Created consensus decision {decision.decision_id}: {title}")
        return decision

    async def submit_vote(
        self, decision_id: UUID, agent_id: str, vote: VoteChoice, comment: str = None
    ) -> bool:
        """Submit a vote for a consensus decision."""
        decision = self.consensus_decisions.get(decision_id)
        if not decision:
            return False

        if decision.resolved:
            return False  # Already resolved

        # Check if agent is participant
        session = self.active_sessions.get(decision.session_id)
        if not session or agent_id not in session.participants:
            return False

        # Record vote
        decision.votes[agent_id] = vote
        if comment:
            decision.comments[agent_id] = comment

        # Update in Redis
        decision_key = f"collaboration:decision:{decision.decision_id}"
        self.redis.setex(decision_key, 86400, decision.model_dump_json())

        # Check if consensus is reached
        await self._check_consensus(decision)

        logger.info(f"Agent {agent_id} voted {vote.value} on decision {decision_id}")
        return True

    async def escalate_issue(
        self,
        session_id: UUID,
        issue_type: str,
        description: str,
        escalated_by: str,
        affected_participants: List[str] = None,
        priority: str = "medium",
    ) -> EscalationRequest:
        """Escalate an issue that cannot be resolved through normal collaboration."""
        escalation = EscalationRequest(
            session_id=session_id,
            issue_type=issue_type,
            description=description,
            escalated_by=escalated_by,
            affected_participants=affected_participants or [],
            priority=priority,
            resolution_deadline=datetime.utcnow()
            + timedelta(hours=4),  # 4 hours to resolve
        )

        # Store escalation
        escalation_key = f"collaboration:escalation:{escalation.escalation_id}"
        self.redis.setex(escalation_key, 86400, escalation.model_dump_json())

        # Send escalation message to management agents or system administrators
        escalation_message = A2AMessage(
            sender_agent_id=escalated_by,
            message_type=MessageType.ESCALATION,
            priority=MessagePriority.HIGH,
            payload={
                "escalation_id": str(escalation.escalation_id),
                "session_id": str(session_id),
                "issue_type": issue_type,
                "description": description,
                "priority": priority,
                "affected_participants": affected_participants or [],
            },
            requires_response=True,
        )

        # Broadcast to management agents (would be filtered by agent type)
        await self.message_broker.send_message(escalation_message)

        logger.warning(f"Issue escalated in session {session_id}: {description}")
        return escalation

    async def complete_collaboration(
        self, session_id: UUID, outputs: Dict = None
    ) -> bool:
        """Complete a collaboration session."""
        session = self.active_sessions.get(session_id)
        if not session:
            return False

        session.status = CollaborationStatus.COMPLETED
        session.completed_at = datetime.utcnow()
        if outputs:
            session.outputs.update(outputs)

        # Calculate metrics
        metrics = await self._calculate_session_metrics(session)

        # Update in Redis
        session_key = f"collaboration:session:{session_id}"
        self.redis.setex(session_key, 86400, session.model_dump_json())

        metrics_key = f"collaboration:metrics:{session_id}"
        self.redis.setex(metrics_key, 86400, metrics.model_dump_json())

        # Notify participants
        await self._notify_participants(
            session, f"Collaboration '{session.title}' has been completed successfully!"
        )

        logger.info(f"Completed collaboration session {session_id}")
        return True

    async def _check_consensus(self, decision: ConsensusDecision) -> bool:
        """Check if consensus has been reached on a decision."""
        total_participants = len(self.active_sessions[decision.session_id].participants)
        total_votes = len(decision.votes)

        if total_votes < total_participants:
            return False  # Not all participants have voted

        # Count approval votes
        approve_votes = sum(
            1 for vote in decision.votes.values() if vote == VoteChoice.APPROVE
        )
        consensus_rate = approve_votes / total_votes

        if consensus_rate >= decision.required_consensus:
            decision.resolved = True
            decision.resolution = "approved"
            decision.resolved_at = datetime.utcnow()

            # Notify participants of consensus
            session = self.active_sessions[decision.session_id]
            await self._notify_participants(
                session,
                f"Consensus reached on '{decision.title}': APPROVED ({consensus_rate:.1%} approval)",
            )

            logger.info(f"Consensus reached on decision {decision.decision_id}")
            return True

        # Check if consensus is impossible (too many rejections)
        reject_votes = sum(
            1 for vote in decision.votes.values() if vote == VoteChoice.REJECT
        )
        max_possible_approval = (total_participants - reject_votes) / total_participants

        if max_possible_approval < decision.required_consensus:
            decision.resolved = True
            decision.resolution = "rejected"
            decision.resolved_at = datetime.utcnow()

            # Notify participants of failed consensus
            session = self.active_sessions[decision.session_id]
            await self._notify_participants(
                session,
                f"Consensus failed on '{decision.title}': REJECTED (insufficient support)",
            )

            logger.info(f"Consensus failed on decision {decision.decision_id}")
            return True

        return False

    async def _notify_participants(
        self, session: CollaborationSession, message: str, exclude_agent: str = None
    ) -> None:
        """Send a notification to all session participants."""
        notification = A2AMessage(
            sender_agent_id="collaboration_orchestrator",
            message_type=MessageType.NOTIFICATION,
            payload={
                "session_id": str(session.session_id),
                "message": message,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

        for participant in session.participants:
            if participant != exclude_agent:
                notification.recipient_agent_id = participant
                await self.message_broker.send_message(notification)

    async def _calculate_session_metrics(
        self, session: CollaborationSession
    ) -> CollaborationMetrics:
        """Calculate metrics for a completed collaboration session."""
        # Get conversation history
        messages = await self.message_broker.get_conversation_history(
            session.session_id
        )

        # Count decisions made
        decisions_made = len(
            [
                d
                for d in self.consensus_decisions.values()
                if d.session_id == session.session_id
            ]
        )
        consensus_achieved = len(
            [
                d
                for d in self.consensus_decisions.values()
                if d.session_id == session.session_id
                and d.resolved
                and d.resolution == "approved"
            ]
        )

        # Calculate duration
        duration = None
        if session.started_at and session.completed_at:
            duration = (
                session.completed_at - session.started_at
            ).total_seconds() / 60  # minutes

        return CollaborationMetrics(
            session_id=session.session_id,
            total_participants=len(session.participants),
            active_participants=len(session.participants),  # Simplified
            messages_exchanged=len(messages),
            decisions_made=decisions_made,
            consensus_achieved=consensus_achieved,
            consensus_rate=consensus_achieved / max(1, decisions_made),
            average_response_time=15.0,  # Simplified - would calculate from message timestamps
            total_duration=duration,
            efficiency_score=0.8,  # Simplified scoring
            quality_score=0.9,  # Simplified scoring
        )
