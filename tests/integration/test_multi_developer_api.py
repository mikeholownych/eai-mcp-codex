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


@pytest.fixture
def mock_orchestrator():
    """Mock the global orchestrator instance."""
    with patch('src.collaboration_orchestrator.multi_developer_routes.orchestrator') as mock:
        yield mock


@pytest.fixture
def mock_profile_manager():
    """Mock the global profile manager instance."""
    with patch('src.collaboration_orchestrator.multi_developer_routes.profile_manager') as mock:
        yield mock


@pytest.fixture
def mock_conflict_resolver():
    """Mock the global conflict resolver instance."""
    with patch('src.collaboration_orchestrator.multi_developer_routes.conflict_resolver') as mock:
        yield mock


class TestDeveloperProfileEndpoints:
    """Test developer profile management endpoints."""
    
    def test_create_developer_profile(self, client, mock_profile_manager):
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
        
        mock_profile_manager.create_developer_profile = AsyncMock(return_value=mock_profile)
        
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
    
    def test_get_developer_profile(self, client, mock_profile_manager):
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
        
        mock_profile_manager.get_developer_profile = AsyncMock(return_value=mock_profile)
        
        response = client.get("/multi-dev/profiles/test_agent")
        
        assert response.status_code == 200
        data = response.json()
        assert data["agent_id"] == "test_agent"
        assert data["current_workload"] == 10
    
    def test_get_developer_profile_not_found(self, client, mock_profile_manager):
        """Test retrieving a non-existent developer profile."""
        mock_profile_manager.get_developer_profile = AsyncMock(return_value=None)
        
        response = client.get("/multi-dev/profiles/nonexistent")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_update_developer_profile(self, client, mock_profile_manager):
        """Test updating a developer profile."""
        mock_profile_manager.update_developer_profile = AsyncMock(return_value=True)
        
        response = client.put("/multi-dev/profiles/test_agent", json={
            "experience_level": "lead",
            "max_concurrent_tasks": 4
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "updated"
        assert data["agent_id"] == "test_agent"
    
    def test_get_available_agents(self, client, mock_profile_manager):
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
        
        mock_profile_manager.get_available_agents = AsyncMock(return_value=mock_agents)
        
        response = client.get("/multi-dev/profiles/available?specialization=backend&required_skills=Python")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["agent_id"] == "backend_dev"
    
    def test_find_best_agents_for_task(self, client, mock_profile_manager):
        """Test finding best agents for a specific task."""
        mock_candidates = [
            {"agent_id": "senior_dev", "score": 0.9},
            {"agent_id": "junior_dev", "score": 0.6}
        ]
        
        mock_profile_manager.find_best_agents_for_task = AsyncMock(
            return_value=[("senior_dev", 0.9), ("junior_dev", 0.6)]
        )
        
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
    
    def test_create_team_coordination_plan(self, client, mock_orchestrator):
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
        
        mock_orchestrator.create_team_coordination_plan = AsyncMock(return_value=mock_plan)
        
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
    
    def test_get_coordination_plan(self, client, mock_orchestrator):
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
        
        mock_orchestrator.get_coordination_plan = AsyncMock(return_value=mock_plan)
        
        response = client.get(f"/multi-dev/plans/{plan_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["plan_id"] == plan_id
        assert data["project_name"] == "Test Project"
    
    def test_get_team_performance_report(self, client, mock_orchestrator):
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
        
        mock_orchestrator.generate_team_performance_report = AsyncMock(return_value=mock_report)
        
        response = client.get(f"/multi-dev/plans/{plan_id}/performance-report")
        
        assert response.status_code == 200
        data = response.json()
        assert data["plan_id"] == plan_id
        assert data["overall_progress"] == 75.0
        assert data["task_summary"]["completed"] == 3
    
    def test_optimize_task_assignments(self, client, mock_orchestrator, mock_profile_manager):
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
        
        mock_orchestrator.get_coordination_plan = AsyncMock(return_value=mock_plan)
        mock_profile_manager.get_developer_profile = AsyncMock(return_value={})
        
        with patch('src.collaboration_orchestrator.multi_developer_routes.orchestrator.assignment_engine') as mock_engine:
            mock_engine.suggest_task_optimizations.return_value = [Mock(model_dump=Mock(return_value=s)) for s in mock_suggestions]
            
            response = client.post(f"/multi-dev/plans/{plan_id}/optimize")
            
            assert response.status_code == 200
            data = response.json()
            assert data["plan_id"] == plan_id
            assert len(data["optimization_suggestions"]) == 1
            assert data["optimization_suggestions"][0]["suggestion_type"] == "reassignment"


class TestTaskAssignmentEndpoints:
    """Test task assignment endpoints."""
    
    def test_assign_task_to_agent(self, client, mock_orchestrator):
        """Test assigning a task to an agent."""
        plan_id = str(uuid4())
        assignment_id = str(uuid4())
        
        mock_orchestrator.assign_task_to_agent = AsyncMock(return_value=True)
        
        response = client.post(
            f"/multi-dev/plans/{plan_id}/tasks/{assignment_id}/assign"
            f"?agent_id=dev_001&reviewer_agents=senior_dev"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "assigned"
        assert data["agent_id"] == "dev_001"
    
    def test_update_task_progress(self, client, mock_orchestrator):
        """Test updating task progress."""
        assignment_id = str(uuid4())
        
        mock_orchestrator.handle_task_progress_update = AsyncMock(return_value=True)
        
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
    
    def test_detect_conflict(self, client, mock_orchestrator, mock_conflict_resolver):
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
        
        mock_orchestrator.get_coordination_plan = AsyncMock(return_value=mock_plan)
        mock_conflict_resolver.detect_conflict = AsyncMock(return_value=mock_conflict)
        
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
    
    def test_resolve_conflict(self, client, mock_conflict_resolver):
        """Test conflict resolution."""
        conflict_id = str(uuid4())
        
        mock_conflict_resolver.resolve_conflict = AsyncMock(return_value=True)
        
        response = client.post(f"/multi-dev/conflicts/{conflict_id}/resolve")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "resolved"
        assert data["conflict_id"] == conflict_id
    
    def test_get_conflict_statistics(self, client, mock_conflict_resolver):
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
        
        mock_conflict_resolver.get_conflict_statistics = AsyncMock(return_value=mock_stats)
        
        response = client.get("/multi-dev/conflicts/statistics")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_conflicts"] == 15
        assert data["resolution_success_rate"] == 0.8
        assert "merge_conflict" in data["by_type"]
    
    def test_auto_detect_conflicts(self, client, mock_orchestrator):
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
        
        mock_orchestrator.detect_and_resolve_conflicts = AsyncMock(return_value=mock_conflicts)
        
        response = client.post(f"/multi-dev/plans/{plan_id}/conflicts/auto-detect")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["type"] == "resource_conflict"


class TestAnalyticsEndpoints:
    """Test analytics and reporting endpoints."""
    
    def test_calculate_team_compatibility(self, client, mock_profile_manager):
        """Test team compatibility calculation."""
        mock_profile_manager.get_team_compatibility_score = AsyncMock(return_value=0.85)
        
        response = client.get("/multi-dev/analytics/team-compatibility?agent_ids=dev_001&agent_ids=dev_002&agent_ids=dev_003")
        
        assert response.status_code == 200
        data = response.json()
        assert data["compatibility_score"] == 0.85
        assert data["recommendation"] == "high"
        assert len(data["team_agents"]) == 3
    
    def test_get_collaboration_history(self, client, mock_profile_manager):
        """Test retrieving collaboration history between agents."""
        mock_history = {
            "agent_1": "dev_001",
            "agent_2": "dev_002",
            "interaction_count": 15,
            "successful_collaborations": 13,
            "mutual_trust_score": 0.87,
            "collaboration_notes": "Great communication and code quality"
        }
        
        mock_profile_manager.get_collaboration_history = AsyncMock(return_value=mock_history)
        
        response = client.get("/multi-dev/analytics/agent-collaboration/dev_001/dev_002")
        
        assert response.status_code == 200
        data = response.json()
        assert data["mutual_trust_score"] == 0.87
        assert data["interaction_count"] == 15
    
    def test_get_workload_distribution(self, client, mock_profile_manager):
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
        
        mock_profile_manager.get_agent_workload = AsyncMock(side_effect=mock_get_workload)
        
        response = client.get("/multi-dev/analytics/workload-distribution?agent_ids=dev_001&agent_ids=dev_002")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_workload_hours"] == 28
        assert data["average_utilization"] == 60.0  # (85 + 35) / 2
        assert "dev_001" in data["agents"]
        assert "dev_002" in data["agents"]


class TestSystemHealthEndpoints:
    """Test system health and monitoring endpoints."""
    
    def test_get_system_health(self, client, mock_orchestrator):
        """Test system health check."""
        mock_orchestrator.active_plans = {}
        mock_orchestrator._get_db_connection = AsyncMock(return_value=AsyncMock())
        mock_orchestrator.redis.ping = Mock()
        
        with patch('src.collaboration_orchestrator.multi_developer_routes.conflict_resolver') as mock_resolver:
            mock_resolver.active_conflicts = {}
            
            response = client.get("/multi-dev/system/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["components"]["database"] == "healthy"
            assert data["components"]["redis"] == "healthy"
            assert "timestamp" in data
    
    def test_get_system_metrics(self, client, mock_orchestrator):
        """Test system metrics retrieval."""
        mock_orchestrator.active_plans = {"plan_1": {}, "plan_2": {}}
        
        with patch('src.collaboration_orchestrator.multi_developer_routes.conflict_resolver') as mock_resolver:
            mock_resolver.active_conflicts = {"conflict_1": {}}
            
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
    
    def test_internal_server_error_handling(self, client, mock_profile_manager):
        """Test handling of internal server errors."""
        mock_profile_manager.get_developer_profile = AsyncMock(side_effect=Exception("Database error"))
        
        response = client.get("/multi-dev/profiles/test_agent")
        assert response.status_code == 500
        assert "Failed to" in response.json()["detail"]


@pytest.mark.asyncio
class TestAsyncEndpoints:
    """Test async functionality in endpoints."""
    
    async def test_concurrent_profile_creation(self):
        """Test handling of concurrent profile creation requests."""
        client = TestClient(app)
        
        with patch('src.collaboration_orchestrator.multi_developer_routes.profile_manager') as mock_manager:
            mock_manager.create_developer_profile = AsyncMock(return_value={
                "agent_id": "concurrent_test",
                "agent_type": "developer",
                "created_at": datetime.utcnow().isoformat()
            })
            
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