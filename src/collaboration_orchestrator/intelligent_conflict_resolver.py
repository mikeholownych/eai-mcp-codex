"""Intelligent Conflict Resolver for multi-developer coordination."""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from uuid import UUID

import asyncpg
from redis import Redis

from src.common.database import DatabaseManager
from src.common.redis_client import get_redis_connection
from src.a2a_communication.models import A2AMessage, MessageType, MessagePriority
from src.a2a_communication.message_broker import A2AMessageBroker

from .multi_developer_models import (
    ConflictType,
    ConflictSeverity,
    ResolutionStrategy,
    ConflictResolutionLog,
    DeveloperProfile,
)
from .developer_profile_manager import DeveloperProfileManager

logger = logging.getLogger(__name__)


class ConflictAnalyzer:
    """Analyzes conflicts to determine type, severity, and optimal resolution strategy."""

    def __init__(self):
        self.conflict_patterns = {
            ConflictType.MERGE_CONFLICT: {
                "keywords": ["merge", "conflict", "git", "branch", "commit"],
                "base_severity": ConflictSeverity.MEDIUM,
                "preferred_strategy": ResolutionStrategy.AUTOMATED,
            },
            ConflictType.DESIGN_CONFLICT: {
                "keywords": ["architecture", "design", "pattern", "approach"],
                "base_severity": ConflictSeverity.HIGH,
                "preferred_strategy": ResolutionStrategy.EXPERTISE_BASED,
            },
            ConflictType.RESOURCE_CONFLICT: {
                "keywords": ["resource", "database", "api", "service"],
                "base_severity": ConflictSeverity.MEDIUM,
                "preferred_strategy": ResolutionStrategy.CONSENSUS,
            },
            ConflictType.TIMELINE_CONFLICT: {
                "keywords": ["deadline", "timeline", "schedule", "delay"],
                "base_severity": ConflictSeverity.HIGH,
                "preferred_strategy": ResolutionStrategy.LEAD_DECISION,
            },
            ConflictType.APPROACH_CONFLICT: {
                "keywords": ["method", "implementation", "algorithm", "solution"],
                "base_severity": ConflictSeverity.MEDIUM,
                "preferred_strategy": ResolutionStrategy.VOTE,
            },
            ConflictType.PRIORITY_CONFLICT: {
                "keywords": ["priority", "urgent", "important", "order"],
                "base_severity": ConflictSeverity.HIGH,
                "preferred_strategy": ResolutionStrategy.LEAD_DECISION,
            },
            ConflictType.DEPENDENCY_CONFLICT: {
                "keywords": ["dependency", "prerequisite", "blocking", "waiting"],
                "base_severity": ConflictSeverity.MEDIUM,
                "preferred_strategy": ResolutionStrategy.AUTOMATED,
            },
            ConflictType.QUALITY_CONFLICT: {
                "keywords": ["quality", "standard", "code review", "testing"],
                "base_severity": ConflictSeverity.MEDIUM,
                "preferred_strategy": ResolutionStrategy.EXPERTISE_BASED,
            },
        }

    def analyze_conflict(
        self, description: str, context: Dict[str, Any], involved_agents: List[str]
    ) -> Tuple[ConflictType, ConflictSeverity, ResolutionStrategy]:
        """Analyze conflict and determine type, severity, and resolution strategy."""
        description_lower = description.lower()

        # Determine conflict type
        conflict_type = ConflictType.APPROACH_CONFLICT  # default
        max_matches = 0

        for c_type, pattern in self.conflict_patterns.items():
            matches = sum(
                1 for keyword in pattern["keywords"] if keyword in description_lower
            )
            if matches > max_matches:
                max_matches = matches
                conflict_type = c_type

        # Determine severity
        base_severity = self.conflict_patterns[conflict_type]["base_severity"]
        severity = base_severity

        # Adjust severity based on context
        if context.get("deadline_impact", False):
            severity = (
                ConflictSeverity.HIGH
                if severity == ConflictSeverity.MEDIUM
                else ConflictSeverity.CRITICAL
            )

        if len(involved_agents) > 3:
            severity = (
                ConflictSeverity.HIGH
                if severity == ConflictSeverity.MEDIUM
                else ConflictSeverity.CRITICAL
            )

        if context.get("affects_critical_path", False):
            severity = ConflictSeverity.CRITICAL

        # Determine resolution strategy
        preferred_strategy = self.conflict_patterns[conflict_type]["preferred_strategy"]

        # Override strategy based on severity and context
        if severity == ConflictSeverity.CRITICAL:
            preferred_strategy = ResolutionStrategy.ESCALATION
        elif (
            context.get("has_domain_expert", False)
            and preferred_strategy != ResolutionStrategy.AUTOMATED
        ):
            preferred_strategy = ResolutionStrategy.EXPERTISE_BASED

        return conflict_type, severity, preferred_strategy


class AutomatedResolutionEngine:
    """Handles automated resolution of certain types of conflicts."""

    def __init__(self, profile_manager: DeveloperProfileManager):
        self.profile_manager = profile_manager

    async def can_resolve_automatically(self, conflict: ConflictResolutionLog) -> bool:
        """Check if conflict can be resolved automatically."""
        automated_types = [
            ConflictType.MERGE_CONFLICT,
            ConflictType.DEPENDENCY_CONFLICT,
        ]

        return (
            conflict.conflict_type in automated_types
            and conflict.conflict_severity
            in [ConflictSeverity.LOW, ConflictSeverity.MEDIUM]
            and len(conflict.involved_agents) <= 2
        )

    async def resolve_merge_conflict(
        self, conflict: ConflictResolutionLog
    ) -> Tuple[bool, str]:
        """Attempt to resolve merge conflicts automatically."""
        try:
            # In a real implementation, this would integrate with Git operations
            # For now, simulate the resolution process

            context = conflict.conflict_context
            if context.get("conflict_files"):
                files = context["conflict_files"]
                steps = [
                    f"Analyzing conflicts in {len(files)} files",
                    "Attempting automatic merge resolution",
                    "Running code quality checks",
                    "Validating merge result",
                ]
                logger.debug("Resolution steps: %s", steps)
                
                # Simulate success rate based on complexity
                complexity = len(files) + len(conflict.involved_agents)
                success_rate = max(0.3, 0.9 - (complexity * 0.1))

                if success_rate > 0.7:  # Simplified success threshold
                    return True, "Merge conflicts resolved automatically"
                else:
                    return False, "Merge conflicts too complex for automatic resolution"

            return False, "Insufficient information for automatic resolution"

        except Exception as e:
            logger.error(f"Error in automatic merge conflict resolution: {e}")
            return False, f"Automatic resolution failed: {str(e)}"

    async def resolve_dependency_conflict(
        self, conflict: ConflictResolutionLog
    ) -> Tuple[bool, str]:
        """Attempt to resolve dependency conflicts automatically."""
        try:
            context = conflict.conflict_context
            if context.get("conflicting_dependencies"):
                deps = context["conflicting_dependencies"]
                logger.debug("Conflicting dependencies: %s", deps)
                
                # Simple heuristic: if there's a clear priority order, resolve automatically
                if context.get("priority_order"):
                    priority_order = context["priority_order"]
                    resolution = (
                        f"Resolved based on priority: {' > '.join(priority_order)}"
                    )
                    return True, resolution

                # If one dependency is much more critical, prioritize it
                if context.get("criticality_scores"):
                    scores = context["criticality_scores"]
                    max_score = max(scores.values())
                    if max_score > 0.8:
                        critical_dep = max(scores, key=scores.get)
                        return True, f"Prioritized critical dependency: {critical_dep}"

            return False, "Cannot resolve dependency conflict automatically"

        except Exception as e:
            logger.error(f"Error in automatic dependency conflict resolution: {e}")
            return False, f"Automatic resolution failed: {str(e)}"


class IntelligentConflictResolver:
    """Main conflict resolution system for multi-developer coordination."""

    def __init__(
        self,
        profile_manager: DeveloperProfileManager,
        message_broker: Optional[A2AMessageBroker] = None,
        postgres_pool: Optional[asyncpg.Pool] = None,
        redis: Optional[Redis] = None,
    ):
        self.profile_manager = profile_manager
        self.message_broker = message_broker or A2AMessageBroker()
        self.postgres_pool = postgres_pool
        self.redis = redis or get_redis_connection()

        self.conflict_analyzer = ConflictAnalyzer()
        self.automated_engine = AutomatedResolutionEngine(profile_manager)

        # Track active conflicts
        self.active_conflicts: Dict[UUID, ConflictResolutionLog] = {}

    async def _get_db_connection(self) -> asyncpg.Connection:
        """Get database connection from pool or create new one."""
        if self.postgres_pool:
            return await self.postgres_pool.acquire()
        else:
            db_manager = DatabaseManager("collaboration_db")
            await db_manager.connect()
            return await db_manager.get_connection().__aenter__()
    
    async def detect_conflict(
        self,
        session_id: UUID,
        plan_id: Optional[UUID],
        conflict_description: str,
        involved_agents: List[str],
        context: Dict[str, Any] = None,
        detected_by: Optional[str] = None,
    ) -> ConflictResolutionLog:
        """Detect and analyze a conflict."""
        context = context or {}

        # Analyze the conflict
        conflict_type, severity, suggested_strategy = (
            self.conflict_analyzer.analyze_conflict(
                conflict_description, context, involved_agents
            )
        )

        # Create conflict log
        conflict = ConflictResolutionLog(
            session_id=session_id,
            plan_id=plan_id,
            conflict_type=conflict_type,
            conflict_description=conflict_description,
            involved_agents=involved_agents,
            conflict_severity=severity,
            conflict_context=context,
            resolution_strategy=suggested_strategy,
        )

        # Store in database
        await self._store_conflict(conflict)

        # Add to active conflicts
        self.active_conflicts[conflict.conflict_id] = conflict

        # Cache in Redis
        conflict_key = f"conflict:{conflict.conflict_id}"
        self.redis.setex(conflict_key, 86400, conflict.model_dump_json())

        logger.warning(
            f"Conflict detected: {conflict_type.value} (severity: {severity.value}) "
            f"involving agents: {involved_agents}"
        )

        return conflict

    async def resolve_conflict(self, conflict_id: UUID) -> bool:
        """Attempt to resolve a conflict using the appropriate strategy."""
        conflict = await self.get_conflict(conflict_id)
        if not conflict or conflict.status != "open":
            return False

        try:
            resolved = False
            resolution_outcome = ""

            if conflict.resolution_strategy == ResolutionStrategy.AUTOMATED:
                resolved, resolution_outcome = await self._resolve_automatically(
                    conflict
                )
            elif conflict.resolution_strategy == ResolutionStrategy.CONSENSUS:
                resolved, resolution_outcome = await self._resolve_by_consensus(
                    conflict
                )
            elif conflict.resolution_strategy == ResolutionStrategy.VOTE:
                resolved, resolution_outcome = await self._resolve_by_vote(conflict)
            elif conflict.resolution_strategy == ResolutionStrategy.EXPERTISE_BASED:
                resolved, resolution_outcome = await self._resolve_by_expertise(
                    conflict
                )
            elif conflict.resolution_strategy == ResolutionStrategy.LEAD_DECISION:
                resolved, resolution_outcome = await self._resolve_by_lead_decision(
                    conflict
                )
            elif conflict.resolution_strategy == ResolutionStrategy.ESCALATION:
                resolved, resolution_outcome = await self._escalate_conflict(conflict)

            if resolved:
                await self._mark_conflict_resolved(conflict, resolution_outcome)

                # Update collaboration history
                for i, agent_1 in enumerate(conflict.involved_agents):
                    for agent_2 in conflict.involved_agents[i + 1 :]:
                        await self.profile_manager.update_collaboration_history(
                            conflict.session_id,
                            agent_1,
                            agent_2,
                            "conflict_resolution",
                            success=True,
                            notes=f"Resolved: {conflict.conflict_type.value}",
                        )

            return resolved

        except Exception as e:
            logger.error(f"Error resolving conflict {conflict_id}: {e}")
            return False

    async def _resolve_automatically(
        self, conflict: ConflictResolutionLog
    ) -> Tuple[bool, str]:
        """Resolve conflict using automated methods."""
        if not await self.automated_engine.can_resolve_automatically(conflict):
            return False, "Cannot resolve automatically"

        if conflict.conflict_type == ConflictType.MERGE_CONFLICT:
            return await self.automated_engine.resolve_merge_conflict(conflict)
        elif conflict.conflict_type == ConflictType.DEPENDENCY_CONFLICT:
            return await self.automated_engine.resolve_dependency_conflict(conflict)

        return False, "No automated resolution available"

    async def _resolve_by_consensus(
        self, conflict: ConflictResolutionLog
    ) -> Tuple[bool, str]:
        """Resolve conflict through consensus building."""
        # Send consensus request to involved agents
        consensus_message = A2AMessage(
            sender_agent_id="conflict_resolver",
            message_type=MessageType.CONSENSUS,
            priority=MessagePriority.HIGH,
            payload={
                "conflict_id": str(conflict.conflict_id),
                "conflict_type": conflict.conflict_type.value,
                "description": conflict.conflict_description,
                "options": conflict.conflict_context.get("resolution_options", []),
                "deadline": (datetime.utcnow() + timedelta(hours=2)).isoformat(),
            },
            requires_response=True,
            response_timeout=7200,  # 2 hours
        )

        # Send to all involved agents
        for agent_id in conflict.involved_agents:
            consensus_message.recipient_agent_id = agent_id
            await self.message_broker.send_message(consensus_message)

        # For now, return False as consensus building is async
        # In a real implementation, this would track responses and determine consensus
        return False, "Consensus building initiated - awaiting responses"

    async def _resolve_by_vote(
        self, conflict: ConflictResolutionLog
    ) -> Tuple[bool, str]:
        """Resolve conflict through voting."""
        # Similar to consensus but with majority rule
        options = conflict.conflict_context.get("resolution_options", [])
        if not options:
            return False, "No resolution options available for voting"

        # Send voting request
        vote_message = A2AMessage(
            sender_agent_id="conflict_resolver",
            message_type=MessageType.CONSENSUS,
            priority=MessagePriority.HIGH,
            payload={
                "conflict_id": str(conflict.conflict_id),
                "voting_type": "majority_rule",
                "options": options,
                "deadline": (datetime.utcnow() + timedelta(hours=1)).isoformat(),
            },
            requires_response=True,
            response_timeout=3600,  # 1 hour
        )

        for agent_id in conflict.involved_agents:
            vote_message.recipient_agent_id = agent_id
            await self.message_broker.send_message(vote_message)

        return False, "Voting initiated - awaiting responses"

    async def _resolve_by_expertise(
        self, conflict: ConflictResolutionLog
    ) -> Tuple[bool, str]:
        """Resolve conflict based on domain expertise."""
        # Find the most experienced agent for this conflict type
        expert_agent = None
        max_expertise = 0.0

        for agent_id in conflict.involved_agents:
            profile = await self.profile_manager.get_developer_profile(agent_id)
            if not profile:
                continue

            # Calculate expertise score for this conflict type
            expertise_score = self._calculate_expertise_score(profile, conflict)
            if expertise_score > max_expertise:
                max_expertise = expertise_score
                expert_agent = agent_id

        if expert_agent and max_expertise > 0.7:
            # Send decision request to expert
            expert_message = A2AMessage(
                sender_agent_id="conflict_resolver",
                recipient_agent_id=expert_agent,
                message_type=MessageType.REQUEST,
                priority=MessagePriority.HIGH,
                payload={
                    "conflict_id": str(conflict.conflict_id),
                    "request_type": "expert_decision",
                    "conflict_description": conflict.conflict_description,
                    "context": conflict.conflict_context,
                    "authority": "domain_expert",
                },
                requires_response=True,
                response_timeout=1800,  # 30 minutes
            )

            await self.message_broker.send_message(expert_message)
            return False, f"Expert decision requested from {expert_agent}"

        return False, "No suitable domain expert found"

    async def _resolve_by_lead_decision(
        self, conflict: ConflictResolutionLog
    ) -> Tuple[bool, str]:
        """Resolve conflict through team lead decision."""
        # Find team lead from the plan
        if not conflict.plan_id:
            return False, "No plan associated with conflict"

        # Get team coordination plan
        conn = await self._get_db_connection()
        try:
            row = await conn.fetchrow(
                "SELECT team_lead FROM team_coordination_plans WHERE plan_id = $1",
                str(conflict.plan_id),
            )
            if not row:
                return False, "Team lead not found"

            team_lead = row["team_lead"]

            # Send decision request to team lead
            lead_message = A2AMessage(
                sender_agent_id="conflict_resolver",
                recipient_agent_id=team_lead,
                message_type=MessageType.REQUEST,
                priority=MessagePriority.HIGH,
                payload={
                    "conflict_id": str(conflict.conflict_id),
                    "request_type": "lead_decision",
                    "conflict_description": conflict.conflict_description,
                    "involved_agents": conflict.involved_agents,
                    "context": conflict.conflict_context,
                    "authority": "team_lead",
                },
                requires_response=True,
                response_timeout=1800,  # 30 minutes
            )

            await self.message_broker.send_message(lead_message)
            return False, f"Lead decision requested from {team_lead}"

        finally:
            if not self.postgres_pool:
                await conn.close()
            else:
                await self.postgres_pool.release(conn)

    async def _escalate_conflict(
        self, conflict: ConflictResolutionLog
    ) -> Tuple[bool, str]:
        """Escalate conflict to higher-level management or human intervention."""
        # Mark as requiring human intervention
        conflict.human_intervention = True

        # Send escalation message
        escalation_message = A2AMessage(
            sender_agent_id="conflict_resolver",
            message_type=MessageType.ESCALATION,
            priority=MessagePriority.URGENT,
            payload={
                "conflict_id": str(conflict.conflict_id),
                "escalation_reason": "Conflict requires human intervention",
                "conflict_type": conflict.conflict_type.value,
                "severity": conflict.conflict_severity.value,
                "description": conflict.conflict_description,
                "involved_agents": conflict.involved_agents,
                "context": conflict.conflict_context,
            },
        )

        # Broadcast to management agents
        await self.message_broker.send_message(escalation_message)

        return False, "Conflict escalated to management"

    def _calculate_expertise_score(
        self, profile: DeveloperProfile, conflict: ConflictResolutionLog
    ) -> float:
        """Calculate expertise score for resolving a specific conflict."""
        base_score = 0.0

        # Experience level contribution
        experience_scores = {
            "junior": 0.2,
            "intermediate": 0.4,
            "senior": 0.6,
            "lead": 0.8,
            "architect": 1.0,
        }
        base_score += experience_scores.get(profile.experience_level.value, 0.4)

        # Specialization relevance
        conflict_specializations = {
            ConflictType.DESIGN_CONFLICT: ["architecture", "fullstack"],
            ConflictType.MERGE_CONFLICT: ["devops", "backend"],
            ConflictType.QUALITY_CONFLICT: ["qa", "senior"],
            ConflictType.SECURITY: ["security"],
        }

        relevant_specs = conflict_specializations.get(conflict.conflict_type, [])
        if any(
            spec in [s.value for s in profile.specializations]
            for spec in relevant_specs
        ):
            base_score += 0.3

        # Performance history
        base_score += profile.performance_metrics.overall_score * 0.2

        return min(1.0, base_score)

    async def _store_conflict(self, conflict: ConflictResolutionLog) -> None:
        """Store conflict in database."""
        conn = await self._get_db_connection()
        try:
            await conn.execute(
                """
                INSERT INTO conflict_resolution_logs (
                    conflict_id, session_id, plan_id, conflict_type, conflict_description,
                    involved_agents, conflict_severity, conflict_context, resolution_strategy,
                    status, metadata, created_at, updated_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
            """,
                str(conflict.conflict_id),
                str(conflict.session_id),
                str(conflict.plan_id) if conflict.plan_id else None,
                conflict.conflict_type.value,
                conflict.conflict_description,
                json.dumps(conflict.involved_agents),
                conflict.conflict_severity.value,
                json.dumps(conflict.conflict_context),
                (
                    conflict.resolution_strategy.value
                    if conflict.resolution_strategy
                    else None
                ),
                conflict.status,
                json.dumps(conflict.metadata),
                conflict.created_at,
                conflict.updated_at,
            )
        finally:
            if not self.postgres_pool:
                await conn.close()
            else:
                await self.postgres_pool.release(conn)

    async def _mark_conflict_resolved(
        self, conflict: ConflictResolutionLog, outcome: str
    ) -> None:
        """Mark conflict as resolved."""
        conflict.status = "resolved"
        conflict.resolution_outcome = outcome
        conflict.resolved_at = datetime.utcnow()
        conflict.updated_at = datetime.utcnow()

        # Update in database
        conn = await self._get_db_connection()
        try:
            await conn.execute(
                """
                UPDATE conflict_resolution_logs SET
                    status = $2, resolution_outcome = $3, resolved_at = $4, updated_at = $5
                WHERE conflict_id = $1
            """,
                str(conflict.conflict_id),
                conflict.status,
                conflict.resolution_outcome,
                conflict.resolved_at,
                conflict.updated_at,
            )
        finally:
            if not self.postgres_pool:
                await conn.close()
            else:
                await self.postgres_pool.release(conn)

        # Update cache
        conflict_key = f"conflict:{conflict.conflict_id}"
        self.redis.setex(conflict_key, 86400, conflict.model_dump_json())

        # Remove from active conflicts
        if conflict.conflict_id in self.active_conflicts:
            del self.active_conflicts[conflict.conflict_id]

        logger.info(f"Conflict {conflict.conflict_id} resolved: {outcome}")

    async def get_conflict(self, conflict_id: UUID) -> Optional[ConflictResolutionLog]:
        """Get conflict by ID."""
        # Check active conflicts first
        if conflict_id in self.active_conflicts:
            return self.active_conflicts[conflict_id]

        # Check Redis cache
        conflict_key = f"conflict:{conflict_id}"
        cached_conflict = self.redis.get(conflict_key)
        if cached_conflict:
            conflict_data = json.loads(cached_conflict)
            conflict = ConflictResolutionLog(**conflict_data)
            if conflict.status == "open":
                self.active_conflicts[conflict_id] = conflict
            return conflict

        # Load from database
        conn = await self._get_db_connection()
        try:
            row = await conn.fetchrow(
                "SELECT * FROM conflict_resolution_logs WHERE conflict_id = $1",
                str(conflict_id),
            )
            if not row:
                return None

            conflict_data = dict(row)
            conflict_data["conflict_id"] = UUID(conflict_data["conflict_id"])
            conflict_data["session_id"] = UUID(conflict_data["session_id"])
            if conflict_data["plan_id"]:
                conflict_data["plan_id"] = UUID(conflict_data["plan_id"])
            conflict_data["conflict_type"] = ConflictType(
                conflict_data["conflict_type"]
            )
            conflict_data["conflict_severity"] = ConflictSeverity(
                conflict_data["conflict_severity"]
            )
            if conflict_data["resolution_strategy"]:
                conflict_data["resolution_strategy"] = ResolutionStrategy(
                    conflict_data["resolution_strategy"]
                )
            conflict_data["involved_agents"] = json.loads(
                conflict_data["involved_agents"]
            )
            conflict_data["conflict_context"] = json.loads(
                conflict_data["conflict_context"] or "{}"
            )
            conflict_data["metadata"] = json.loads(conflict_data["metadata"] or "{}")

            conflict = ConflictResolutionLog(**conflict_data)

            # Cache it
            self.redis.setex(conflict_key, 86400, conflict.model_dump_json())
            if conflict.status == "open":
                self.active_conflicts[conflict_id] = conflict

            return conflict

        finally:
            if not self.postgres_pool:
                await conn.close()
            else:
                await self.postgres_pool.release(conn)

    async def get_conflicts_for_session(
        self, session_id: UUID
    ) -> List[ConflictResolutionLog]:
        """Get all conflicts for a session."""
        conn = await self._get_db_connection()
        try:
            rows = await conn.fetch(
                "SELECT * FROM conflict_resolution_logs WHERE session_id = $1 ORDER BY created_at DESC",
                str(session_id),
            )

            conflicts = []
            for row in rows:
                conflict_data = dict(row)
                conflict_data["conflict_id"] = UUID(conflict_data["conflict_id"])
                conflict_data["session_id"] = UUID(conflict_data["session_id"])
                if conflict_data["plan_id"]:
                    conflict_data["plan_id"] = UUID(conflict_data["plan_id"])
                conflict_data["conflict_type"] = ConflictType(
                    conflict_data["conflict_type"]
                )
                conflict_data["conflict_severity"] = ConflictSeverity(
                    conflict_data["conflict_severity"]
                )
                if conflict_data["resolution_strategy"]:
                    conflict_data["resolution_strategy"] = ResolutionStrategy(
                        conflict_data["resolution_strategy"]
                    )
                conflict_data["involved_agents"] = json.loads(
                    conflict_data["involved_agents"]
                )
                conflict_data["conflict_context"] = json.loads(
                    conflict_data["conflict_context"] or "{}"
                )
                conflict_data["metadata"] = json.loads(
                    conflict_data["metadata"] or "{}"
                )

                conflicts.append(ConflictResolutionLog(**conflict_data))

            return conflicts

        finally:
            if not self.postgres_pool:
                await conn.close()
            else:
                await self.postgres_pool.release(conn)

    async def get_conflict_statistics(
        self, session_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """Get conflict resolution statistics."""
        conn = await self._get_db_connection()
        try:
            where_clause = "WHERE session_id = $1" if session_id else ""
            params = [str(session_id)] if session_id else []

            # Get basic counts
            stats_query = f"""
                SELECT 
                    conflict_type,
                    conflict_severity,
                    status,
                    COUNT(*) as count,
                    AVG(EXTRACT(EPOCH FROM (resolved_at - created_at))/3600) as avg_resolution_hours
                FROM conflict_resolution_logs
                {where_clause}
                GROUP BY conflict_type, conflict_severity, status
            """

            rows = await conn.fetch(stats_query, *params)

            statistics = {
                "total_conflicts": 0,
                "resolved_conflicts": 0,
                "open_conflicts": 0,
                "by_type": {},
                "by_severity": {},
                "average_resolution_time_hours": 0.0,
                "resolution_success_rate": 0.0,
            }

            total_resolution_time = 0.0
            resolved_count = 0

            for row in rows:
                count = row["count"]
                statistics["total_conflicts"] += count

                if row["status"] == "resolved":
                    statistics["resolved_conflicts"] += count
                    resolved_count += count
                    if row["avg_resolution_hours"]:
                        total_resolution_time += row["avg_resolution_hours"] * count
                elif row["status"] == "open":
                    statistics["open_conflicts"] += count

                # By type
                conflict_type = row["conflict_type"]
                if conflict_type not in statistics["by_type"]:
                    statistics["by_type"][conflict_type] = 0
                statistics["by_type"][conflict_type] += count

                # By severity
                severity = row["conflict_severity"]
                if severity not in statistics["by_severity"]:
                    statistics["by_severity"][severity] = 0
                statistics["by_severity"][severity] += count

            # Calculate averages
            if resolved_count > 0:
                statistics["average_resolution_time_hours"] = (
                    total_resolution_time / resolved_count
                )
                statistics["resolution_success_rate"] = (
                    statistics["resolved_conflicts"] / statistics["total_conflicts"]
                )

            return statistics

        finally:
            if not self.postgres_pool:
                await conn.close()
            else:
                await self.postgres_pool.release(conn)
