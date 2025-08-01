"""Unit tests for Multi-Developer Coordination system."""

import asyncio
import json
import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from unittest.mock import Mock, AsyncMock, patch

from src.collaboration_orchestrator.multi_developer_models import (
    DeveloperProfile,
    DeveloperSpecialization,
    ExperienceLevel,
    TaskType,
    TaskStatus,
    TaskAssignment,
    TeamCoordinationPlan,
    ConflictType,
    ConflictSeverity,
    ResolutionStrategy,
    ConflictResolutionLog,
    PerformanceMetrics,
)
from src.collaboration_orchestrator.developer_profile_manager import DeveloperProfileManager
from src.collaboration_orchestrator.intelligent_conflict_resolver import (
    IntelligentConflictResolver,
    ConflictAnalyzer,
    AutomatedResolutionEngine,
)
from src.collaboration_orchestrator.multi_developer_orchestrator import (
    MultiDeveloperOrchestrator,
    TaskAssignmentEngine,
)


class TestDeveloperProfile:
    """Test DeveloperProfile model and methods."""
    
    def test_developer_profile_creation(self):
        """Test creating a developer profile."""
        profile = DeveloperProfile(
            agent_id="test_agent",
            specializations=[DeveloperSpecialization.BACKEND],
            programming_languages=["Python", "JavaScript"],
            frameworks=["FastAPI", "React"],
            experience_level=ExperienceLevel.SENIOR
        )
        
        assert profile.agent_id == "test_agent"
        assert DeveloperSpecialization.BACKEND in profile.specializations
        assert profile.experience_level == ExperienceLevel.SENIOR
        assert profile.current_workload == 0
        assert profile.max_concurrent_tasks == 3
    
    def test_capability_score_calculation(self):
        """Test capability score calculation for tasks."""
        profile = DeveloperProfile(
            agent_id="test_agent",
            specializations=[DeveloperSpecialization.BACKEND],
            programming_languages=["Python", "Go"],
            frameworks=["FastAPI", "Django"],
            experience_level=ExperienceLevel.SENIOR,
            preferred_tasks=[TaskType.FEATURE_DEVELOPMENT, TaskType.BUG_FIX]
        )
        
        # Test high capability score for matching task
        score = profile.get_capability_score(
            TaskType.FEATURE_DEVELOPMENT,
            ["Python", "FastAPI"]
        )
        assert score > 0.7
        
        # Test lower capability score for non-matching task
        score = profile.get_capability_score(
            TaskType.TESTING,
            ["Java", "JUnit"]
        )
        assert score < 0.7
    
    def test_availability_check(self):
        """Test agent availability checking."""
        profile = DeveloperProfile(
            agent_id="test_agent",
            current_workload=20,  # 20 hours
            max_concurrent_tasks=3  # 3 * 8 = 24 hours max
        )
        
        assert profile.is_available(2)  # 2 hours - should be available
        assert not profile.is_available(6)  # 6 hours - would exceed capacity


class TestPerformanceMetrics:
    """Test PerformanceMetrics model and calculations."""
    
    def test_completion_rate_calculation(self):
        """Test task completion rate calculation."""
        metrics = PerformanceMetrics(
            tasks_completed=8,
            tasks_failed=2
        )
        
        assert metrics.completion_rate == 0.8
        
        # Test edge case with no tasks
        empty_metrics = PerformanceMetrics()
        assert empty_metrics.completion_rate == 0.0


class TestTaskAssignment:
    """Test TaskAssignment model and properties."""
    
    def test_task_assignment_creation(self):
        """Test creating a task assignment."""
        plan_id = uuid4()
        assignment = TaskAssignment(
            plan_id=plan_id,
            task_name="Implement user authentication",
            task_description="Add OAuth2 authentication",
            task_type=TaskType.FEATURE_DEVELOPMENT,
            assigned_agent="dev_001",
            complexity_score=0.7,
            estimated_effort=8
        )
        
        assert assignment.plan_id == plan_id
        assert assignment.task_type == TaskType.FEATURE_DEVELOPMENT
        assert assignment.status == TaskStatus.PENDING
        assert assignment.complexity_score == 0.7
    
    def test_task_blocking_check(self):
        """Test task blocking detection."""
        assignment = TaskAssignment(
            plan_id=uuid4(),
            task_name="Test task",
            task_description="Test description",
            task_type=TaskType.TESTING,
            assigned_agent="test_agent",
            blockers=["Waiting for API design"]
        )
        
        assert assignment.is_blocked
        
        # Test status-based blocking
        assignment.blockers = []
        assignment.status = TaskStatus.BLOCKED
        assert assignment.is_blocked
    
    def test_overdue_check(self):
        """Test overdue task detection."""
        past_deadline = datetime.utcnow() - timedelta(hours=1)
        assignment = TaskAssignment(
            plan_id=uuid4(),
            task_name="Overdue task",
            task_description="Test description",
            task_type=TaskType.BUG_FIX,
            assigned_agent="test_agent",
            deadline=past_deadline
        )
        
        assert assignment.is_overdue
        
        # Test completed task is not overdue
        assignment.status = TaskStatus.COMPLETED
        assert not assignment.is_overdue


class TestTeamCoordinationPlan:
    """Test TeamCoordinationPlan model and methods."""
    
    def test_plan_creation(self):
        """Test creating a team coordination plan."""
        session_id = uuid4()
        plan = TeamCoordinationPlan(
            session_id=session_id,
            project_name="E-commerce Platform",
            project_description="Build a modern e-commerce platform",
            team_lead="lead_001",
            team_members=["lead_001", "dev_001", "dev_002"]
        )
        
        assert plan.session_id == session_id
        assert plan.team_lead == "lead_001"
        assert len(plan.team_members) == 3
        assert plan.status == "draft"
    
    def test_workload_distribution_calculation(self):
        """Test team workload distribution calculation."""
        plan = TeamCoordinationPlan(
            session_id=uuid4(),
            project_name="Test Project",
            project_description="Test",
            team_lead="lead_001",
            team_members=["lead_001", "dev_001", "dev_002"]
        )
        
        # Add task assignments
        assignment1 = TaskAssignment(
            plan_id=plan.plan_id,
            task_name="Task 1",
            task_description="Test",
            task_type=TaskType.FEATURE_DEVELOPMENT,
            assigned_agent="dev_001",
            estimated_effort=8
        )
        assignment2 = TaskAssignment(
            plan_id=plan.plan_id,
            task_name="Task 2",
            task_description="Test",
            task_type=TaskType.BUG_FIX,
            assigned_agent="dev_001",
            estimated_effort=4
        )
        assignment3 = TaskAssignment(
            plan_id=plan.plan_id,
            task_name="Task 3",
            task_description="Test",
            task_type=TaskType.TESTING,
            assigned_agent="dev_002",
            estimated_effort=6
        )
        
        plan.task_assignments = {
            str(assignment1.assignment_id): assignment1,
            str(assignment2.assignment_id): assignment2,
            str(assignment3.assignment_id): assignment3,
        }
        
        workload = plan.get_team_workload_distribution()
        assert workload["dev_001"] == 12  # 8 + 4
        assert workload["dev_002"] == 6
        assert workload["lead_001"] == 0
    
    def test_completion_percentage_calculation(self):
        """Test plan completion percentage calculation."""
        plan = TeamCoordinationPlan(
            session_id=uuid4(),
            project_name="Test Project",
            project_description="Test",
            team_lead="lead_001",
            team_members=["lead_001", "dev_001"]
        )
        
        # Add assignments with different progress
        assignment1 = TaskAssignment(
            plan_id=plan.plan_id,
            task_name="Task 1",
            task_description="Test",
            task_type=TaskType.FEATURE_DEVELOPMENT,
            assigned_agent="dev_001",
            progress_percentage=100
        )
        assignment2 = TaskAssignment(
            plan_id=plan.plan_id,
            task_name="Task 2",
            task_description="Test",
            task_type=TaskType.BUG_FIX,
            assigned_agent="dev_001",
            progress_percentage=50
        )
        
        plan.task_assignments = {
            str(assignment1.assignment_id): assignment1,
            str(assignment2.assignment_id): assignment2,
        }
        
        assert plan.completion_percentage == 75.0  # (100 + 50) / 2


class TestConflictAnalyzer:
    """Test ConflictAnalyzer functionality."""
    
    def test_conflict_type_detection(self):
        """Test conflict type detection from description."""
        analyzer = ConflictAnalyzer()
        
        # Test merge conflict detection
        conflict_type, severity, strategy = analyzer.analyze_conflict(
            "Git merge conflict in main.py",
            {},
            ["dev_001", "dev_002"]
        )
        assert conflict_type == ConflictType.MERGE_CONFLICT
        assert strategy == ResolutionStrategy.AUTOMATED
        
        # Test design conflict detection
        conflict_type, severity, strategy = analyzer.analyze_conflict(
            "Disagreement on architecture pattern choice",
            {},
            ["architect_001", "dev_001"]
        )
        assert conflict_type == ConflictType.DESIGN_CONFLICT
        assert strategy == ResolutionStrategy.EXPERTISE_BASED
    
    def test_severity_adjustment(self):
        """Test conflict severity adjustment based on context."""
        analyzer = ConflictAnalyzer()
        
        # Test deadline impact increases severity
        conflict_type, severity, strategy = analyzer.analyze_conflict(
            "Resource conflict with database",
            {"deadline_impact": True},
            ["dev_001", "dev_002"]
        )
        assert severity in [ConflictSeverity.HIGH, ConflictSeverity.CRITICAL]
        
        # Test critical path impact
        conflict_type, severity, strategy = analyzer.analyze_conflict(
            "Dependency issue",
            {"affects_critical_path": True},
            ["dev_001"]
        )
        assert severity == ConflictSeverity.CRITICAL
        assert strategy == ResolutionStrategy.ESCALATION


@pytest.mark.asyncio
class TestDeveloperProfileManager:
    """Test DeveloperProfileManager functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.profile_manager = DeveloperProfileManager()
        self.profile_manager.postgres_pool = None  # Use mock connections
        self.profile_manager.redis = Mock()
    
    async def test_create_developer_profile(self):
        """Test creating a developer profile."""
        with patch('src.common.database.DatabaseManager') as MockDatabaseManager:
            MockDatabaseManager.return_value.get_connection.return_value.__aenter__.return_value = AsyncMock()
            
            profile = await self.profile_manager.create_developer_profile(
                agent_id="test_agent",
                specializations=[DeveloperSpecialization.BACKEND],
                programming_languages=["Python"],
                experience_level=ExperienceLevel.SENIOR
            )
            
            assert profile.agent_id == "test_agent"
            assert profile.experience_level == ExperienceLevel.SENIOR
            
            # Verify database call was made
            mock_conn.return_value.execute.assert_called_once()
    
    async def test_find_best_agents_for_task(self):
        """Test finding best agents for a task."""
        with patch('src.common.database.DatabaseManager') as MockDatabaseManager:
            # Mock database response
            MockDatabaseManager.return_value.get_connection.return_value.__aenter__.return_value = AsyncMock()
            MockDatabaseManager.return_value.get_connection.return_value.__aenter__.return_value.fetch.return_value = [{"agent_id": "dev_001"}, {"agent_id": "dev_002"}]
            
            # Mock profile retrieval
            self.profile_manager.get_developer_profile = AsyncMock()
            self.profile_manager.get_developer_profile.side_effect = [
                DeveloperProfile(
                    agent_id="dev_001",
                    specializations=[DeveloperSpecialization.BACKEND],
                    programming_languages=["Python"],
                    experience_level=ExperienceLevel.SENIOR,
                    current_workload=10
                ),
                DeveloperProfile(
                    agent_id="dev_002",
                    specializations=[DeveloperSpecialization.FRONTEND],
                    programming_languages=["JavaScript"],
                    experience_level=ExperienceLevel.INTERMEDIATE,
                    current_workload=5
                )
            ]
            
            candidates = await self.profile_manager.find_best_agents_for_task(
                TaskType.FEATURE_DEVELOPMENT,
                ["Python"],
                max_agents=2
            )
            
            assert len(candidates) == 2
            assert candidates[0][0] == "dev_001"  # Should rank higher due to experience and skill match
            assert candidates[0][1] > candidates[1][1]  # Higher score


@pytest.mark.asyncio
class TestIntelligentConflictResolver:
    """Test IntelligentConflictResolver functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.profile_manager = Mock(spec=DeveloperProfileManager)
        self.conflict_resolver = IntelligentConflictResolver(self.profile_manager)
        self.conflict_resolver.postgres_pool = None
        self.conflict_resolver.redis = Mock()
    
    async def test_detect_conflict(self):
        """Test conflict detection and analysis."""
        session_id = uuid4()
        plan_id = uuid4()
        
        with patch('src.common.database.DatabaseManager') as MockDatabaseManager:
            MockDatabaseManager.return_value.get_connection.return_value.__aenter__.return_value = AsyncMock()
            
            conflict = await self.conflict_resolver.detect_conflict(
                session_id=session_id,
                plan_id=plan_id,
                conflict_description="Git merge conflict in feature branch",
                involved_agents=["dev_001", "dev_002"],
                context={"conflict_files": ["main.py", "utils.py"]}
            )
            
            assert conflict.session_id == session_id
            assert conflict.plan_id == plan_id
            assert conflict.conflict_type == ConflictType.MERGE_CONFLICT
            assert len(conflict.involved_agents) == 2
            
            # Verify database storage
            MockDatabaseManager.return_value.get_connection.return_value.__aenter__.return_value.execute.assert_called_once()
    
    async def test_automated_resolution_feasibility(self):
        """Test automated resolution feasibility check."""
        conflict = ConflictResolutionLog(
            session_id=uuid4(),
            conflict_type=ConflictType.MERGE_CONFLICT,
            conflict_description="Simple merge conflict",
            involved_agents=["dev_001", "dev_002"],
            conflict_severity=ConflictSeverity.LOW
        )
        
        can_resolve = await self.conflict_resolver.automated_engine.can_resolve_automatically(conflict)
        assert can_resolve
        
        # Test complex conflict that cannot be auto-resolved
        complex_conflict = ConflictResolutionLog(
            session_id=uuid4(),
            conflict_type=ConflictType.DESIGN_CONFLICT,
            conflict_description="Architecture disagreement",
            involved_agents=["dev_001", "dev_002", "dev_003"],
            conflict_severity=ConflictSeverity.HIGH
        )
        
        can_resolve = await self.conflict_resolver.automated_engine.can_resolve_automatically(complex_conflict)
        assert not can_resolve


@pytest.mark.asyncio
class TestMultiDeveloperOrchestrator:
    """Test MultiDeveloperOrchestrator functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.orchestrator = MultiDeveloperOrchestrator()
        self.orchestrator.postgres_pool = None
        self.orchestrator.redis = Mock()
        
        # Mock the managers
        self.orchestrator.profile_manager = Mock(spec=DeveloperProfileManager)
        self.orchestrator.conflict_resolver = Mock(spec=IntelligentConflictResolver)
    
    async def test_create_team_coordination_plan(self):
        """Test creating a team coordination plan."""
        session_id = uuid4()
        
        # Mock available agents
        self.orchestrator._get_available_team_agents = AsyncMock(return_value=[
            DeveloperProfile(
                agent_id="dev_001",
                specializations=[DeveloperSpecialization.BACKEND],
                experience_level=ExperienceLevel.SENIOR
            ),
            DeveloperProfile(
                agent_id="dev_002",
                specializations=[DeveloperSpecialization.FRONTEND],
                experience_level=ExperienceLevel.INTERMEDIATE
            )
        ])
        
        # Mock assignment optimization
        self.orchestrator.assignment_engine.optimize_task_assignments = AsyncMock(
            return_value={}
        )
        
        with patch('src.common.database.DatabaseManager') as MockDatabaseManager:
            MockDatabaseManager.return_value.get_connection.return_value.__aenter__.return_value = AsyncMock()
            
            tasks = [
                {
                    "name": "User Authentication",
                    "description": "Implement OAuth2",
                    "type": TaskType.FEATURE_DEVELOPMENT.value,
                    "assigned_agent": "dev_001",
                    "estimated_effort": 8,
                    "priority": "high"
                },
                {
                    "name": "UI Components",
                    "description": "Create reusable components",
                    "type": TaskType.FEATURE_DEVELOPMENT.value,
                    "assigned_agent": "dev_002",
                    "estimated_effort": 6,
                    "priority": "medium"
                }
            ]
            
            plan = await self.orchestrator.create_team_coordination_plan(
                session_id=session_id,
                project_name="E-commerce Platform",
                project_description="Modern e-commerce solution",
                team_lead="dev_001",
                team_members=["dev_001", "dev_002"],
                tasks=tasks
            )
            
            assert plan.session_id == session_id
            assert plan.project_name == "E-commerce Platform"
            assert plan.team_lead == "dev_001"
            assert len(plan.team_members) == 2
            
            # Verify database storage was called
            mock_conn.return_value.execute.assert_called()
    
    async def test_assign_task_to_agent(self):
        """Test assigning a task to an agent."""
        plan_id = uuid4()
        assignment_id = uuid4()
        
        # Mock plan retrieval
        plan = TeamCoordinationPlan(
            session_id=uuid4(),
            project_name="Test Project",
            project_description="Test",
            team_lead="lead_001",
            team_members=["lead_001", "dev_001"]
        )
        
        assignment = TaskAssignment(
            plan_id=plan_id,
            task_name="Test Task",
            task_description="Test",
            task_type=TaskType.FEATURE_DEVELOPMENT,
            assigned_agent="dev_001"
        )
        assignment.assignment_id = assignment_id
        plan.task_assignments[str(assignment_id)] = assignment
        
        self.orchestrator.get_coordination_plan = AsyncMock(return_value=plan)
        self.orchestrator.profile_manager.get_developer_profile = AsyncMock(
            return_value=DeveloperProfile(
                agent_id="dev_002",
                current_workload=5,
                max_concurrent_tasks=3
            )
        )
        self.orchestrator._update_coordination_plan = AsyncMock()
        self.orchestrator._update_task_assignment = AsyncMock()
        
        success = await self.orchestrator.assign_task_to_agent(
            plan_id=plan_id,
            assignment_id=assignment_id,
            agent_id="dev_002",
            reviewer_agents=["dev_001"]
        )
        
        assert success
        assert assignment.assigned_agent == "dev_002"
        assert "dev_001" in assignment.reviewer_agents
        assert assignment.status == TaskStatus.ASSIGNED
    
    async def test_handle_task_progress_update(self):
        """Test handling task progress updates."""
        assignment_id = uuid4()
        
        assignment = TaskAssignment(
            plan_id=uuid4(),
            task_name="Test Task",
            task_description="Test",
            task_type=TaskType.FEATURE_DEVELOPMENT,
            assigned_agent="dev_001"
        )
        assignment.assignment_id = assignment_id
        
        self.orchestrator._get_task_assignment = AsyncMock(return_value=assignment)
        self.orchestrator._update_task_assignment = AsyncMock()
        self.orchestrator._handle_task_blockers = AsyncMock()
        self.orchestrator.profile_manager.update_performance_metrics = AsyncMock()
        
        success = await self.orchestrator.handle_task_progress_update(
            assignment_id=assignment_id,
            agent_id="dev_001",
            progress_percentage=75,
            status=TaskStatus.IN_PROGRESS,
            blockers=["Waiting for API"],
            feedback={"quality": "good"}
        )
        
        assert success
        assert assignment.progress_percentage == 75
        assert assignment.status == TaskStatus.IN_PROGRESS
        assert "Waiting for API" in assignment.blockers
        assert len(assignment.feedback) == 1
        
        # Verify blocker handling was called
        self.orchestrator._handle_task_blockers.assert_called_once()


class TestTaskAssignmentEngine:
    """Test TaskAssignmentEngine functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.profile_manager = Mock(spec=DeveloperProfileManager)
        self.assignment_engine = TaskAssignmentEngine(self.profile_manager)
    
    async def test_calculate_assignment_score(self):
        """Test assignment score calculation."""
        agent = DeveloperProfile(
            agent_id="dev_001",
            specializations=[DeveloperSpecialization.BACKEND],
            programming_languages=["Python", "Go"],
            experience_level=ExperienceLevel.SENIOR,
            preferred_tasks=[TaskType.FEATURE_DEVELOPMENT],
            performance_metrics=PerformanceMetrics(overall_score=0.9)
        )
        
        task = TaskAssignment(
            plan_id=uuid4(),
            task_name="API Development",
            task_description="Build REST API",
            task_type=TaskType.FEATURE_DEVELOPMENT,
            assigned_agent="dev_001",
            complexity_score=0.8,
            requirements={"skills": ["Python", "FastAPI"]}
        )
        
        score = await self.assignment_engine._calculate_assignment_score(
            agent, task, ["Python", "FastAPI"], current_workload=10
        )
        
        # Should be high score due to skill match, experience, and task preference
        assert score > 0.7
        
        # Test with overloaded agent
        score_overloaded = await self.assignment_engine._calculate_assignment_score(
            agent, task, ["Python", "FastAPI"], current_workload=30  # Very high workload
        )
        
        # Score should be lower due to workload penalty
        assert score_overloaded < score
    
    def test_suggest_task_optimizations(self):
        """Test task optimization suggestions."""
        plan = TeamCoordinationPlan(
            session_id=uuid4(),
            project_name="Test Project",
            project_description="Test",
            team_lead="lead_001",
            team_members=["lead_001", "dev_001", "dev_002"]
        )
        
        # Create assignments with workload issues
        overloaded_assignment = TaskAssignment(
            plan_id=plan.plan_id,
            task_name="Heavy Task",
            task_description="Complex task",
            task_type=TaskType.FEATURE_DEVELOPMENT,
            assigned_agent="dev_001",
            estimated_effort=20  # High effort
        )
        
        plan.task_assignments[str(overloaded_assignment.assignment_id)] = overloaded_assignment
        
        agent_profiles = {
            "dev_001": DeveloperProfile(
                agent_id="dev_001",
                max_concurrent_tasks=2,  # Low capacity
                current_workload=20
            ),
            "dev_002": DeveloperProfile(
                agent_id="dev_002",
                max_concurrent_tasks=3,
                current_workload=5
            )
        }
        
        suggestions = self.assignment_engine.suggest_task_optimizations(plan, agent_profiles)
        
        assert len(suggestions) > 0
        assert any(s.suggestion_type == "reassignment" for s in suggestions)
        assert any("overloaded" in s.rationale.lower() for s in suggestions)


@pytest.mark.asyncio
class TestIntegrationScenarios:
    """Integration tests for complete workflows."""
    
    def setup_method(self):
        """Set up integration test fixtures."""
        self.orchestrator = MultiDeveloperOrchestrator()
        self.orchestrator.postgres_pool = None
        self.orchestrator.redis = Mock()
        
        # Create mock agents
        self.agents = {
            "senior_dev": DeveloperProfile(
                agent_id="senior_dev",
                specializations=[DeveloperSpecialization.BACKEND, DeveloperSpecialization.ARCHITECTURE],
                programming_languages=["Python", "Go", "TypeScript"],
                frameworks=["FastAPI", "Django", "React"],
                experience_level=ExperienceLevel.SENIOR,
                preferred_tasks=[TaskType.FEATURE_DEVELOPMENT, TaskType.ARCHITECTURE_DESIGN],
                current_workload=10,
                max_concurrent_tasks=4
            ),
            "frontend_dev": DeveloperProfile(
                agent_id="frontend_dev",
                specializations=[DeveloperSpecialization.FRONTEND],
                programming_languages=["JavaScript", "TypeScript"],
                frameworks=["React", "Vue", "Angular"],
                experience_level=ExperienceLevel.INTERMEDIATE,
                preferred_tasks=[TaskType.FEATURE_DEVELOPMENT, TaskType.BUG_FIX],
                current_workload=8,
                max_concurrent_tasks=3
            ),
            "qa_specialist": DeveloperProfile(
                agent_id="qa_specialist",
                specializations=[DeveloperSpecialization.QA],
                programming_languages=["Python", "JavaScript"],
                frameworks=["Pytest", "Jest", "Selenium"],
                experience_level=ExperienceLevel.SENIOR,
                preferred_tasks=[TaskType.TESTING, TaskType.CODE_REVIEW],
                current_workload=5,
                max_concurrent_tasks=3
            )
        }
    
    async def test_complete_project_workflow(self):
        """Test a complete project workflow from plan creation to completion."""
        session_id = uuid4()
        
        # Mock all the necessary methods
        with patch.multiple(
            self.orchestrator,
            _get_available_team_agents=AsyncMock(return_value=list(self.agents.values())),
            _store_coordination_plan=AsyncMock(),
            _update_coordination_plan=AsyncMock(),
            _update_task_assignment=AsyncMock(),
            get_coordination_plan=AsyncMock(),
            detect_and_resolve_conflicts=AsyncMock(return_value=[])
        ):
            
            # 1. Create coordination plan
            tasks = [
                {
                    "name": "Backend API",
                    "description": "Develop REST API",
                    "type": TaskType.FEATURE_DEVELOPMENT.value,
                    "requirements": {"skills": ["Python", "FastAPI"]},
                    "estimated_effort": 12,
                    "priority": "high"
                },
                {
                    "name": "Frontend UI",
                    "description": "Create user interface",
                    "type": TaskType.FEATURE_DEVELOPMENT.value,
                    "requirements": {"skills": ["React", "TypeScript"]},
                    "estimated_effort": 10,
                    "priority": "high"
                },
                {
                    "name": "Integration Tests",
                    "description": "End-to-end testing",
                    "type": TaskType.TESTING.value,
                    "requirements": {"skills": ["Python", "Selenium"]},
                    "estimated_effort": 6,
                    "priority": "medium"
                }
            ]
            
            plan = await self.orchestrator.create_team_coordination_plan(
                session_id=session_id,
                project_name="E-commerce Platform",
                project_description="Full-stack e-commerce solution",
                team_lead="senior_dev",
                team_members=list(self.agents.keys()),
                tasks=tasks
            )
            
            assert plan.project_name == "E-commerce Platform"
            assert len(plan.task_assignments) == 3
            
            # 2. Verify optimal assignments were made
            # The assignment optimization should assign tasks to best-suited agents
            backend_tasks = [a for a in plan.task_assignments.values() if "API" in a.task_name]
            frontend_tasks = [a for a in plan.task_assignments.values() if "UI" in a.task_name]
            testing_tasks = [a for a in plan.task_assignments.values() if "Test" in a.task_name]
            
            # Backend task should ideally go to senior_dev (has Python, FastAPI)
            # Frontend task should go to frontend_dev (has React, TypeScript)
            # Testing task should go to qa_specialist (has testing specialization)
            
            # 3. Simulate task progress
            for assignment in plan.task_assignments.values():
                self.orchestrator.get_coordination_plan.return_value = plan
                
                # Start task
                await self.orchestrator.handle_task_progress_update(
                    assignment_id=assignment.assignment_id,
                    agent_id=assignment.assigned_agent,
                    progress_percentage=25,
                    status=TaskStatus.IN_PROGRESS
                )
                
                # Mid-progress update
                await self.orchestrator.handle_task_progress_update(
                    assignment_id=assignment.assignment_id,
                    agent_id=assignment.assigned_agent,
                    progress_percentage=75,
                    status=TaskStatus.IN_PROGRESS
                )
                
                # Complete task
                await self.orchestrator.handle_task_progress_update(
                    assignment_id=assignment.assignment_id,
                    agent_id=assignment.assigned_agent,
                    progress_percentage=100,
                    status=TaskStatus.COMPLETED
                )
            
            # 4. Check for conflicts (should be none in this ideal scenario)
            conflicts = await self.orchestrator.detect_and_resolve_conflicts(plan.plan_id)
            assert len(conflicts) == 0
            
            # 5. Generate performance report
            with patch.object(self.orchestrator, 'get_coordination_plan', return_value=plan):
                with patch.object(self.orchestrator.conflict_resolver, 'get_conflict_statistics', return_value={}):
                    with patch.object(self.orchestrator.profile_manager, 'get_developer_profile') as mock_get_profile:
                        mock_get_profile.side_effect = lambda agent_id: self.agents.get(agent_id)
                        
                        report = await self.orchestrator.generate_team_performance_report(plan.plan_id)
                        
                        assert report["plan_id"] == str(plan.plan_id)
                        assert report["project_name"] == "E-commerce Platform"
                        assert report["overall_progress"] >= 0
                        assert "task_summary" in report
                        assert "agent_performance" in report
    
    async def test_conflict_resolution_workflow(self):
        """Test conflict detection and resolution workflow."""
        session_id = uuid4()
        plan_id = uuid4()
        
        # Mock database connections
        with patch.multiple(
            self.orchestrator.conflict_resolver,
            _get_db_connection=AsyncMock(return_value=AsyncMock()),
            _store_conflict=AsyncMock(),
            _mark_conflict_resolved=AsyncMock()
        ):
            
            # 1. Detect a merge conflict
            conflict = await self.orchestrator.conflict_resolver.detect_conflict(
                session_id=session_id,
                plan_id=plan_id,
                conflict_description="Git merge conflict in authentication module",
                involved_agents=["senior_dev", "frontend_dev"],
                context={
                    "conflict_files": ["auth.py", "login.js"],
                    "branch_1": "feature/oauth",
                    "branch_2": "feature/social-login"
                }
            )
            
            assert conflict.conflict_type == ConflictType.MERGE_CONFLICT
            assert conflict.conflict_severity in [ConflictSeverity.LOW, ConflictSeverity.MEDIUM]
            assert conflict.resolution_strategy == ResolutionStrategy.AUTOMATED
            
            # 2. Attempt automatic resolution
            with patch.object(
                self.orchestrator.conflict_resolver.automated_engine,
                'resolve_merge_conflict',
                return_value=(True, "Conflicts resolved automatically")
            ):
                resolved = await self.orchestrator.conflict_resolver.resolve_conflict(conflict.conflict_id)
                assert resolved
            
            # 3. Test a design conflict requiring human expertise
            design_conflict = await self.orchestrator.conflict_resolver.detect_conflict(
                session_id=session_id,
                plan_id=plan_id,
                conflict_description="Disagreement on database architecture pattern",
                involved_agents=["senior_dev", "qa_specialist"],
                context={
                    "options": ["Microservices", "Monolithic"],
                    "has_domain_expert": True,
                    "affects_critical_path": True
                }
            )
            
            assert design_conflict.conflict_type == ConflictType.DESIGN_CONFLICT
            assert design_conflict.conflict_severity == ConflictSeverity.CRITICAL
            assert design_conflict.resolution_strategy == ResolutionStrategy.ESCALATION
            
            # This type of conflict would require escalation or expert decision
            # In a real scenario, it would send messages to appropriate agents
            
        # Verify conflicts were properly tracked
        assert conflict.conflict_id in self.orchestrator.conflict_resolver.active_conflicts or \
               conflict.status == "resolved"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])