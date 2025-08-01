"""Integration tests for Multi-Developer Coordination API endpoints."""

import asyncio
import json
import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from unittest.mock import Mock, AsyncMock, patch

from fastapi.testclient import TestClient
from src.collaboration_orchestrator.app import app
from src.collaboration_orchestrator.multi_developer_models import (
    DeveloperSpecialization,
    ExperienceLevel,
    TaskType,
    TaskStatus,
    ResolutionStrategy,
)


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)





class TestDeveloperProfileEndpoints:
    """Test developer profile management endpoints."""
    
    @pytest.mark.asyncio
    async def test_create_developer_profile(self, client):
        """Test creating a developer profile via API."""
        mock_profile = {
            "agent_id": "test_agent",
            "agent_type": "developer",
            "specializations": ["backend"],
            "programming_languages": ["Python", "Go"],
            "frameworks": ["FastAPI", "Django"],
            "experience_level": "senior",
            "preferred_tasks": ["feature_development"],
            "max_concurrent_tasks": 3,
            "metadata": {},
            "current_workload": 0,
            "performance_metrics": {
                "tasks_completed": 0,
                "tasks_failed": 0,
                "overall_score": 0.8
            },
            "collaboration_preferences": {},
            "trust_scores": {},
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        with patch('src.collaboration_orchestrator.multi_developer_orchestrator.DeveloperProfileManager.create', new_callable=AsyncMock) as mock_create_manager:
            mock_manager_instance = AsyncMock()
            mock_create_manager.return_value = mock_manager_instance
            mock_manager_instance.create_developer_profile.return_value = mock_profile

            response = client.post("/multi-dev/profiles", json={
                "agent_id": "test_agent",
                "agent_type": "developer",
                "specializations": ["backend"],
                "programming_languages": ["Python", "Go"],
                "frameworks": ["FastAPI", "Django"],
                "experience_level": "senior",
                "preferred_tasks": ["feature_development"],
                "max_concurrent_tasks": 3
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["agent_id"] == "test_agent"
            assert data["experience_level"] == "senior"
            assert "backend" in data["specializations"]

    @pytest.mark.asyncio
    async def test_get_developer_profile(self, client):
        """Test retrieving a developer profile."""
        mock_profile = {
            "agent_id": "test_agent",
            "agent_type": "developer",
            "specializations": ["backend"],
            "programming_languages": ["Python"],
            "experience_level": "senior",
            "current_workload": 10,
            "max_concurrent_tasks": 3
        }
        
        with patch('src.collaboration_orchestrator.multi_developer_orchestrator.DeveloperProfileManager.create', new_callable=AsyncMock) as mock_create_manager:
            mock_manager_instance = AsyncMock()
            mock_create_manager.return_value = mock_manager_instance
            mock_manager_instance.get_developer_profile.return_value = mock_profile

            response = client.get("/multi-dev/profiles/test_agent")
            
            assert response.status_code == 200
            data = response.json()
            assert data["agent_id"] == "test_agent"
            assert data["current_workload"] == 10

    @pytest.mark.asyncio
    async def test_get_developer_profile_not_found(self, client):
        """Test retrieving a non-existent developer profile."""
        with patch('src.collaboration_orchestrator.multi_developer_orchestrator.DeveloperProfileManager.create', new_callable=AsyncMock) as mock_create_manager:
            mock_manager_instance = AsyncMock()
            mock_create_manager.return_value = mock_manager_instance
            mock_manager_instance.get_developer_profile.return_value = None

            response = client.get("/multi-dev/profiles/nonexistent")
            
            assert response.status_code == 404
            assert "not found" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_update_developer_profile(self, client):
        """Test updating a developer profile."""
        with patch('src.collaboration_orchestrator.multi_developer_orchestrator.DeveloperProfileManager.create', new_callable=AsyncMock) as mock_create_manager:
            mock_manager_instance = AsyncMock()
            mock_create_manager.return_value = mock_manager_instance
            mock_manager_instance.update_developer_profile.return_value = True

            response = client.put("/multi-dev/profiles/test_agent", json={
                "experience_level": "lead",
                "max_concurrent_tasks": 4
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "updated"
            assert data["agent_id"] == "test_agent"

    @pytest.mark.asyncio
    async def test_get_available_agents(self, client):
        """Test getting available agents with filters."""
        mock_agents = [
            {
                "agent_id": "backend_dev",
                "specializations": ["backend"],
                "programming_languages": ["Python"],
                "experience_level": "senior",
                "current_workload": 5
            },
            {
                "agent_id": "frontend_dev",
                "specializations": ["frontend"],
                "programming_languages": ["JavaScript"],
                "experience_level": "intermediate",
                "current_workload": 8
            }
        ]
        
        with patch('src.collaboration_orchestrator.multi_developer_orchestrator.DeveloperProfileManager.create', new_callable=AsyncMock) as mock_create_manager:
            mock_manager_instance = AsyncMock()
            mock_create_manager.return_value = mock_manager_instance
            mock_manager_instance.get_available_agents.return_value = mock_agents

            response = client.get("/multi-dev/profiles/available?specialization=backend&required_skills=Python")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
            assert data[0]["agent_id"] == "backend_dev"

    @pytest.mark.asyncio
    async def test_find_best_agents_for_task(self, client):
        """Test finding best agents for a specific task."""
        mock_candidates = [
            {"agent_id": "senior_dev", "score": 0.9},
            {"agent_id": "junior_dev", "score": 0.6}
        ]
        
        with patch('src.collaboration_orchestrator.multi_developer_orchestrator.DeveloperProfileManager.create', new_callable=AsyncMock) as mock_create_manager:
            mock_manager_instance = AsyncMock()
            mock_create_manager.return_value = mock_manager_instance
            mock_manager_instance.find_best_agents_for_task.return_value = [("senior_dev", 0.9), ("junior_dev", 0.6)]

            response = client.get(
                "/multi-dev/profiles/find-for-task"
                "?task_type=feature_development&required_skills=Python&required_skills=FastAPI&max_agents=2"
            )
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
            assert data[0]["agent_id"] == "senior_dev"
            assert data[0]["score"] == 0.9
            assert data[1]["score"] == 0.6


class TestTeamCoordinationPlanEndpoints:
    """Test team coordination plan endpoints."""
    
    @pytest.mark.asyncio
    async def test_create_team_coordination_plan(self, client):
        """Test creating a team coordination plan."""
        session_id = str(uuid4())
        plan_id = str(uuid4())
        
        mock_plan = {
            "plan_id": plan_id,
            "session_id": session_id,
            "project_name": "E-commerce Platform",
            "project_description": "Modern e-commerce solution",
            "team_lead": "senior_dev",
            "team_members": ["senior_dev", "frontend_dev", "qa_specialist"],
            "task_assignments": {},
            "status": "draft",
            "priority": "high",
            "conflict_resolution_strategy": "consensus",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        with patch('src.collaboration_orchestrator.multi_developer_orchestrator.MultiDeveloperOrchestrator.create', new_callable=AsyncMock) as mock_create_orchestrator:
            mock_orchestrator_instance = AsyncMock()
            mock_create_orchestrator.return_value = mock_orchestrator_instance
            mock_orchestrator_instance.create_team_coordination_plan.return_value = mock_plan

            response = client.post("/multi-dev/plans", json={
                "session_id": session_id,
                "project_name": "E-commerce Platform",
                "project_description": "Modern e-commerce solution",
                "team_lead": "senior_dev",
                "team_members": ["senior_dev", "frontend_dev", "qa_specialist"],
                "tasks": [
                    {
                        "name": "User Authentication",
                        "description": "Implement OAuth2",
                        "type": "feature_development",
                        "estimated_effort": 8,
                        "priority": "high"
                    }
                ],
                "conflict_resolution_strategy": "consensus"
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["project_name"] == "E-commerce Platform"
            assert data["team_lead"] == "senior_dev"
            assert len(data["team_members"]) == 3
    
    @pytest.mark.asyncio
    async def test_get_coordination_plan(self, client):
        """Test retrieving a coordination plan."""
        plan_id = str(uuid4())
        mock_plan = {
            "plan_id": plan_id,
            "project_name": "Test Project",
            "team_lead": "lead_001",
            "team_members": ["lead_001", "dev_001"],
            "task_assignments": {},
            "status": "active"
        }
        
        with patch('src.collaboration_orchestrator.multi_developer_orchestrator.MultiDeveloperOrchestrator.create', new_callable=AsyncMock) as mock_create_orchestrator:
            mock_orchestrator_instance = AsyncMock()
            mock_create_orchestrator.return_value = mock_orchestrator_instance
            mock_orchestrator_instance.get_coordination_plan.return_value = mock_plan

            response = client.get(f"/multi-dev/plans/{plan_id}")
            
            assert response.status_code == 200
            data = response.json()
            assert data["plan_id"] == plan_id
            assert data["project_name"] == "Test Project"
    
    @pytest.mark.asyncio
    async def test_get_team_performance_report(self, client):
        """Test generating team performance report."""
        plan_id = str(uuid4())
        mock_report = {
            "plan_id": plan_id,
            "project_name": "Test Project",
            "overall_progress": 75.0,
            "task_summary": {
                "total": 4,
                "completed": 3,
                "in_progress": 1,
                "blocked": 0
            },
            "workload_distribution": {
                "dev_001": 16,
                "dev_002": 12
            },
            "agent_performance": {
                "dev_001": {
                    "total_tasks": 2,
                    "completed_tasks": 2,
                    "completion_rate": 1.0
                }
            },
            "optimization_suggestions": [],
            "generated_at": datetime.utcnow().isoformat()
        }
        
        with patch('src.collaboration_orchestrator.multi_developer_orchestrator.MultiDeveloperOrchestrator.create', new_callable=AsyncMock) as mock_create_orchestrator:
            mock_orchestrator_instance = AsyncMock()
            mock_create_orchestrator.return_value = mock_orchestrator_instance
            mock_orchestrator_instance.generate_team_performance_report.return_value = mock_report

            response = client.get(f"/multi-dev/plans/{plan_id}/performance-report")
            
            assert response.status_code == 200
            data = response.json()
            assert data["plan_id"] == plan_id
            assert data["overall_progress"] == 75.0
            assert data["task_summary"]["completed"] == 3
    
    @pytest.mark.asyncio
    async def test_optimize_task_assignments(self, client):
        """Test task assignment optimization."""
        plan_id = str(uuid4())
        
        mock_plan = {
            "plan_id": plan_id,
            "team_members": ["dev_001", "dev_002"],
            "task_assignments": {}
        }
        
        mock_suggestions = [
            {
                "suggestion_type": "reassignment",
                "current_assignment": "task_001",
                "expected_improvement": {"efficiency": 0.2},
                "rationale": "Better skill match available",
                "confidence_score": 0.8
            }
        ]
        
        with patch('src.collaboration_orchestrator.multi_developer_orchestrator.MultiDeveloperOrchestrator.create', new_callable=AsyncMock) as mock_create_orchestrator,
             patch('src.collaboration_orchestrator.multi_developer_orchestrator.DeveloperProfileManager.create', new_callable=AsyncMock) as mock_create_profile_manager:
            mock_orchestrator_instance = AsyncMock()
            mock_create_orchestrator.return_value = mock_orchestrator_instance
            mock_orchestrator_instance.get_coordination_plan.return_value = mock_plan
            
            mock_profile_manager_instance = AsyncMock()
            mock_create_profile_manager.return_value = mock_profile_manager_instance
            mock_profile_manager_instance.get_developer_profile.return_value = {}

            mock_orchestrator_instance.assignment_engine = AsyncMock()
            mock_orchestrator_instance.assignment_engine.suggest_task_optimizations.return_value = [Mock(model_dump=Mock(return_value=s)) for s in mock_suggestions]
            
            response = client.post(f"/multi-dev/plans/{plan_id}/optimize")
            
            assert response.status_code == 200
            data = response.json()
            assert data["plan_id"] == plan_id
            assert len(data["optimization_suggestions"]) == 1
            assert data["optimization_suggestions"][0]["suggestion_type"] == "reassignment"


class TestTaskAssignmentEndpoints:
    """Test task assignment endpoints."""
    
    @pytest.mark.asyncio
    async def test_assign_task_to_agent(self, client):
        """Test assigning a task to an agent."""
        plan_id = str(uuid4())
        assignment_id = str(uuid4())
        
        with patch('src.collaboration_orchestrator.multi_developer_orchestrator.MultiDeveloperOrchestrator.create', new_callable=AsyncMock) as mock_create_orchestrator:
            mock_orchestrator_instance = AsyncMock()
            mock_create_orchestrator.return_value = mock_orchestrator_instance
            mock_orchestrator_instance.assign_task_to_agent.return_value = True

            response = client.post(
                f"/multi-dev/plans/{plan_id}/tasks/{assignment_id}/assign"
                f"?agent_id=dev_001&reviewer_agents=senior_dev"
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "assigned"
            assert data["agent_id"] == "dev_001"
    
    @pytest.mark.asyncio
    async def test_update_task_progress(self, client):
        """Test updating task progress."""
        assignment_id = str(uuid4())
        
        with patch('src.collaboration_orchestrator.multi_developer_orchestrator.MultiDeveloperOrchestrator.create', new_callable=AsyncMock) as mock_create_orchestrator:
            mock_orchestrator_instance = AsyncMock()
            mock_create_orchestrator.return_value = mock_orchestrator_instance
            mock_orchestrator_instance.handle_task_progress_update.return_value = True

            response = client.put(f"/multi-dev/tasks/{assignment_id}/progress?agent_id=dev_001", json={
                "progress_percentage": 75,
                "status": "in_progress",
                "blockers": ["Waiting for API documentation"],
                "feedback": {"quality": "good", "notes": "Making good progress"}
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "updated"
            assert data["progress"] == 75


class TestConflictResolutionEndpoints:
    """Test conflict resolution endpoints."""
    
    @pytest.mark.asyncio
    async def test_detect_conflict(self, client):
        """Test conflict detection."""
        plan_id = str(uuid4())
        conflict_id = str(uuid4())
        
        mock_plan = {"session_id": str(uuid4())}
        mock_conflict = {
            "conflict_id": conflict_id,
            "conflict_type": "merge_conflict",
            "conflict_description": "Git merge conflict in main.py",
            "involved_agents": ["dev_001", "dev_002"],
            "conflict_severity": "medium",
            "status": "open",
            "created_at": datetime.utcnow().isoformat()
        }
        
        with patch('src.collaboration_orchestrator.multi_developer_orchestrator.MultiDeveloperOrchestrator.create', new_callable=AsyncMock) as mock_create_orchestrator,
             patch('src.collaboration_orchestrator.intelligent_conflict_resolver.IntelligentConflictResolver.create', new_callable=AsyncMock) as mock_create_conflict_resolver:
            mock_orchestrator_instance = AsyncMock()
            mock_create_orchestrator.return_value = mock_orchestrator_instance
            mock_orchestrator_instance.get_coordination_plan.return_value = mock_plan

            mock_conflict_resolver_instance = AsyncMock()
            mock_create_conflict_resolver.return_value = mock_conflict_resolver_instance
            mock_conflict_resolver_instance.detect_conflict.return_value = mock_conflict

            response = client.post(f"/multi-dev/plans/{plan_id}/conflicts/detect", json={
                "conflict_description": "Git merge conflict in main.py",
                "involved_agents": ["dev_001", "dev_002"],
                "context": {"conflict_files": ["main.py"]},
                "detected_by": "system"
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["conflict_type"] == "merge_conflict"
            assert len(data["involved_agents"]) == 2
    
    @pytest.mark.asyncio
    async def test_resolve_conflict(self, client):
        """Test conflict resolution."""
        conflict_id = str(uuid4())
        
        with patch('src.collaboration_orchestrator.intelligent_conflict_resolver.IntelligentConflictResolver.create', new_callable=AsyncMock) as mock_create_conflict_resolver:
            mock_conflict_resolver_instance = AsyncMock()
            mock_create_conflict_resolver.return_value = mock_conflict_resolver_instance
            mock_conflict_resolver_instance.resolve_conflict.return_value = True

            response = client.post(f"/multi-dev/conflicts/{conflict_id}/resolve")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "resolved"
            assert data["conflict_id"] == conflict_id
    
    @pytest.mark.asyncio
    async def test_get_conflict_statistics(self, client):
        """Test retrieving conflict statistics."""
        mock_stats = {
            "total_conflicts": 15,
            "resolved_conflicts": 12,
            "open_conflicts": 3,
            "by_type": {
                "merge_conflict": 8,
                "design_conflict": 4,
                "resource_conflict": 3
            },
            "by_severity": {
                "low": 6,
                "medium": 7,
                "high": 2
            },
            "average_resolution_time_hours": 2.5,
            "resolution_success_rate": 0.8
        }
        
        with patch('src.collaboration_orchestrator.intelligent_conflict_resolver.IntelligentConflictResolver.create', new_callable=AsyncMock) as mock_create_conflict_resolver:
            mock_conflict_resolver_instance = AsyncMock()
            mock_create_conflict_resolver.return_value = mock_conflict_resolver_instance
            mock_conflict_resolver_instance.get_conflict_statistics.return_value = mock_stats

            response = client.get("/multi-dev/conflicts/statistics")
            
            assert response.status_code == 200
            data = response.json()
            assert data["total_conflicts"] == 15
            assert data["resolution_success_rate"] == 0.8
            assert "merge_conflict" in data["by_type"]
    
    @pytest.mark.asyncio
    async def test_auto_detect_conflicts(self, client):
        """Test automatic conflict detection."""
        plan_id = str(uuid4())
        
        mock_conflicts = [
            {
                "conflict_id": str(uuid4()),
                "type": "resource_conflict",
                "description": "Database connection conflict",
                "resolved": False,
                "strategy": "consensus"
            }
        ]
        
        with patch('src.collaboration_orchestrator.multi_developer_orchestrator.MultiDeveloperOrchestrator.create', new_callable=AsyncMock) as mock_create_orchestrator:
            mock_orchestrator_instance = AsyncMock()
            mock_create_orchestrator.return_value = mock_orchestrator_instance
            mock_orchestrator_instance.detect_and_resolve_conflicts.return_value = mock_conflicts

            response = client.post(f"/multi-dev/plans/{plan_id}/conflicts/auto-detect")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["type"] == "resource_conflict"


class TestAnalyticsEndpoints:
    """Test analytics and reporting endpoints."""
    
    @pytest.mark.asyncio
    async def test_calculate_team_compatibility(self, client):
        """Test team compatibility calculation."""
        with patch('src.collaboration_orchestrator.developer_profile_manager.DeveloperProfileManager.create', new_callable=AsyncMock) as mock_create_manager:
            mock_manager_instance = AsyncMock()
            mock_create_manager.return_value = mock_manager_instance
            mock_manager_instance.get_team_compatibility_score.return_value = 0.85

            response = client.get("/multi-dev/analytics/team-compatibility?agent_ids=dev_001&agent_ids=dev_002&agent_ids=dev_003")
            
            assert response.status_code == 200
            data = response.json()
            assert data["compatibility_score"] == 0.85
            assert data["recommendation"] == "high"
            assert len(data["team_agents"]) == 3
    
    @pytest.mark.asyncio
    async def test_get_collaboration_history(self, client):
        """Test retrieving collaboration history between agents."""
        mock_history = {
            "agent_1": "dev_001",
            "agent_2": "dev_002",
            "interaction_count": 15,
            "successful_collaborations": 13,
            "mutual_trust_score": 0.87,
            "collaboration_notes": "Great communication and code quality"
        }
        
        with patch('src.collaboration_orchestrator.developer_profile_manager.DeveloperProfileManager.create', new_callable=AsyncMock) as mock_create_manager:
            mock_manager_instance = AsyncMock()
            mock_create_manager.return_value = mock_manager_instance
            mock_manager_instance.get_collaboration_history.return_value = mock_history

            response = client.get("/multi-dev/analytics/agent-collaboration/dev_001/dev_002")
            
            assert response.status_code == 200
            data = response.json()
            assert data["mutual_trust_score"] == 0.87
            assert data["interaction_count"] == 15
    
    @pytest.mark.asyncio
    async def test_get_workload_distribution(self, client):
        """Test workload distribution analysis."""
        def mock_get_workload(agent_id):
            workloads = {
                "dev_001": {
                    "current_tasks": ["task_1", "task_2"],
                    "total_estimated_hours": 20,
                    "utilization_percentage": 85,
                    "stress_indicators": ["high_utilization"],
                    "recommendations": ["Consider redistributing tasks"]
                },
                "dev_002": {
                    "current_tasks": ["task_3"],
                    "total_estimated_hours": 8,
                    "utilization_percentage": 35,
                    "stress_indicators": [],
                    "recommendations": []
                }
            }
            return Mock(**workloads.get(agent_id, {}))
        
        with patch('src.collaboration_orchestrator.developer_profile_manager.DeveloperProfileManager.create', new_callable=AsyncMock) as mock_create_manager:
            mock_manager_instance = AsyncMock()
            mock_create_manager.return_value = mock_manager_instance
            mock_manager_instance.get_agent_workload.side_effect = mock_get_workload

            response = client.get("/multi-dev/analytics/workload-distribution?agent_ids=dev_001&agent_ids=dev_002")
            
            assert response.status_code == 200
            data = response.json()
            assert data["total_workload_hours"] == 28
            assert data["average_utilization"] == 60.0  # (85 + 35) / 2
            assert "dev_001" in data["agents"]
            assert "dev_002" in data["agents"]


class TestSystemHealthEndpoints:
    """Test system health and monitoring endpoints."""
    
    @pytest.mark.asyncio
    async def test_get_system_health(self, client):
        """Test system health check."""
        with patch('src.collaboration_orchestrator.multi_developer_orchestrator.MultiDeveloperOrchestrator.create', new_callable=AsyncMock) as mock_create_orchestrator,
             patch('src.collaboration_orchestrator.intelligent_conflict_resolver.IntelligentConflictResolver.create', new_callable=AsyncMock) as mock_create_conflict_resolver:
            mock_orchestrator_instance = AsyncMock()
            mock_create_orchestrator.return_value = mock_orchestrator_instance
            mock_orchestrator_instance.active_plans = {}
            mock_orchestrator_instance._get_db_connection = AsyncMock(return_value=AsyncMock(close=AsyncMock()))
            mock_orchestrator_instance.redis = AsyncMock()
            mock_orchestrator_instance.redis.ping.return_value = True

            mock_conflict_resolver_instance = AsyncMock()
            mock_create_conflict_resolver.return_value = mock_conflict_resolver_instance
            mock_conflict_resolver_instance.active_conflicts = {}
            
            response = client.get("/multi-dev/system/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["components"]["database"] == "healthy"
            assert data["components"]["redis"] == "healthy"
            assert "timestamp" in data
    
    @pytest.mark.asyncio
    async def test_get_system_metrics(self, client):
        """Test system metrics retrieval."""
        with patch('src.collaboration_orchestrator.multi_developer_orchestrator.MultiDeveloperOrchestrator.create', new_callable=AsyncMock) as mock_create_orchestrator,
             patch('src.collaboration_orchestrator.intelligent_conflict_resolver.IntelligentConflictResolver.create', new_callable=AsyncMock) as mock_create_conflict_resolver:
            mock_orchestrator_instance = AsyncMock()
            mock_create_orchestrator.return_value = mock_orchestrator_instance
            mock_orchestrator_instance.active_plans = {"plan_1": {}, "plan_2": {}}

            mock_conflict_resolver_instance = AsyncMock()
            mock_create_conflict_resolver.return_value = mock_conflict_resolver_instance
            mock_conflict_resolver_instance.active_conflicts = {"conflict_1": {}}
            
            response = client.get("/multi-dev/system/metrics")
            
            assert response.status_code == 200
            data = response.json()
            assert data["coordination_plans"]["total"] == 2
            assert data["conflicts"]["total_detected"] == 1
            assert "timestamp" in data


class TestErrorHandling:
    """Test error handling in API endpoints."""
    
    def test_invalid_uuid_format(self, client):
        """Test handling of invalid UUID formats."""
        response = client.get("/multi-dev/plans/invalid-uuid")
        assert response.status_code == 422  # Validation error
    
    def test_missing_required_fields(self, client):
        """Test handling of missing required fields."""
        response = client.post("/multi-dev/profiles", json={
            "agent_type": "developer"
            # Missing required agent_id field
        })
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_internal_server_error_handling(self, client):
        """Test handling of internal server errors."""
        with patch('src.collaboration_orchestrator.multi_developer_orchestrator.DeveloperProfileManager.create', new_callable=AsyncMock) as mock_create_manager:
            mock_manager_instance = AsyncMock()
            mock_create_manager.return_value = mock_manager_instance
            mock_manager_instance.get_developer_profile.side_effect = Exception("Database error")

            response = client.get("/multi-dev/profiles/test_agent")
            assert response.status_code == 500
            assert "Failed to" in response.json()["detail"]


@pytest.mark.asyncio
class TestAsyncEndpoints:
    """Test async functionality in endpoints."""
    
    async def test_concurrent_profile_creation(self):
        """Test handling of concurrent profile creation requests."""
        client = TestClient(app)
        
        with patch('src.collaboration_orchestrator.developer_profile_manager.DeveloperProfileManager.create', new_callable=AsyncMock) as mock_create_manager:
            mock_manager_instance = AsyncMock()
            mock_create_manager.return_value = mock_manager_instance
            mock_manager_instance.create_developer_profile.return_value = {
                "agent_id": "concurrent_test",
                "agent_type": "developer",
                "created_at": datetime.utcnow().isoformat()
            }
            
            # Simulate concurrent requests
            tasks = []
            for i in range(5):
                tasks.append(
                    client.post("/multi-dev/profiles", json={
                        "agent_id": f"concurrent_test_{i}",
                        "agent_type": "developer"
                    })
                )
            
            # All requests should succeed
            for response in tasks:
                assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])