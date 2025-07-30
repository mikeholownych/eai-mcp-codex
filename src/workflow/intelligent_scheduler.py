"""Intelligent Scheduler with Dependency-Aware Logic and Optimization."""

import networkx as nx
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import numpy as np
import random

from ..common.logging import get_logger
from ..plan_management.models import Task

logger = get_logger("intelligent_scheduler")


class TaskStatus(str, Enum):
    """Task execution status."""

    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"
    SKIPPED = "skipped"


class SchedulingStrategy(str, Enum):
    """Scheduling optimization strategies."""

    MINIMIZE_DURATION = "minimize_duration"
    MAXIMIZE_PARALLELISM = "maximize_parallelism"
    BALANCE_RESOURCES = "balance_resources"
    MINIMIZE_COST = "minimize_cost"
    PRIORITIZE_CRITICAL = "prioritize_critical"


@dataclass
class TaskDependency:
    """Represents a dependency between tasks."""

    predecessor: str
    successor: str
    dependency_type: str = "finish_to_start"  # finish_to_start, start_to_start, etc.
    lag_time: float = 0.0  # in hours
    required: bool = True


@dataclass
class Resource:
    """Represents a computational resource."""

    resource_id: str
    resource_type: str  # cpu, memory, gpu, etc.
    capacity: float
    cost_per_hour: float = 0.0
    availability_schedule: Dict[str, Any] = field(default_factory=dict)
    current_usage: float = 0.0


@dataclass
class ScheduledTask:
    """Task with scheduling information."""

    task_id: str
    task: Task
    dependencies: List[TaskDependency]
    estimated_duration: float
    resource_requirements: Dict[str, float]
    priority: int = 5  # 1-10, higher is more important
    earliest_start: datetime = field(default_factory=datetime.utcnow)
    latest_finish: Optional[datetime] = None
    scheduled_start: Optional[datetime] = None
    scheduled_finish: Optional[datetime] = None
    assigned_resources: List[Resource] = field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    criticality_score: float = 0.0


@dataclass
class SchedulingPlan:
    """Complete scheduling plan with optimization results."""

    plan_id: str
    tasks: List[ScheduledTask]
    total_duration: float
    critical_path: List[str]
    resource_allocation: Dict[str, List[Resource]]
    optimization_objective: str
    optimization_score: float
    parallel_efficiency: float
    resource_utilization: Dict[str, float]
    estimated_cost: float
    created_at: datetime = field(default_factory=datetime.utcnow)
    constraints_satisfied: bool = True
    warnings: List[str] = field(default_factory=list)


class DependencyGraphAnalyzer:
    """Analyzes task dependencies and builds execution graphs."""

    def __init__(self):
        self.graph = nx.DiGraph()

    def build_dependency_graph(self, tasks: List[ScheduledTask]) -> nx.DiGraph:
        """Build directed graph of task dependencies."""
        self.graph.clear()

        # Add all tasks as nodes
        for task in tasks:
            self.graph.add_node(
                task.task_id,
                task=task,
                duration=task.estimated_duration,
                priority=task.priority,
            )

        # Add dependency edges
        for task in tasks:
            for dep in task.dependencies:
                if dep.predecessor in [t.task_id for t in tasks]:
                    self.graph.add_edge(
                        dep.predecessor,
                        dep.successor,
                        dependency_type=dep.dependency_type,
                        lag_time=dep.lag_time,
                        required=dep.required,
                    )

        return self.graph

    def calculate_critical_path(self) -> List[str]:
        """Calculate the critical path through the task graph."""
        if not self.graph.nodes():
            return []

        try:
            # Calculate longest path (critical path)
            critical_path = nx.dag_longest_path(self.graph, weight="duration")
            return critical_path
        except nx.NetworkXError:
            # Graph has cycles - need to handle
            logger.warning("Dependency graph contains cycles")
            return self._find_approximate_critical_path()

    def _find_approximate_critical_path(self) -> List[str]:
        """Find approximate critical path when cycles exist."""
        # Use topological sort with cycle breaking
        try:
            # Break cycles by removing some edges
            cycles = list(nx.simple_cycles(self.graph))
            edges_to_remove = []

            for cycle in cycles:
                # Remove the edge with lowest priority
                min_priority_edge = None
                min_priority = float("inf")

                for i in range(len(cycle)):
                    u, v = cycle[i], cycle[(i + 1) % len(cycle)]
                    if self.graph.has_edge(u, v):
                        task_priority = self.graph.nodes[v]["priority"]
                        if task_priority < min_priority:
                            min_priority = task_priority
                            min_priority_edge = (u, v)

                if min_priority_edge:
                    edges_to_remove.append(min_priority_edge)

            # Create temporary graph without cycles
            temp_graph = self.graph.copy()
            temp_graph.remove_edges_from(edges_to_remove)

            # Find longest path in acyclic graph
            if nx.is_directed_acyclic_graph(temp_graph):
                return nx.dag_longest_path(temp_graph, weight="duration")
            else:
                # Fallback to simple ordering
                return list(nx.topological_sort(temp_graph))

        except Exception as e:
            logger.error(f"Error finding critical path: {e}")
            return []

    def calculate_slack_times(self, critical_path: List[str]) -> Dict[str, float]:
        """Calculate slack time for each task."""
        slack_times = {}

        # Tasks on critical path have zero slack
        for task_id in critical_path:
            slack_times[task_id] = 0.0

        # Calculate slack for non-critical tasks
        for task_id in self.graph.nodes():
            if task_id not in critical_path:
                # Simplified slack calculation
                # In production, would use forward/backward pass
                slack_times[task_id] = self._calculate_task_slack(
                    task_id, critical_path
                )

        return slack_times

    def _calculate_task_slack(self, task_id: str, critical_path: List[str]) -> float:
        """Calculate slack time for a specific task."""
        # Simplified calculation - would be more sophisticated in production

        # Find parallel paths and estimate slack
        paths_through_task = list(
            nx.all_simple_paths(self.graph, list(self.graph.nodes())[0], task_id)
        )

        if paths_through_task:
            max_path_duration = max(
                sum(self.graph.nodes[node]["duration"] for node in path)
                for path in paths_through_task
            )

            critical_path_duration = sum(
                self.graph.nodes[node]["duration"] for node in critical_path
            )

            return max(0.0, critical_path_duration - max_path_duration)

        return 0.0

    def identify_bottlenecks(self) -> List[str]:
        """Identify potential bottleneck tasks."""
        bottlenecks = []

        for task_id in self.graph.nodes():
            # Tasks with many dependencies coming in/out
            in_degree = self.graph.in_degree(task_id)
            out_degree = self.graph.out_degree(task_id)

            # High-duration tasks
            duration = self.graph.nodes[task_id]["duration"]

            if (in_degree > 2 or out_degree > 2) and duration > 4:  # 4+ hours
                bottlenecks.append(task_id)

        return bottlenecks


class ResourceOptimizer:
    """Optimizes resource allocation for tasks."""

    def __init__(self, available_resources: List[Resource]):
        self.available_resources = available_resources
        self.resource_usage_timeline = {}

    def optimize_resource_allocation(
        self, tasks: List[ScheduledTask], strategy: SchedulingStrategy
    ) -> Dict[str, List[Resource]]:
        """Optimize resource allocation based on strategy."""
        allocation = {}

        # Sort tasks by priority and dependencies
        sorted_tasks = self._sort_tasks_for_allocation(tasks, strategy)

        for task in sorted_tasks:
            allocated_resources = self._allocate_resources_for_task(task, strategy)
            allocation[task.task_id] = allocated_resources
            task.assigned_resources = allocated_resources

        return allocation

    def _sort_tasks_for_allocation(
        self, tasks: List[ScheduledTask], strategy: SchedulingStrategy
    ) -> List[ScheduledTask]:
        """Sort tasks based on allocation strategy."""
        if strategy == SchedulingStrategy.PRIORITIZE_CRITICAL:
            return sorted(tasks, key=lambda t: (-t.criticality_score, -t.priority))
        elif strategy == SchedulingStrategy.MINIMIZE_DURATION:
            return sorted(tasks, key=lambda t: -t.estimated_duration)
        elif strategy == SchedulingStrategy.BALANCE_RESOURCES:
            return sorted(tasks, key=lambda t: sum(t.resource_requirements.values()))
        else:
            return sorted(tasks, key=lambda t: -t.priority)

    def _allocate_resources_for_task(
        self, task: ScheduledTask, strategy: SchedulingStrategy
    ) -> List[Resource]:
        """Allocate resources for a specific task."""
        allocated = []

        for resource_type, required_amount in task.resource_requirements.items():
            suitable_resources = [
                r
                for r in self.available_resources
                if r.resource_type == resource_type
                and r.capacity - r.current_usage >= required_amount
            ]

            if not suitable_resources:
                logger.warning(
                    f"No suitable {resource_type} resources for task {task.task_id}"
                )
                continue

            # Select best resource based on strategy
            if strategy == SchedulingStrategy.MINIMIZE_COST:
                best_resource = min(suitable_resources, key=lambda r: r.cost_per_hour)
            else:
                # Default to least utilized
                best_resource = min(
                    suitable_resources, key=lambda r: r.current_usage / r.capacity
                )

            # Allocate resource
            best_resource.current_usage += required_amount
            allocated.append(best_resource)

        return allocated

    def calculate_resource_utilization(
        self, allocation: Dict[str, List[Resource]]
    ) -> Dict[str, float]:
        """Calculate resource utilization metrics."""
        utilization = {}

        for resource in self.available_resources:
            utilization[resource.resource_id] = (
                resource.current_usage / resource.capacity
            )

        return utilization

    def estimate_cost(
        self, allocation: Dict[str, List[Resource]], total_duration: float
    ) -> float:
        """Estimate total cost of resource allocation."""
        total_cost = 0.0

        for task_id, resources in allocation.items():
            for resource in resources:
                # Cost = resource usage * cost per hour * duration
                usage_ratio = resource.current_usage / resource.capacity
                task_cost = usage_ratio * resource.cost_per_hour * total_duration
                total_cost += task_cost

        return total_cost


class GeneticAlgorithmOptimizer:
    """Genetic algorithm for advanced scheduling optimization."""

    def __init__(self, population_size: int = 50, generations: int = 100):
        self.population_size = population_size
        self.generations = generations
        self.mutation_rate = 0.1
        self.crossover_rate = 0.8

    def optimize_schedule(
        self,
        tasks: List[ScheduledTask],
        constraints: Dict[str, Any],
        objective: SchedulingStrategy,
    ) -> List[str]:
        """Optimize task schedule using genetic algorithm."""
        logger.info(
            f"Starting genetic algorithm optimization with {self.population_size} individuals"
        )

        # Initialize population
        population = self._initialize_population(tasks)

        best_fitness = float("-inf")
        best_individual = None

        for generation in range(self.generations):
            # Evaluate fitness
            fitness_scores = []
            for individual in population:
                fitness = self._evaluate_fitness(
                    individual, tasks, constraints, objective
                )
                fitness_scores.append(fitness)

                if fitness > best_fitness:
                    best_fitness = fitness
                    best_individual = individual.copy()

            # Selection, crossover, and mutation
            population = self._evolve_population(population, fitness_scores)

            if generation % 20 == 0:
                logger.info(
                    f"Generation {generation}: Best fitness = {best_fitness:.4f}"
                )

        logger.info(f"Genetic algorithm completed. Best fitness: {best_fitness:.4f}")
        return best_individual if best_individual else tasks[0].task_id

    def _initialize_population(self, tasks: List[ScheduledTask]) -> List[List[str]]:
        """Initialize random population of task orderings."""
        population = []
        task_ids = [task.task_id for task in tasks]

        for _ in range(self.population_size):
            individual = task_ids.copy()
            random.shuffle(individual)
            population.append(individual)

        return population

    def _evaluate_fitness(
        self,
        individual: List[str],
        tasks: List[ScheduledTask],
        constraints: Dict[str, Any],
        objective: SchedulingStrategy,
    ) -> float:
        """Evaluate fitness of an individual schedule."""
        # Simplified fitness calculation
        fitness = 0.0

        # Penalty for dependency violations
        dependency_penalty = self._calculate_dependency_penalty(individual, tasks)
        fitness -= dependency_penalty * 100

        # Reward based on objective
        if objective == SchedulingStrategy.MINIMIZE_DURATION:
            # Reward shorter overall duration
            estimated_duration = self._estimate_schedule_duration(individual, tasks)
            fitness += 1000 / max(estimated_duration, 1)

        elif objective == SchedulingStrategy.MAXIMIZE_PARALLELISM:
            # Reward better parallelization
            parallelism_score = self._calculate_parallelism_score(individual, tasks)
            fitness += parallelism_score * 50

        return fitness

    def _calculate_dependency_penalty(
        self, individual: List[str], tasks: List[ScheduledTask]
    ) -> float:
        """Calculate penalty for dependency violations."""
        penalty = 0.0
        task_positions = {task_id: i for i, task_id in enumerate(individual)}

        for task in tasks:
            task_pos = task_positions[task.task_id]

            for dep in task.dependencies:
                if dep.predecessor in task_positions:
                    pred_pos = task_positions[dep.predecessor]

                    # Dependency violation if predecessor comes after successor
                    if pred_pos >= task_pos:
                        penalty += 1.0

        return penalty

    def _estimate_schedule_duration(
        self, individual: List[str], tasks: List[ScheduledTask]
    ) -> float:
        """Estimate total duration of schedule."""
        # Simplified estimation - parallel tasks could overlap
        task_dict = {task.task_id: task for task in tasks}

        total_duration = 0.0
        for task_id in individual:
            if task_id in task_dict:
                total_duration += task_dict[task_id].estimated_duration

        # Apply parallelization factor (rough estimate)
        parallelization_factor = min(len(individual) / 4, 4)  # Max 4x speedup
        return total_duration / parallelization_factor

    def _calculate_parallelism_score(
        self, individual: List[str], tasks: List[ScheduledTask]
    ) -> float:
        """Calculate how well the schedule enables parallelism."""
        # Simplified - measures task independence
        task_dict = {task.task_id: task for task in tasks}

        independent_tasks = 0
        for i, task_id in enumerate(individual):
            task = task_dict.get(task_id)
            if task and len(task.dependencies) == 0:
                # Independent tasks early in schedule are good for parallelism
                score = (len(individual) - i) / len(individual)
                independent_tasks += score

        return independent_tasks / len(individual)

    def _evolve_population(
        self, population: List[List[str]], fitness_scores: List[float]
    ) -> List[List[str]]:
        """Evolve population through selection, crossover, and mutation."""
        new_population = []

        # Sort by fitness
        sorted_indices = sorted(
            range(len(fitness_scores)), key=lambda i: fitness_scores[i], reverse=True
        )

        # Elitism - keep top 20%
        elite_count = max(1, self.population_size // 5)
        for i in range(elite_count):
            new_population.append(population[sorted_indices[i]].copy())

        # Generate rest through crossover and mutation
        while len(new_population) < self.population_size:
            # Tournament selection
            parent1 = self._tournament_selection(population, fitness_scores)
            parent2 = self._tournament_selection(population, fitness_scores)

            # Crossover
            if random.random() < self.crossover_rate:
                child1, child2 = self._crossover(parent1, parent2)
            else:
                child1, child2 = parent1.copy(), parent2.copy()

            # Mutation
            if random.random() < self.mutation_rate:
                child1 = self._mutate(child1)
            if random.random() < self.mutation_rate:
                child2 = self._mutate(child2)

            new_population.extend([child1, child2])

        return new_population[: self.population_size]

    def _tournament_selection(
        self,
        population: List[List[str]],
        fitness_scores: List[float],
        tournament_size: int = 3,
    ) -> List[str]:
        """Select individual using tournament selection."""
        tournament_indices = random.sample(range(len(population)), tournament_size)
        best_index = max(tournament_indices, key=lambda i: fitness_scores[i])
        return population[best_index].copy()

    def _crossover(
        self, parent1: List[str], parent2: List[str]
    ) -> Tuple[List[str], List[str]]:
        """Order crossover for preserving task uniqueness."""
        size = len(parent1)
        start, end = sorted(random.sample(range(size), 2))

        child1 = [None] * size
        child2 = [None] * size

        # Copy segment from parent1 to child1
        child1[start:end] = parent1[start:end]

        # Fill remaining positions from parent2
        remaining = [item for item in parent2 if item not in child1[start:end]]
        j = 0
        for i in range(size):
            if child1[i] is None:
                child1[i] = remaining[j]
                j += 1

        # Similar for child2
        child2[start:end] = parent2[start:end]
        remaining = [item for item in parent1 if item not in child2[start:end]]
        j = 0
        for i in range(size):
            if child2[i] is None:
                child2[i] = remaining[j]
                j += 1

        return child1, child2

    def _mutate(self, individual: List[str]) -> List[str]:
        """Swap mutation - swap two random positions."""
        mutated = individual.copy()
        if len(mutated) > 1:
            i, j = random.sample(range(len(mutated)), 2)
            mutated[i], mutated[j] = mutated[j], mutated[i]
        return mutated


class IntelligentScheduler:
    """Main intelligent scheduler with dependency-aware optimization."""

    def __init__(self, available_resources: List[Resource] = None):
        self.dependency_analyzer = DependencyGraphAnalyzer()
        self.resource_optimizer = ResourceOptimizer(available_resources or [])
        self.genetic_optimizer = GeneticAlgorithmOptimizer()

        # Default resources if none provided
        if not available_resources:
            self.resource_optimizer.available_resources = (
                self._create_default_resources()
            )

    def _create_default_resources(self) -> List[Resource]:
        """Create default resource pool."""
        return [
            Resource("cpu-1", "cpu", 8.0, 0.1),  # 8 cores, $0.1/hour
            Resource("cpu-2", "cpu", 8.0, 0.1),
            Resource("memory-1", "memory", 32.0, 0.05),  # 32GB, $0.05/hour
            Resource("memory-2", "memory", 32.0, 0.05),
            Resource("gpu-1", "gpu", 1.0, 2.0),  # 1 GPU, $2/hour
        ]

    async def optimize_task_scheduling(
        self,
        task_list: List[Task],
        constraints: Dict[str, Any] = None,
        objective: SchedulingStrategy = SchedulingStrategy.MINIMIZE_DURATION,
    ) -> SchedulingPlan:
        """Optimize task scheduling with dependency awareness and resource allocation."""
        logger.info(f"Starting intelligent scheduling for {len(task_list)} tasks")

        # Convert tasks to scheduled tasks
        scheduled_tasks = await self._prepare_scheduled_tasks(task_list)

        # Build dependency graph
        dependency_graph = self.dependency_analyzer.build_dependency_graph(
            scheduled_tasks
        )

        # Calculate critical path
        critical_path = self.dependency_analyzer.calculate_critical_path()

        # Calculate criticality scores
        await self._calculate_criticality_scores(scheduled_tasks, critical_path)

        # Optimize task order using genetic algorithm
        if len(scheduled_tasks) > 10:  # Use GA for complex schedules
            optimized_order = self.genetic_optimizer.optimize_schedule(
                scheduled_tasks, constraints or {}, objective
            )
        else:
            # Simple topological sort for small schedules
            optimized_order = list(nx.topological_sort(dependency_graph))

        # Optimize resource allocation
        resource_allocation = self.resource_optimizer.optimize_resource_allocation(
            scheduled_tasks, objective
        )

        # Calculate timing
        total_duration = await self._calculate_schedule_timing(
            scheduled_tasks, optimized_order
        )

        # Calculate metrics
        parallel_efficiency = self._calculate_parallel_efficiency(
            scheduled_tasks, total_duration
        )
        resource_utilization = self.resource_optimizer.calculate_resource_utilization(
            resource_allocation
        )
        estimated_cost = self.resource_optimizer.estimate_cost(
            resource_allocation, total_duration
        )

        # Calculate optimization score
        optimization_score = self._calculate_optimization_score(
            total_duration, parallel_efficiency, resource_utilization, objective
        )

        # Generate warnings
        warnings = self._generate_scheduling_warnings(
            scheduled_tasks, resource_utilization
        )

        plan_id = f"schedule-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"

        scheduling_plan = SchedulingPlan(
            plan_id=plan_id,
            tasks=scheduled_tasks,
            total_duration=total_duration,
            critical_path=critical_path,
            resource_allocation=resource_allocation,
            optimization_objective=objective.value,
            optimization_score=optimization_score,
            parallel_efficiency=parallel_efficiency,
            resource_utilization=resource_utilization,
            estimated_cost=estimated_cost,
            constraints_satisfied=len(warnings) == 0,
            warnings=warnings,
        )

        logger.info(
            f"Scheduling completed: {total_duration:.1f}h duration, {optimization_score:.2f} score"
        )

        return scheduling_plan

    async def _prepare_scheduled_tasks(self, tasks: List[Task]) -> List[ScheduledTask]:
        """Convert tasks to scheduled tasks with dependencies and estimates."""
        scheduled_tasks = []

        for task in tasks:
            # Extract dependencies from task description or metadata
            dependencies = self._extract_dependencies(task)

            # Estimate duration and resources
            estimated_duration = self._estimate_task_duration(task)
            resource_requirements = self._estimate_resource_requirements(task)

            # Determine priority
            priority = self._calculate_task_priority(task)

            scheduled_task = ScheduledTask(
                task_id=task.id,
                task=task,
                dependencies=dependencies,
                estimated_duration=estimated_duration,
                resource_requirements=resource_requirements,
                priority=priority,
            )

            scheduled_tasks.append(scheduled_task)

        return scheduled_tasks

    def _extract_dependencies(self, task: Task) -> List[TaskDependency]:
        """Extract task dependencies from task metadata or description."""
        dependencies = []

        # Check task metadata for explicit dependencies
        if hasattr(task, "metadata") and task.metadata:
            if "dependencies" in task.metadata:
                for dep_info in task.metadata["dependencies"]:
                    dependency = TaskDependency(
                        predecessor=dep_info.get("predecessor"),
                        successor=task.id,
                        dependency_type=dep_info.get("type", "finish_to_start"),
                        lag_time=dep_info.get("lag_time", 0.0),
                    )
                    dependencies.append(dependency)

        # Extract implicit dependencies from description
        description = task.description.lower()

        # Look for dependency keywords
        if "after" in description or "depends on" in description:
            # This would be more sophisticated in production
            # For now, create a simple dependency pattern
            pass

        return dependencies

    def _estimate_task_duration(self, task: Task) -> float:
        """Estimate task duration based on complexity indicators."""
        base_duration = 4.0  # 4 hours default

        description = task.description.lower()

        # Duration multipliers based on keywords
        complexity_keywords = {
            "simple": 0.5,
            "quick": 0.3,
            "complex": 2.0,
            "difficult": 1.8,
            "research": 2.5,
            "analysis": 1.5,
            "implementation": 1.2,
            "testing": 0.8,
            "review": 0.6,
            "documentation": 0.4,
        }

        multiplier = 1.0
        for keyword, factor in complexity_keywords.items():
            if keyword in description:
                multiplier *= factor

        # Consider description length
        if len(task.description) > 500:
            multiplier *= 1.3
        elif len(task.description) < 100:
            multiplier *= 0.8

        return base_duration * multiplier

    def _estimate_resource_requirements(self, task: Task) -> Dict[str, float]:
        """Estimate resource requirements for task."""
        requirements = {
            "cpu": 2.0,  # 2 CPU cores
            "memory": 4.0,  # 4GB RAM
        }

        description = task.description.lower()

        # Adjust based on task type
        if any(keyword in description for keyword in ["ml", "ai", "model", "training"]):
            requirements["gpu"] = 1.0
            requirements["memory"] = 16.0
            requirements["cpu"] = 4.0

        elif any(
            keyword in description for keyword in ["data", "analysis", "processing"]
        ):
            requirements["memory"] = 8.0
            requirements["cpu"] = 4.0

        elif any(keyword in description for keyword in ["compile", "build", "test"]):
            requirements["cpu"] = 6.0
            requirements["memory"] = 8.0

        return requirements

    def _calculate_task_priority(self, task: Task) -> int:
        """Calculate task priority (1-10, higher is more important)."""
        base_priority = 5

        if hasattr(task, "priority"):
            priority_map = {
                "low": 3,
                "medium": 5,
                "high": 7,
                "urgent": 9,
                "critical": 10,
            }
            base_priority = priority_map.get(task.priority.lower(), 5)

        # Adjust based on description keywords
        description = task.description.lower()

        if any(
            keyword in description for keyword in ["critical", "urgent", "important"]
        ):
            base_priority = min(10, base_priority + 2)
        elif any(keyword in description for keyword in ["optional", "nice to have"]):
            base_priority = max(1, base_priority - 2)

        return base_priority

    async def _calculate_criticality_scores(
        self, tasks: List[ScheduledTask], critical_path: List[str]
    ):
        """Calculate criticality scores for all tasks."""
        slack_times = self.dependency_analyzer.calculate_slack_times(critical_path)

        for task in tasks:
            # Base criticality from critical path membership
            if task.task_id in critical_path:
                task.criticality_score = 1.0
            else:
                # Inverse of slack time (normalized)
                slack = slack_times.get(task.task_id, 8.0)  # Default 8 hours slack
                task.criticality_score = max(0.1, 1.0 / (1.0 + slack))

            # Adjust for priority and dependencies
            task.criticality_score *= task.priority / 10.0
            task.criticality_score *= 1.0 + len(task.dependencies) * 0.1

    async def _calculate_schedule_timing(
        self, tasks: List[ScheduledTask], optimized_order: List[str]
    ) -> float:
        """Calculate schedule timing with parallel execution consideration."""
        task_dict = {task.task_id: task for task in tasks}

        # Simple parallel scheduling simulation
        current_time = 0.0
        resource_availability = {
            resource.resource_id: 0.0  # Time when resource becomes available
            for resource in self.resource_optimizer.available_resources
        }

        for task_id in optimized_order:
            if task_id not in task_dict:
                continue

            task = task_dict[task_id]

            # Find earliest start time considering dependencies and resources
            earliest_start = current_time

            # Check dependency constraints
            for dep in task.dependencies:
                if dep.predecessor in task_dict:
                    pred_task = task_dict[dep.predecessor]
                    if pred_task.scheduled_finish:
                        earliest_start = max(
                            earliest_start, pred_task.scheduled_finish + dep.lag_time
                        )

            # Check resource availability
            if task.assigned_resources:
                resource_ready_time = max(
                    resource_availability.get(res.resource_id, 0.0)
                    for res in task.assigned_resources
                )
                earliest_start = max(earliest_start, resource_ready_time)

            # Schedule task
            task.scheduled_start = datetime.utcnow() + timedelta(hours=earliest_start)
            task.scheduled_finish = datetime.utcnow() + timedelta(
                hours=earliest_start + task.estimated_duration
            )

            # Update resource availability
            for resource in task.assigned_resources:
                resource_availability[resource.resource_id] = (
                    earliest_start + task.estimated_duration
                )

        # Total duration is the latest finish time
        if tasks:
            finish_times = [
                (task.scheduled_finish - datetime.utcnow()).total_seconds() / 3600
                for task in tasks
                if task.scheduled_finish
            ]
            return max(finish_times) if finish_times else 0.0

        return 0.0

    def _calculate_parallel_efficiency(
        self, tasks: List[ScheduledTask], total_duration: float
    ) -> float:
        """Calculate how efficiently the schedule uses parallelism."""
        if not tasks or total_duration == 0:
            return 0.0

        # Sequential execution time
        sequential_time = sum(task.estimated_duration for task in tasks)

        # Efficiency = sequential_time / (total_duration * max_parallel_tasks)
        max_parallel = min(len(tasks), len(self.resource_optimizer.available_resources))
        theoretical_minimum = sequential_time / max_parallel

        efficiency = theoretical_minimum / total_duration
        return min(1.0, efficiency)

    def _calculate_optimization_score(
        self,
        total_duration: float,
        parallel_efficiency: float,
        resource_utilization: Dict[str, float],
        objective: SchedulingStrategy,
    ) -> float:
        """Calculate overall optimization score."""
        score = 0.0

        if objective == SchedulingStrategy.MINIMIZE_DURATION:
            # Higher score for shorter duration
            score += (100.0 / max(total_duration, 1.0)) * 0.4
            score += parallel_efficiency * 0.4
            score += np.mean(list(resource_utilization.values())) * 0.2

        elif objective == SchedulingStrategy.MAXIMIZE_PARALLELISM:
            score += parallel_efficiency * 0.6
            score += np.mean(list(resource_utilization.values())) * 0.3
            score += (50.0 / max(total_duration, 1.0)) * 0.1

        elif objective == SchedulingStrategy.BALANCE_RESOURCES:
            # Reward balanced resource usage
            utilization_variance = np.var(list(resource_utilization.values()))
            score += (1.0 / (1.0 + utilization_variance)) * 0.5
            score += np.mean(list(resource_utilization.values())) * 0.3
            score += parallel_efficiency * 0.2

        return min(100.0, max(0.0, score))

    def _generate_scheduling_warnings(
        self, tasks: List[ScheduledTask], resource_utilization: Dict[str, float]
    ) -> List[str]:
        """Generate warnings about potential scheduling issues."""
        warnings = []

        # Check for over-utilized resources
        for resource_id, utilization in resource_utilization.items():
            if utilization > 0.9:
                warnings.append(
                    f"Resource {resource_id} is over-utilized ({utilization:.1%})"
                )

        # Check for under-utilized resources
        underutilized = [
            r_id for r_id, util in resource_utilization.items() if util < 0.3
        ]
        if len(underutilized) > len(resource_utilization) / 2:
            warnings.append(
                "Many resources are under-utilized - consider reducing resource allocation"
            )

        # Check for long critical path
        critical_tasks = [task for task in tasks if task.criticality_score > 0.8]
        if len(critical_tasks) > len(tasks) * 0.7:
            warnings.append(
                "Many tasks are on or near critical path - schedule has limited flexibility"
            )

        # Check for resource conflicts
        high_resource_tasks = [
            task for task in tasks if sum(task.resource_requirements.values()) > 10
        ]
        if len(high_resource_tasks) > 3:
            warnings.append(
                "Multiple high-resource tasks may cause scheduling conflicts"
            )

        return warnings
