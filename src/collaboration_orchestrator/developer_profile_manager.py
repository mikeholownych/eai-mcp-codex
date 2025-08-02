"""Developer Profile Manager for multi-developer coordination."""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from uuid import UUID

import asyncpg
from redis import Redis

from src.common.database import DatabaseManager
from src.common.redis_client import get_redis_connection
from src.common.caching import get_cache_manager
from .multi_developer_models import (
    DeveloperProfile,
    DeveloperSpecialization,
    ExperienceLevel,
    PerformanceMetrics,
    TaskType,
    DeveloperWorkload,
    AgentCollaborationHistory,
)

logger = logging.getLogger(__name__)


class DeveloperProfileManager:
    """Manages developer agent profiles, capabilities, and performance tracking."""

    @classmethod
    async def create(
        cls,
        redis: Optional[Redis] = None,
        postgres_pool: Optional[asyncpg.Pool] = None
    ) -> "DeveloperProfileManager":
        """Create a new DeveloperProfileManager instance."""
        instance = cls()
        instance.redis = redis or await get_redis_connection()
        # Create a DatabaseManager that uses the existing pool
        if postgres_pool:
            # Create a mock DatabaseManager that uses the existing pool
            instance.db_manager = DatabaseManager('multi_developer_orchestrator')
            instance.db_manager._pool = postgres_pool
        else:
            instance.db_manager = DatabaseManager('multi_developer_orchestrator')
            await instance.db_manager.connect()
        instance.profile_cache = {}
        instance.cache_manager = get_cache_manager("orchestrator")
        return instance

    def __init__(
        self, 
        db_manager: Optional[DatabaseManager] = None,
        redis: Optional[Redis] = None
    ) -> None:
        self.db_manager = db_manager or DatabaseManager(db_name="mcp_database")
        self.redis = redis or get_redis_connection()
        self.profile_cache: Dict[str, DeveloperProfile] = {}
        self.cache_manager = get_cache_manager("orchestrator")

    async def _get_db_connection(self) -> asyncpg.Connection:
        """Get database connection from pool or create new one."""
        return await self.db_manager.get_connection().__aenter__()
    
    async def create_developer_profile(
        self,
        agent_id: str,
        agent_type: str = "developer",
        specializations: List[DeveloperSpecialization] = None,
        programming_languages: List[str] = None,
        frameworks: List[str] = None,
        experience_level: ExperienceLevel = ExperienceLevel.INTERMEDIATE,
        preferred_tasks: List[TaskType] = None,
        max_concurrent_tasks: int = 3,
        metadata: Dict = None,
    ) -> DeveloperProfile:
        """Create a new developer profile."""
        profile = DeveloperProfile(
            agent_id=agent_id,
            agent_type=agent_type,
            specializations=specializations or [],
            programming_languages=programming_languages or [],
            frameworks=frameworks or [],
            experience_level=experience_level,
            preferred_tasks=preferred_tasks or [],
            max_concurrent_tasks=max_concurrent_tasks,
            metadata=metadata or {},
        )

        # Store in database
        async with self.db_manager.get_connection() as conn:
            await conn.execute("""
                INSERT INTO developer_profiles (
                    agent_id, agent_type, specializations, programming_languages, 
                    frameworks, experience_level, preferred_tasks, availability_schedule,
                    current_workload, max_concurrent_tasks, performance_metrics,
                    collaboration_preferences, trust_scores, metadata, created_at, updated_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16)
            """,
                agent_id,
                agent_type,
                json.dumps([s.value for s in profile.specializations]),
                json.dumps(profile.programming_languages),
                json.dumps(profile.frameworks),
                profile.experience_level.value,
                json.dumps([t.value for t in profile.preferred_tasks]),
                json.dumps(profile.availability_schedule),
                profile.current_workload,
                profile.max_concurrent_tasks,
                profile.performance_metrics.model_dump_json(),
                json.dumps(profile.collaboration_preferences),
                json.dumps(profile.trust_scores),
                json.dumps(profile.metadata),
                profile.created_at,
                profile.updated_at,
            )
        
        # Cache the profile
        self.profile_cache[agent_id] = profile

        # Store in Redis for quick access
        profile_key = f"developer_profile:{agent_id}"
        self.redis.setex(profile_key, 3600, profile.model_dump_json())

        logger.info(f"Created developer profile for agent {agent_id}")
        return profile

    async def get_developer_profile(self, agent_id: str) -> Optional[DeveloperProfile]:
        """Get developer profile by agent ID."""
        # Check cache first
        if agent_id in self.profile_cache:
            return self.profile_cache[agent_id]

        # Check Redis cache
        profile_key = f"developer_profile:{agent_id}"
        cached_profile = self.redis.get(profile_key)
        if cached_profile:
            profile_data = json.loads(cached_profile)
            profile = DeveloperProfile(**profile_data)
            self.profile_cache[agent_id] = profile
            return profile

        # Load from database
        async with self.db_manager.get_connection() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM developer_profiles WHERE agent_id = $1", agent_id
            )
            if not row:
                return None

            # Convert row to profile
            profile_data = dict(row)
            profile_data["specializations"] = [
                DeveloperSpecialization(s)
                for s in json.loads(profile_data["specializations"] or "[]")
            ]
            profile_data["programming_languages"] = json.loads(
                profile_data["programming_languages"] or "[]"
            )
            profile_data["frameworks"] = json.loads(profile_data["frameworks"] or "[]")
            profile_data["experience_level"] = ExperienceLevel(
                profile_data["experience_level"]
            )
            profile_data["preferred_tasks"] = [
                TaskType(t) for t in json.loads(profile_data["preferred_tasks"] or "[]")
            ]
            profile_data['availability_schedule'] = json.loads(profile_data['availability_schedule'] or '{}')
            profile_data['current_workload'] = profile_data['current_workload']
            profile_data['max_concurrent_tasks'] = profile_data['max_concurrent_tasks']
            profile_data['performance_metrics'] = PerformanceMetrics(**json.loads(profile_data['performance_metrics'] or '{}'))
            profile_data['collaboration_preferences'] = json.loads(profile_data['collaboration_preferences'] or '{}')
            profile_data['trust_scores'] = json.loads(profile_data['trust_scores'] or '{}')
            profile_data['metadata'] = json.loads(profile_data['metadata'] or '{}')
            
            profile = DeveloperProfile(**profile_data)

            # Cache the profile
            self.profile_cache[agent_id] = profile
            self.redis.setex(profile_key, 3600, profile.model_dump_json())

            return profile
    
    async def update_developer_profile(self, agent_id: str, updates: Dict) -> bool:
        """Update developer profile with new data."""
        profile = await self.get_developer_profile(agent_id)
        if not profile:
            return False

        # Apply updates
        for key, value in updates.items():
            if hasattr(profile, key):
                setattr(profile, key, value)

        profile.updated_at = datetime.utcnow()

        # Update in database
        async with self.db_manager.get_connection() as conn:
            await conn.execute("""
                UPDATE developer_profiles SET
                    specializations = $2, programming_languages = $3, frameworks = $4,
                    experience_level = $5, preferred_tasks = $6, availability_schedule = $7,
                    current_workload = $8, max_concurrent_tasks = $9, performance_metrics = $10,
                    collaboration_preferences = $11, trust_scores = $12, metadata = $13,
                    updated_at = $14
                WHERE agent_id = $1
            """,
                agent_id,
                json.dumps([s.value for s in profile.specializations]),
                json.dumps(profile.programming_languages),
                json.dumps(profile.frameworks),
                profile.experience_level.value,
                json.dumps([t.value for t in profile.preferred_tasks]),
                json.dumps(profile.availability_schedule),
                profile.current_workload,
                profile.max_concurrent_tasks,
                profile.performance_metrics.model_dump_json(),
                json.dumps(profile.collaboration_preferences),
                json.dumps(profile.trust_scores),
                json.dumps(profile.metadata),
                profile.updated_at,
            )
        
        # Update cache
        self.profile_cache[agent_id] = profile
        profile_key = f"developer_profile:{agent_id}"
        self.redis.setex(profile_key, 3600, profile.model_dump_json())

        logger.info(f"Updated developer profile for agent {agent_id}")
        return True

    async def update_performance_metrics(
        self,
        agent_id: str,
        task_completed: bool = True,
        completion_time: Optional[float] = None,
        quality_score: Optional[float] = None,
        peer_rating: Optional[float] = None,
    ) -> bool:
        """Update performance metrics for a developer."""
        profile = await self.get_developer_profile(agent_id)
        if not profile:
            return False

        metrics = profile.performance_metrics

        # Update task completion stats
        if task_completed:
            metrics.tasks_completed += 1
        else:
            metrics.tasks_failed += 1

        # Update completion time
        if completion_time:
            if metrics.average_completion_time:
                total_tasks = metrics.tasks_completed + metrics.tasks_failed
                metrics.average_completion_time = (
                    metrics.average_completion_time * (total_tasks - 1)
                    + completion_time
                ) / total_tasks
            else:
                metrics.average_completion_time = completion_time

        # Update quality score
        if quality_score:
            metrics.code_quality_score = (
                metrics.code_quality_score + quality_score
            ) / 2

        # Update peer ratings
        if peer_rating:
            metrics.peer_ratings.append(peer_rating)
            # Keep only last 10 ratings
            if len(metrics.peer_ratings) > 10:
                metrics.peer_ratings = metrics.peer_ratings[-10:]

        # Recalculate overall score
        metrics.overall_score = self._calculate_overall_score(metrics)
        metrics.last_updated = datetime.utcnow()

        # Update profile
        return await self.update_developer_profile(
            agent_id, {"performance_metrics": metrics}
        )

    def _calculate_overall_score(self, metrics: PerformanceMetrics) -> float:
        """Calculate overall performance score."""
        weights = {
            "completion_rate": 0.25,
            "quality": 0.25,
            "collaboration": 0.20,
            "communication": 0.15,
            "reliability": 0.15,
        }

        scores = {
            "completion_rate": metrics.completion_rate,
            "quality": metrics.code_quality_score,
            "collaboration": metrics.collaboration_score,
            "communication": metrics.communication_score,
            "reliability": metrics.reliability_score,
        }

        # Include peer ratings if available
        if metrics.peer_ratings:
            avg_peer_rating = sum(metrics.peer_ratings) / len(metrics.peer_ratings)
            scores["peer_feedback"] = avg_peer_rating
            weights["peer_feedback"] = 0.1
            # Adjust other weights
            for key in weights:
                if key != "peer_feedback":
                    weights[key] *= 0.9

        overall_score = sum(scores[key] * weights[key] for key in scores)
        return max(0.0, min(1.0, overall_score))

    async def find_best_agents_for_task(
        self,
        task_type: TaskType,
        required_skills: List[str],
        max_agents: int = 3,
        exclude_agents: List[str] = None,
    ) -> List[Tuple[str, float]]:
        """Find the best agents for a specific task based on capabilities and availability."""
        exclude_agents = exclude_agents or []

        # Build cache key
        skills_key = ",".join(sorted(required_skills)) if required_skills else "none"
        cache_key = f"best_agents:{task_type.value}:{skills_key}:{max_agents}:{','.join(sorted(exclude_agents))}"

        cached_result = self.cache_manager.get(cache_key)
        if cached_result is not None:
            return cached_result

        # Get all developer profiles
        async with self.db_manager.get_connection() as conn:
            rows = await conn.fetch("SELECT agent_id FROM developer_profiles")
            agent_ids = [row['agent_id'] for row in rows if row['agent_id'] not in exclude_agents]
        
        candidates = []
        for agent_id in agent_ids:
            profile = await self.get_developer_profile(agent_id)
            if not profile:
                continue

            # Check availability
            if not profile.is_available():
                continue

            # Calculate capability score
            capability_score = profile.get_capability_score(task_type, required_skills)

            # Factor in performance history
            performance_bonus = profile.performance_metrics.overall_score * 0.2
            total_score = capability_score + performance_bonus

            candidates.append((agent_id, total_score))

        # Sort by score and return top candidates
        candidates.sort(key=lambda x: x[1], reverse=True)
        top_candidates = candidates[:max_agents]
        # Cache result for 5 minutes
        self.cache_manager.set(cache_key, top_candidates, ttl=300)
        return top_candidates

    async def get_agent_workload(self, agent_id: str) -> Optional[DeveloperWorkload]:
        """Get current workload for an agent."""
        profile = await self.get_developer_profile(agent_id)
        if not profile:
            return None

        # Get current tasks from task assignments
        async with self.db_manager.get_connection() as conn:
            rows = await conn.fetch("""
                SELECT assignment_id, estimated_effort, actual_effort, deadline, status
                FROM task_assignments 
                WHERE assigned_agent = $1 AND status NOT IN ('completed', 'cancelled', 'failed')
            """,
                agent_id,
            )

            current_tasks = []
            total_estimated_hours = 0
            total_actual_hours = 0
            upcoming_deadlines = []

            for row in rows:
                current_tasks.append(row["assignment_id"])
                total_estimated_hours += row["estimated_effort"] or 0
                total_actual_hours += row["actual_effort"] or 0
                if row["deadline"]:
                    upcoming_deadlines.append((row["assignment_id"], row["deadline"]))

            # Calculate utilization
            max_hours = (
                profile.max_concurrent_tasks * 8
            )  # Assuming 8 hours per task slot
            utilization_percentage = (
                (total_estimated_hours / max_hours) * 100 if max_hours > 0 else 0
            )

            # Identify stress indicators
            stress_indicators = []
            if utilization_percentage > 90:
                stress_indicators.append("high_utilization")
            if len(upcoming_deadlines) > 3:
                stress_indicators.append("multiple_deadlines")
            if any(
                deadline[1] < datetime.utcnow() + timedelta(days=1)
                for deadline in upcoming_deadlines
            ):
                stress_indicators.append("urgent_deadlines")

            # Generate recommendations
            recommendations = []
            if utilization_percentage > 80:
                recommendations.append("Consider redistributing some tasks")
            if stress_indicators:
                recommendations.append("Monitor workload closely")

            return DeveloperWorkload(
                agent_id=agent_id,
                current_tasks=current_tasks,
                total_estimated_hours=total_estimated_hours,
                total_actual_hours=total_actual_hours,
                utilization_percentage=utilization_percentage,
                upcoming_deadlines=upcoming_deadlines,
                stress_indicators=stress_indicators,
                recommendations=recommendations,
            )
    
    async def get_collaboration_history(
        self, agent_1: str, agent_2: str, session_id: Optional[UUID] = None
    ) -> Optional[AgentCollaborationHistory]:
        """Get collaboration history between two agents."""
        async with self.db_manager.get_connection() as conn:
            query = """
                SELECT * FROM agent_collaboration_history 
                WHERE (agent_1 = $1 AND agent_2 = $2) OR (agent_1 = $2 AND agent_2 = $1)
            """
            params = [agent_1, agent_2]

            if session_id:
                query += " AND session_id = $3"
                params.append(str(session_id))

            query += " ORDER BY last_collaboration DESC LIMIT 1"

            row = await conn.fetchrow(query, *params)
            if not row:
                return None

            # Convert row to collaboration history
            history_data = dict(row)
            history_data["session_id"] = UUID(history_data["session_id"])
            history_data["collaboration_id"] = UUID(history_data["collaboration_id"])
            history_data["quality_ratings"] = json.loads(
                history_data["quality_ratings"] or "[]"
            )
            history_data["improvement_areas"] = json.loads(
                history_data["improvement_areas"] or "[]"
            )
            history_data["strengths"] = json.loads(history_data["strengths"] or "[]")
            history_data["metadata"] = json.loads(history_data["metadata"] or "{}")

            return AgentCollaborationHistory(**history_data)
    
    async def update_collaboration_history(
        self,
        session_id: UUID,
        agent_1: str,
        agent_2: str,
        collaboration_type: str,
        success: bool,
        quality_rating: Optional[float] = None,
        notes: Optional[str] = None,
    ) -> None:
        """Update collaboration history between two agents."""
        history = await self.get_collaboration_history(agent_1, agent_2, session_id)

        if not history:
            # Create new collaboration history
            history = AgentCollaborationHistory(
                session_id=session_id,
                agent_1=agent_1,
                agent_2=agent_2,
                collaboration_type=collaboration_type,
            )

        # Update history
        history.update_trust_score(success, quality_rating)
        if notes:
            history.collaboration_notes = notes

        # Store in database
        async with self.db_manager.get_connection() as conn:
            await conn.execute("""
                INSERT INTO agent_collaboration_history (
                    collaboration_id, session_id, agent_1, agent_2, collaboration_type,
                    interaction_count, successful_collaborations, conflict_count,
                    average_response_time, quality_ratings, communication_effectiveness,
                    task_completion_rate, mutual_trust_score, collaboration_notes,
                    improvement_areas, strengths, metadata, first_collaboration, last_collaboration
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19)
                ON CONFLICT (collaboration_id) DO UPDATE SET
                    interaction_count = EXCLUDED.interaction_count,
                    successful_collaborations = EXCLUDED.successful_collaborations,
                    conflict_count = EXCLUDED.conflict_count,
                    average_response_time = EXCLUDED.average_response_time,
                    quality_ratings = EXCLUDED.quality_ratings,
                    communication_effectiveness = EXCLUDED.communication_effectiveness,
                    task_completion_rate = EXCLUDED.task_completion_rate,
                    mutual_trust_score = EXCLUDED.mutual_trust_score,
                    collaboration_notes = EXCLUDED.collaboration_notes,
                    improvement_areas = EXCLUDED.improvement_areas,
                    strengths = EXCLUDED.strengths,
                    metadata = EXCLUDED.metadata,
                    last_collaboration = EXCLUDED.last_collaboration
            """,
                str(history.collaboration_id),
                str(history.session_id),
                history.agent_1,
                history.agent_2,
                history.collaboration_type,
                history.interaction_count,
                history.successful_collaborations,
                history.conflict_count,
                history.average_response_time,
                json.dumps(history.quality_ratings),
                history.communication_effectiveness,
                history.task_completion_rate,
                history.mutual_trust_score,
                history.collaboration_notes,
                json.dumps(history.improvement_areas),
                json.dumps(history.strengths),
                json.dumps(history.metadata),
                history.first_collaboration,
                history.last_collaboration,
            )
        
        logger.info(f"Updated collaboration history between {agent_1} and {agent_2}")

    async def get_team_compatibility_score(self, agent_ids: List[str]) -> float:
        """Calculate compatibility score for a team of agents."""
        if len(agent_ids) < 2:
            return 1.0

        total_pairs = 0
        compatibility_sum = 0.0

        for i, agent_1 in enumerate(agent_ids):
            for agent_2 in agent_ids[i + 1 :]:
                history = await self.get_collaboration_history(agent_1, agent_2)
                if history and history.mutual_trust_score:
                    compatibility_sum += history.mutual_trust_score
                else:
                    # Default compatibility for agents who haven't worked together
                    compatibility_sum += 0.7
                total_pairs += 1

        return compatibility_sum / total_pairs if total_pairs > 0 else 0.7

    async def get_available_agents(
        self,
        specialization: Optional[DeveloperSpecialization] = None,
        min_experience: Optional[ExperienceLevel] = None,
        required_skills: List[str] = None,
    ) -> List[DeveloperProfile]:
        """Get list of available agents matching criteria."""
        # Get all developer profiles
        async with self.db_manager.get_connection() as conn:
            rows = await conn.fetch("SELECT agent_id FROM developer_profiles")
            agent_ids = [row['agent_id'] for row in rows]
        
        available_agents = []
        required_skills = required_skills or []

        for agent_id in agent_ids:
            profile = await self.get_developer_profile(agent_id)
            if not profile or not profile.is_available():
                continue

            # Check specialization
            if specialization and specialization not in profile.specializations:
                continue

            # Check experience level
            if min_experience:
                experience_levels = list(ExperienceLevel)
                if experience_levels.index(
                    profile.experience_level
                ) < experience_levels.index(min_experience):
                    continue

            # Check required skills
            if required_skills:
                agent_skills = set(profile.programming_languages + profile.frameworks)
                if not set(required_skills).issubset(agent_skills):
                    continue

            available_agents.append(profile)

        return available_agents
