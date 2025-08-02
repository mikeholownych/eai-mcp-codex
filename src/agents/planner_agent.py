"""Planner Agent - Specializes in task breakdown and project planning."""

import asyncio
from typing import Any, Dict, List
from datetime import datetime, timedelta

from .base_agent import BaseAgent, AgentConfig, TaskInput


class PlannerAgent(BaseAgent):
    """Agent specialized in project planning and task breakdown."""

    @classmethod
    def create(cls, agent_id: str, name: str | None = None) -> "PlannerAgent":
        """Factory compatible with legacy startup scripts."""
        return cls(agent_id=agent_id, name=name)

    def __init__(self, agent_id: str = None, name: str = None, config: AgentConfig = None):
        if config is None:
            # Legacy initialization with individual parameters
            config = AgentConfig(
                agent_id=agent_id,
                agent_type="planner",
                name=name or f"Planner-{agent_id}",
                capabilities=[
                    "task_breakdown",
                    "estimation",
                    "dependency_analysis",
                    "project_planning",
                    "milestone_creation",
                    "resource_planning",
                ],
                max_concurrent_tasks=5,
                heartbeat_interval=30,
            )
        super().__init__(config)

        # Planner-specific state
        self.planning_templates = {
            "web_app": self._web_app_template,
            "api_service": self._api_service_template,
            "data_pipeline": self._data_pipeline_template,
            "mobile_app": self._mobile_app_template,
        }

    async def _initialize_agent(self) -> None:
        """Initialize planner-specific resources."""
        self.logger.info("Planner agent initialized with planning templates")
        await asyncio.sleep(0.1)  # Agent initialization complete

    async def process_task(self, task: TaskInput) -> Dict[str, Any]:
        """Process planning-related tasks."""
        task_type = task.task_type.lower()
        context = task.context

        if task_type == "project_breakdown":
            return await self._break_down_project(task.description, context)
        elif task_type == "estimate_effort":
            return await self._estimate_effort(context)
        elif task_type == "create_timeline":
            return await self._create_timeline(context)
        elif task_type == "analyze_dependencies":
            return await self._analyze_dependencies(context)
        elif task_type == "create_milestones":
            return await self._create_milestones(context)
        else:
            raise ValueError(f"Unknown task type: {task_type}")

    async def get_capabilities(self) -> List[str]:
        """Get current planner capabilities."""
        return self.config.capabilities

    async def _break_down_project(
        self, description: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Break down a project into manageable tasks."""
        project_type = context.get("project_type", "general")
        complexity = context.get("complexity", "medium")

        # Use appropriate template
        if project_type in self.planning_templates:
            template_func = self.planning_templates[project_type]
            tasks = await template_func(description, complexity)
        else:
            tasks = await self._general_breakdown(description, complexity)

        # Add estimates and dependencies
        enhanced_tasks = []
        for i, task in enumerate(tasks):
            enhanced_task = {
                "id": f"task_{i+1}",
                "title": task["title"],
                "description": task["description"],
                "estimated_hours": task.get("estimated_hours", 8),
                "priority": task.get("priority", "medium"),
                "dependencies": task.get("dependencies", []),
                "skills_required": task.get("skills_required", []),
                "deliverables": task.get("deliverables", []),
            }
            enhanced_tasks.append(enhanced_task)

        return {
            "project_description": description,
            "project_type": project_type,
            "complexity": complexity,
            "total_tasks": len(enhanced_tasks),
            "estimated_total_hours": sum(
                task["estimated_hours"] for task in enhanced_tasks
            ),
            "tasks": enhanced_tasks,
            "recommendations": await self._generate_recommendations(
                enhanced_tasks, context
            ),
        }

    async def _estimate_effort(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Estimate effort for a set of tasks."""
        tasks = context.get("tasks", [])
        team_size = context.get("team_size", 3)
        experience_level = context.get("experience_level", "intermediate")

        # Base estimates
        total_hours = 0
        task_estimates = []

        for task in tasks:
            base_hours = task.get("estimated_hours", 8)

            # Apply complexity multipliers
            if task.get("complexity") == "high":
                base_hours *= 1.5
            elif task.get("complexity") == "low":
                base_hours *= 0.7

            # Apply experience multipliers
            if experience_level == "junior":
                base_hours *= 1.3
            elif experience_level == "senior":
                base_hours *= 0.8

            task_estimates.append(
                {
                    "task_id": task.get("id", "unknown"),
                    "title": task.get("title", "Untitled"),
                    "estimated_hours": round(base_hours, 1),
                    "confidence": self._calculate_confidence(task),
                }
            )

            total_hours += base_hours

        # Calculate timeline
        working_hours_per_day = 6  # Accounting for meetings, etc.
        total_days = total_hours / (team_size * working_hours_per_day)

        return {
            "total_estimated_hours": round(total_hours, 1),
            "estimated_days": round(total_days, 1),
            "estimated_weeks": round(total_days / 5, 1),
            "team_size": team_size,
            "task_estimates": task_estimates,
            "confidence_level": sum(est["confidence"] for est in task_estimates)
            / len(task_estimates),
            "buffer_recommendation": "20%",  # Recommended buffer
            "assumptions": [
                f"Team of {team_size} {experience_level} developers",
                f"{working_hours_per_day} productive hours per day",
                "Standard complexity multipliers applied",
            ],
        }

    async def _create_timeline(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Create a project timeline with milestones."""
        tasks = context.get("tasks", [])
        start_date = datetime.fromisoformat(
            context.get("start_date", datetime.utcnow().isoformat())
        )
        team_size = context.get("team_size", 3)

        # Sort tasks by dependencies
        sorted_tasks = self._topological_sort(tasks)

        timeline = []
        current_date = start_date

        for task in sorted_tasks:
            estimated_hours = task.get("estimated_hours", 8)
            working_days = max(
                1, estimated_hours / (6 * team_size)
            )  # 6 productive hours per day

            end_date = current_date + timedelta(days=working_days)

            timeline_item = {
                "task_id": task.get("id"),
                "title": task.get("title"),
                "start_date": current_date.isoformat(),
                "end_date": end_date.isoformat(),
                "duration_days": round(working_days, 1),
                "dependencies": task.get("dependencies", []),
                "critical_path": self._is_critical_path(task, tasks),
            }

            timeline.append(timeline_item)
            current_date = end_date

        return {
            "project_start": start_date.isoformat(),
            "project_end": current_date.isoformat(),
            "total_duration_days": (current_date - start_date).days,
            "timeline": timeline,
            "milestones": self._extract_milestones(timeline),
            "critical_path": [item for item in timeline if item["critical_path"]],
        }

    async def _analyze_dependencies(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze task dependencies and identify potential issues."""
        tasks = context.get("tasks", [])

        dependency_graph = {}
        issues = []

        for task in tasks:
            task_id = task.get("id")
            dependencies = task.get("dependencies", [])
            dependency_graph[task_id] = dependencies

            # Check for circular dependencies
            if self._has_circular_dependency(task_id, dependency_graph):
                issues.append(
                    {
                        "type": "circular_dependency",
                        "task_id": task_id,
                        "description": f"Circular dependency detected involving task {task_id}",
                    }
                )

            # Check for missing dependencies
            for dep in dependencies:
                if not any(t.get("id") == dep for t in tasks):
                    issues.append(
                        {
                            "type": "missing_dependency",
                            "task_id": task_id,
                            "missing_dep": dep,
                            "description": f"Task {task_id} depends on missing task {dep}",
                        }
                    )

        return {
            "dependency_graph": dependency_graph,
            "total_dependencies": sum(len(deps) for deps in dependency_graph.values()),
            "issues": issues,
            "complexity_score": self._calculate_dependency_complexity(dependency_graph),
            "recommendations": self._generate_dependency_recommendations(
                dependency_graph, issues
            ),
        }

    async def _create_milestones(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Create project milestones based on task completion."""
        tasks = context.get("tasks", [])
        project_phases = context.get(
            "phases", ["planning", "development", "testing", "deployment"]
        )

        milestones = []
        phase_tasks = self._group_tasks_by_phase(tasks, project_phases)

        for phase, phase_task_list in phase_tasks.items():
            if phase_task_list:
                milestone = {
                    "id": f"milestone_{phase}",
                    "title": f"{phase.title()} Complete",
                    "description": f"All {phase} tasks completed",
                    "phase": phase,
                    "tasks": [task.get("id") for task in phase_task_list],
                    "completion_criteria": self._get_phase_criteria(phase),
                    "deliverables": self._get_phase_deliverables(phase),
                    "estimated_completion": None,  # Would be calculated based on timeline
                }
                milestones.append(milestone)

        return {
            "total_milestones": len(milestones),
            "milestones": milestones,
            "success_criteria": self._generate_success_criteria(milestones),
            "risk_factors": self._identify_milestone_risks(milestones),
        }

    # Template methods for different project types

    async def _web_app_template(
        self, description: str, complexity: str
    ) -> List[Dict[str, Any]]:
        """Template for web application projects."""
        base_tasks = [
            {
                "title": "Project Setup and Architecture",
                "description": "Set up development environment and define architecture",
                "estimated_hours": 16,
                "priority": "high",
                "skills_required": ["architecture", "setup"],
                "deliverables": ["project_structure", "architecture_doc"],
            },
            {
                "title": "Database Design",
                "description": "Design and implement database schema",
                "estimated_hours": 12,
                "dependencies": ["task_1"],
                "skills_required": ["database", "modeling"],
                "deliverables": ["database_schema", "migrations"],
            },
            {
                "title": "Backend API Development",
                "description": "Implement core API endpoints",
                "estimated_hours": 32,
                "dependencies": ["task_2"],
                "skills_required": ["backend", "api"],
                "deliverables": ["api_endpoints", "documentation"],
            },
            {
                "title": "Frontend Development",
                "description": "Implement user interface",
                "estimated_hours": 40,
                "dependencies": ["task_1"],
                "skills_required": ["frontend", "ui"],
                "deliverables": ["user_interface", "components"],
            },
            {
                "title": "Integration and Testing",
                "description": "Integrate frontend and backend, implement tests",
                "estimated_hours": 20,
                "dependencies": ["task_3", "task_4"],
                "skills_required": ["testing", "integration"],
                "deliverables": ["test_suite", "integration_tests"],
            },
            {
                "title": "Deployment and DevOps",
                "description": "Set up deployment pipeline and monitoring",
                "estimated_hours": 12,
                "dependencies": ["task_5"],
                "skills_required": ["devops", "deployment"],
                "deliverables": ["deployment_pipeline", "monitoring"],
            },
        ]

        # Adjust based on complexity
        if complexity == "high":
            for task in base_tasks:
                task["estimated_hours"] = int(task["estimated_hours"] * 1.5)
        elif complexity == "low":
            for task in base_tasks:
                task["estimated_hours"] = int(task["estimated_hours"] * 0.7)

        return base_tasks

    async def _api_service_template(
        self, description: str, complexity: str
    ) -> List[Dict[str, Any]]:
        """Template for API service projects."""
        return [
            {
                "title": "API Design and Specification",
                "description": "Design API endpoints and create OpenAPI specification",
                "estimated_hours": 8,
                "priority": "high",
                "skills_required": ["api_design", "documentation"],
            },
            {
                "title": "Core Service Implementation",
                "description": "Implement core business logic and endpoints",
                "estimated_hours": 24,
                "dependencies": ["task_1"],
                "skills_required": ["backend", "api"],
            },
            {
                "title": "Authentication and Authorization",
                "description": "Implement security features",
                "estimated_hours": 12,
                "dependencies": ["task_2"],
                "skills_required": ["security", "auth"],
            },
            {
                "title": "Testing and Validation",
                "description": "Implement comprehensive test suite",
                "estimated_hours": 16,
                "dependencies": ["task_3"],
                "skills_required": ["testing", "validation"],
            },
            {
                "title": "Documentation and Deployment",
                "description": "Create documentation and deploy service",
                "estimated_hours": 8,
                "dependencies": ["task_4"],
                "skills_required": ["documentation", "deployment"],
            },
        ]

    async def _data_pipeline_template(
        self, description: str, complexity: str
    ) -> List[Dict[str, Any]]:
        """Template for data pipeline projects."""
        return [
            {
                "title": "Data Architecture Design",
                "description": "Design data flow and architecture",
                "estimated_hours": 12,
                "skills_required": ["data_architecture", "design"],
            },
            {
                "title": "Data Ingestion",
                "description": "Implement data ingestion mechanisms",
                "estimated_hours": 20,
                "dependencies": ["task_1"],
                "skills_required": ["data_engineering", "etl"],
            },
            {
                "title": "Data Processing",
                "description": "Implement data transformation and processing",
                "estimated_hours": 24,
                "dependencies": ["task_2"],
                "skills_required": ["data_processing", "algorithms"],
            },
            {
                "title": "Data Storage",
                "description": "Set up data storage and indexing",
                "estimated_hours": 16,
                "dependencies": ["task_3"],
                "skills_required": ["database", "storage"],
            },
            {
                "title": "Monitoring and Alerting",
                "description": "Implement pipeline monitoring",
                "estimated_hours": 12,
                "dependencies": ["task_4"],
                "skills_required": ["monitoring", "devops"],
            },
        ]

    async def _mobile_app_template(
        self, description: str, complexity: str
    ) -> List[Dict[str, Any]]:
        """Template for mobile application projects."""
        return [
            {
                "title": "App Architecture and Setup",
                "description": "Set up mobile development environment and architecture",
                "estimated_hours": 12,
                "skills_required": ["mobile", "architecture"],
            },
            {
                "title": "UI/UX Implementation",
                "description": "Implement user interface and navigation",
                "estimated_hours": 32,
                "dependencies": ["task_1"],
                "skills_required": ["mobile_ui", "design"],
            },
            {
                "title": "Core Features Development",
                "description": "Implement main application features",
                "estimated_hours": 40,
                "dependencies": ["task_2"],
                "skills_required": ["mobile", "features"],
            },
            {
                "title": "Backend Integration",
                "description": "Integrate with backend services",
                "estimated_hours": 16,
                "dependencies": ["task_3"],
                "skills_required": ["integration", "api"],
            },
            {
                "title": "Testing and Optimization",
                "description": "Test on multiple devices and optimize performance",
                "estimated_hours": 20,
                "dependencies": ["task_4"],
                "skills_required": ["testing", "optimization"],
            },
            {
                "title": "App Store Preparation",
                "description": "Prepare for app store submission",
                "estimated_hours": 8,
                "dependencies": ["task_5"],
                "skills_required": ["deployment", "publishing"],
            },
        ]

    async def _general_breakdown(
        self, description: str, complexity: str
    ) -> List[Dict[str, Any]]:
        """General project breakdown for unknown project types."""
        return [
            {
                "title": "Requirements Analysis",
                "description": "Analyze and document project requirements",
                "estimated_hours": 8,
                "skills_required": ["analysis", "documentation"],
            },
            {
                "title": "Design and Planning",
                "description": "Create technical design and implementation plan",
                "estimated_hours": 12,
                "dependencies": ["task_1"],
                "skills_required": ["design", "planning"],
            },
            {
                "title": "Core Implementation",
                "description": "Implement main project functionality",
                "estimated_hours": 32,
                "dependencies": ["task_2"],
                "skills_required": ["development", "implementation"],
            },
            {
                "title": "Testing and Quality Assurance",
                "description": "Test implementation and ensure quality",
                "estimated_hours": 16,
                "dependencies": ["task_3"],
                "skills_required": ["testing", "qa"],
            },
            {
                "title": "Documentation and Deployment",
                "description": "Document project and deploy to production",
                "estimated_hours": 8,
                "dependencies": ["task_4"],
                "skills_required": ["documentation", "deployment"],
            },
        ]

    # Utility methods

    def _calculate_confidence(self, task: Dict[str, Any]) -> float:
        """Calculate confidence level for task estimation."""
        base_confidence = 0.8

        # Reduce confidence for complex tasks
        if task.get("complexity") == "high":
            base_confidence -= 0.2

        # Reduce confidence for tasks with many dependencies
        deps = len(task.get("dependencies", []))
        if deps > 3:
            base_confidence -= 0.1

        return max(0.3, base_confidence)

    def _topological_sort(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Sort tasks based on dependencies."""
        # Simple topological sort - could be enhanced
        sorted_tasks = []
        remaining_tasks = tasks.copy()

        while remaining_tasks:
            # Find tasks with no unresolved dependencies
            ready_tasks = []
            for task in remaining_tasks:
                deps = task.get("dependencies", [])
                if all(
                    any(t.get("id") == dep for t in sorted_tasks)
                    or dep not in [t.get("id") for t in tasks]
                    for dep in deps
                ):
                    ready_tasks.append(task)

            if ready_tasks:
                # Add ready tasks to sorted list
                sorted_tasks.extend(ready_tasks)
                for task in ready_tasks:
                    remaining_tasks.remove(task)
            else:
                # Handle circular dependencies by adding remaining tasks
                sorted_tasks.extend(remaining_tasks)
                break

        return sorted_tasks

    def _is_critical_path(
        self, task: Dict[str, Any], all_tasks: List[Dict[str, Any]]
    ) -> bool:
        """Determine if task is on critical path."""
        # Simplified critical path detection
        return task.get("priority") == "high" or len(task.get("dependencies", [])) > 2

    def _extract_milestones(
        self, timeline: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Extract major milestones from timeline."""
        milestones = []

        # Add milestone every 25% of timeline
        total_items = len(timeline)
        milestone_indices = [
            int(total_items * 0.25),
            int(total_items * 0.5),
            int(total_items * 0.75),
            total_items - 1,
        ]

        for i, idx in enumerate(milestone_indices):
            if idx < len(timeline):
                item = timeline[idx]
                milestones.append(
                    {
                        "id": f"milestone_{i+1}",
                        "title": f"Milestone {i+1}",
                        "date": item["end_date"],
                        "tasks_completed": idx + 1,
                        "progress_percentage": ((idx + 1) / total_items) * 100,
                    }
                )

        return milestones

    def _has_circular_dependency(
        self, task_id: str, dependency_graph: Dict[str, List[str]]
    ) -> bool:
        """Check for circular dependencies."""
        visited = set()
        path = set()

        def dfs(node):
            if node in path:
                return True
            if node in visited:
                return False

            visited.add(node)
            path.add(node)

            for dep in dependency_graph.get(node, []):
                if dfs(dep):
                    return True

            path.remove(node)
            return False

        return dfs(task_id)

    def _calculate_dependency_complexity(
        self, dependency_graph: Dict[str, List[str]]
    ) -> float:
        """Calculate complexity score based on dependencies."""
        total_deps = sum(len(deps) for deps in dependency_graph.values())
        total_tasks = len(dependency_graph)

        if total_tasks == 0:
            return 0.0

        return min(10.0, (total_deps / total_tasks) * 2)  # Scale to 0-10

    def _generate_dependency_recommendations(
        self, dependency_graph: Dict[str, List[str]], issues: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate recommendations for dependency management."""
        recommendations = []

        if issues:
            recommendations.append("Resolve dependency issues before proceeding")

        complexity = self._calculate_dependency_complexity(dependency_graph)
        if complexity > 7:
            recommendations.append("Consider breaking down complex dependencies")

        if any(len(deps) > 5 for deps in dependency_graph.values()):
            recommendations.append(
                "Some tasks have too many dependencies - consider simplification"
            )

        return recommendations

    def _group_tasks_by_phase(
        self, tasks: List[Dict[str, Any]], phases: List[str]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Group tasks by project phases."""
        phase_tasks = {phase: [] for phase in phases}

        for task in tasks:
            # Simple phase assignment based on task title/description
            title_lower = task.get("title", "").lower()
            description_lower = task.get("description", "").lower()

            assigned = False
            for phase in phases:
                if phase.lower() in title_lower or phase.lower() in description_lower:
                    phase_tasks[phase].append(task)
                    assigned = True
                    break

            # Default to development phase if not assigned
            if not assigned:
                phase_tasks.get("development", phase_tasks[phases[0]]).append(task)

        return phase_tasks

    def _get_phase_criteria(self, phase: str) -> List[str]:
        """Get completion criteria for a phase."""
        criteria_map = {
            "planning": [
                "Requirements documented",
                "Architecture defined",
                "Timeline approved",
            ],
            "development": [
                "All features implemented",
                "Code reviewed",
                "Unit tests passing",
            ],
            "testing": [
                "All tests passing",
                "Performance verified",
                "Security validated",
            ],
            "deployment": [
                "Production deployment successful",
                "Monitoring active",
                "Documentation complete",
            ],
        }
        return criteria_map.get(phase, ["Phase objectives completed"])

    def _get_phase_deliverables(self, phase: str) -> List[str]:
        """Get deliverables for a phase."""
        deliverables_map = {
            "planning": [
                "Requirements document",
                "Architecture diagram",
                "Project plan",
            ],
            "development": [
                "Source code",
                "API documentation",
                "Development environment",
            ],
            "testing": ["Test results", "Performance report", "Bug reports"],
            "deployment": [
                "Production system",
                "Deployment guide",
                "User documentation",
            ],
        }
        return deliverables_map.get(phase, ["Phase deliverables"])

    def _generate_success_criteria(self, milestones: List[Dict[str, Any]]) -> List[str]:
        """Generate overall project success criteria."""
        return [
            "All milestones completed on time",
            "All deliverables meet quality standards",
            "Stakeholder acceptance achieved",
            "Project deployed successfully",
            "Documentation complete and approved",
        ]

    def _identify_milestone_risks(
        self, milestones: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Identify potential risks for milestones."""
        risks = []

        for milestone in milestones:
            task_count = len(milestone.get("tasks", []))
            if task_count > 10:
                risks.append(
                    {
                        "milestone": milestone["id"],
                        "risk": "high_complexity",
                        "description": f"Milestone has {task_count} tasks - may be difficult to coordinate",
                    }
                )

        return risks

    async def _generate_recommendations(
        self, tasks: List[Dict[str, Any]], context: Dict[str, Any]
    ) -> List[str]:
        """Generate recommendations for the project plan."""
        recommendations = []

        # Check for balance
        total_hours = sum(task["estimated_hours"] for task in tasks)
        if total_hours > 200:
            recommendations.append(
                "Consider breaking this into multiple phases or sprints"
            )

        # Check for skill diversity
        all_skills = set()
        for task in tasks:
            all_skills.update(task.get("skills_required", []))

        if len(all_skills) > 8:
            recommendations.append(
                "Project requires diverse skill set - ensure team coverage"
            )

        # Check for high-risk tasks
        high_risk_tasks = [
            t
            for t in tasks
            if t.get("priority") == "high" and t["estimated_hours"] > 20
        ]
        if high_risk_tasks:
            recommendations.append(
                "Consider breaking down high-priority, high-effort tasks"
            )

        return recommendations
