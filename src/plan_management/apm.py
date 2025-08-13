"""
Plan Management Application Performance Monitoring (APM) implementation.
Provides comprehensive performance monitoring for plan creation, task management, and consensus operations.
"""

import logging
import time
from typing import Dict, Any, Optional, List
from contextlib import asynccontextmanager
from dataclasses import dataclass
from enum import Enum
from collections import defaultdict
import statistics

from opentelemetry.trace import Status, StatusCode

from src.common.apm import (
    APMOperationType, 
    APMConfig, 
    get_apm
)
from src.common.tracing import get_tracing_config

logger = logging.getLogger(__name__)


class PlanManagementOperationType(Enum):
    """Plan Management specific operation types."""
    PLAN_CREATION = "plan_creation"
    TASK_DECOMPOSITION = "task_decomposition"
    CONSENSUS_BUILDING = "consensus_building"
    PLAN_VALIDATION = "plan_validation"
    PLAN_ESTIMATION = "plan_estimation"
    TASK_CREATION = "task_creation"
    TASK_COMPLETION = "task_completion"
    MILESTONE_CREATION = "milestone_creation"
    PLAN_STORAGE = "plan_storage"
    PLAN_RETRIEVAL = "plan_retrieval"
    PLAN_UPDATE = "plan_update"


@dataclass
class PlanPerformanceMetrics:
    """Plan-specific performance metrics."""
    plan_id: str
    creation_duration: float = 0.0
    task_count: int = 0
    completed_tasks: int = 0
    total_estimated_duration: float = 0.0
    actual_duration: float = 0.0
    consensus_duration: float = 0.0
    validation_duration: float = 0.0
    storage_operations: int = 0
    last_updated: float = 0.0
    
    @property
    def completion_rate(self) -> float:
        """Calculate task completion rate."""
        if self.task_count == 0:
            return 0.0
        return self.completed_tasks / self.task_count
    
    @property
    def duration_accuracy(self) -> float:
        """Calculate duration estimation accuracy."""
        if self.total_estimated_duration == 0:
            return 0.0
        return min(1.0, self.total_estimated_duration / max(self.actual_duration, 0.001))


@dataclass
class TaskPerformanceMetrics:
    """Task-specific performance metrics."""
    task_id: str
    plan_id: str
    creation_duration: float = 0.0
    execution_duration: float = 0.0
    completion_duration: float = 0.0
    estimated_duration: float = 0.0
    actual_duration: float = 0.0
    complexity_score: float = 0.0
    dependencies_count: int = 0
    success: bool = True
    error_message: Optional[str] = None
    
    @property
    def duration_accuracy(self) -> float:
        """Calculate duration estimation accuracy."""
        if self.estimated_duration == 0:
            return 0.0
        return min(1.0, self.estimated_duration / max(self.actual_duration, 0.001))


@dataclass
class ConsensusMetrics:
    """Consensus building metrics."""
    consensus_id: str
    plan_id: str
    participant_count: int
    duration: float
    success: bool
    rounds_count: int
    agreement_score: float
    conflict_count: int
    resolution_duration: float
    strategy_used: str


class PlanManagementAPM:
    """APM implementation for Plan Management service."""
    
    def __init__(self, config: APMConfig = None):
        """Initialize Plan Management APM."""
        self.config = config or APMConfig()
        self.apm = get_apm()
        self.tracer = get_tracing_config().get_tracer()
        self.meter = get_tracing_config().get_meter()
        
        # Performance tracking
        self.plan_metrics = defaultdict(lambda: PlanPerformanceMetrics(plan_id=""))
        self.task_metrics = defaultdict(lambda: TaskPerformanceMetrics(task_id="", plan_id=""))
        self.consensus_metrics = []
        
        # Initialize metrics
        self._initialize_metrics()
        
        # Performance thresholds
        self.slow_plan_creation_threshold = 30.0  # seconds
        self.slow_consensus_threshold = 60.0  # seconds
        self.low_consensus_threshold = 0.7  # 70%
        self.high_conflict_threshold = 5  # conflicts
        
        # History limits
        self.max_consensus_history = 1000
    
    def _initialize_metrics(self):
        """Initialize OpenTelemetry metrics for Plan Management."""
        # Counters
        self.plan_creation_counter = self.meter.create_counter(
            "plan_management_plans_created_total",
            description="Total number of plans created"
        )
        
        self.task_creation_counter = self.meter.create_counter(
            "plan_management_tasks_created_total",
            description="Total number of tasks created"
        )
        
        self.task_completion_counter = self.meter.create_counter(
            "plan_management_tasks_completed_total",
            description="Total number of tasks completed"
        )
        
        self.consensus_operations_counter = self.meter.create_counter(
            "plan_management_consensus_operations_total",
            description="Total number of consensus operations"
        )
        
        self.validation_operations_counter = self.meter.create_counter(
            "plan_management_validation_operations_total",
            description="Total number of validation operations"
        )
        
        self.storage_operations_counter = self.meter.create_counter(
            "plan_management_storage_operations_total",
            description="Total number of storage operations"
        )
        
        # Histograms
        self.plan_creation_duration = self.meter.create_histogram(
            "plan_management_plan_creation_duration_seconds",
            description="Duration of plan creation operations"
        )
        
        self.task_decomposition_duration = self.meter.create_histogram(
            "plan_management_task_decomposition_duration_seconds",
            description="Duration of task decomposition operations"
        )
        
        self.consensus_duration = self.meter.create_histogram(
            "plan_management_consensus_duration_seconds",
            description="Duration of consensus building operations"
        )
        
        self.validation_duration = self.meter.create_histogram(
            "plan_management_validation_duration_seconds",
            description="Duration of validation operations"
        )
        
        self.task_execution_duration = self.meter.create_histogram(
            "plan_management_task_execution_duration_seconds",
            description="Duration of task execution operations"
        )
        
        # Gauges
        self.active_plans_gauge = self.meter.create_up_down_counter(
            "plan_management_active_plans",
            description="Number of currently active plans"
        )
        
        self.active_tasks_gauge = self.meter.create_up_down_counter(
            "plan_management_active_tasks",
            description="Number of currently active tasks"
        )
        
        self.consensus_participants_gauge = self.meter.create_up_down_counter(
            "plan_management_consensus_participants",
            description="Number of participants in consensus operations"
        )
    
    @asynccontextmanager
    async def trace_plan_creation(self, plan_title: str, task_count: int = 0,
                                complexity: str = "medium"):
        """Trace plan creation process."""
        operation_name = "create_plan"
        attributes = {
            "plan_management.plan_title": plan_title,
            "plan_management.task_count": task_count,
            "plan_management.complexity": complexity
        }
        
        start_time = time.time()
        success = True
        error_message = None
        plan_id = None
        
        async with self.apm.trace_async_operation(
            operation_name, APMOperationType.BUSINESS_TRANSACTION, attributes
        ) as span:
            try:
                yield span
            except Exception as e:
                success = False
                error_message = str(e)
                span.set_status(Status(StatusCode.ERROR, error_message))
                span.record_exception(e)
                raise
            finally:
                end_time = time.time()
                duration = end_time - start_time
                
                # Record plan metrics
                if plan_id:
                    plan_metrics = self.plan_metrics[plan_id]
                    plan_metrics.plan_id = plan_id
                    plan_metrics.creation_duration = duration
                    plan_metrics.task_count = task_count
                    plan_metrics.last_updated = end_time
                
                # Update metrics
                self.plan_creation_counter.add(1, {"success": success})
                self.plan_creation_duration.record(duration, {"complexity": complexity})
    
    @asynccontextmanager
    async def trace_task_decomposition(self, plan_id: str, input_text: str,
                                     complexity: str = "medium"):
        """Trace task decomposition process."""
        operation_name = "task_decomposition"
        attributes = {
            "plan_management.plan_id": plan_id,
            "plan_management.input_length": len(input_text),
            "plan_management.complexity": complexity
        }
        
        start_time = time.time()
        success = True
        error_message = None
        task_count = 0
        
        async with self.apm.trace_async_operation(
            operation_name, APMOperationType.CPU_INTENSIVE, attributes
        ) as span:
            try:
                yield span
            except Exception as e:
                success = False
                error_message = str(e)
                span.set_status(Status(StatusCode.ERROR, error_message))
                span.record_exception(e)
                raise
            finally:
                end_time = time.time()
                duration = end_time - start_time
                
                # Update plan metrics
                if plan_id in self.plan_metrics:
                    plan_metrics = self.plan_metrics[plan_id]
                    plan_metrics.task_count = task_count
                    plan_metrics.last_updated = end_time
                
                # Update metrics
                self.task_decomposition_duration.record(duration, {
                    "plan_id": plan_id,
                    "complexity": complexity
                })
    
    @asynccontextmanager
    async def trace_consensus_building(self, plan_id: str, participant_count: int,
                                     strategy: str = "voting"):
        """Trace consensus building process."""
        operation_name = "consensus_building"
        attributes = {
            "plan_management.plan_id": plan_id,
            "plan_management.participant_count": participant_count,
            "plan_management.strategy": strategy
        }
        
        start_time = time.time()
        success = True
        error_message = None
        consensus_id = None
        rounds_count = 0
        agreement_score = 0.0
        conflict_count = 0
        
        async with self.apm.trace_async_operation(
            operation_name, APMOperationType.BUSINESS_TRANSACTION, attributes
        ) as span:
            try:
                yield span
            except Exception as e:
                success = False
                error_message = str(e)
                span.set_status(Status(StatusCode.ERROR, error_message))
                span.record_exception(e)
                raise
            finally:
                end_time = time.time()
                duration = end_time - start_time
                
                # Record consensus metrics
                if consensus_id:
                    consensus_metrics = ConsensusMetrics(
                        consensus_id=consensus_id,
                        plan_id=plan_id,
                        participant_count=participant_count,
                        duration=duration,
                        success=success,
                        rounds_count=rounds_count,
                        agreement_score=agreement_score,
                        conflict_count=conflict_count,
                        resolution_duration=duration,
                        strategy_used=strategy
                    )
                    self.consensus_metrics.append(consensus_metrics)
                    
                    # Keep only recent consensus data
                    if len(self.consensus_metrics) > self.max_consensus_history:
                        self.consensus_metrics.pop(0)
                
                # Update plan metrics
                if plan_id in self.plan_metrics:
                    plan_metrics = self.plan_metrics[plan_id]
                    plan_metrics.consensus_duration = duration
                    plan_metrics.last_updated = end_time
                
                # Update metrics
                self.consensus_operations_counter.add(1, {
                    "plan_id": plan_id,
                    "strategy": strategy,
                    "success": success
                })
                
                self.consensus_duration.record(duration, {
                    "plan_id": plan_id,
                    "strategy": strategy
                })
    
    @asynccontextmanager
    async def trace_plan_validation(self, plan_id: str, validation_type: str = "completeness"):
        """Trace plan validation process."""
        operation_name = "plan_validation"
        attributes = {
            "plan_management.plan_id": plan_id,
            "plan_management.validation_type": validation_type
        }
        
        start_time = time.time()
        success = True
        error_message = None
        
        async with self.apm.trace_async_operation(
            operation_name, APMOperationType.CPU_INTENSIVE, attributes
        ) as span:
            try:
                yield span
            except Exception as e:
                success = False
                error_message = str(e)
                span.set_status(Status(StatusCode.ERROR, error_message))
                span.record_exception(e)
                raise
            finally:
                end_time = time.time()
                duration = end_time - start_time
                
                # Update plan metrics
                if plan_id in self.plan_metrics:
                    plan_metrics = self.plan_metrics[plan_id]
                    plan_metrics.validation_duration = duration
                    plan_metrics.last_updated = end_time
                
                # Update metrics
                self.validation_operations_counter.add(1, {
                    "plan_id": plan_id,
                    "validation_type": validation_type,
                    "success": success
                })
                
                self.validation_duration.record(duration, {
                    "plan_id": plan_id,
                    "validation_type": validation_type
                })
    
    @asynccontextmanager
    async def trace_plan_estimation(self, plan_id: str, estimation_method: str = "expert"):
        """Trace plan estimation process."""
        operation_name = "plan_estimation"
        attributes = {
            "plan_management.plan_id": plan_id,
            "plan_management.estimation_method": estimation_method
        }
        
        start_time = time.time()
        success = True
        error_message = None
        total_estimated_duration = 0.0
        
        async with self.apm.trace_async_operation(
            operation_name, APMOperationType.CPU_INTENSIVE, attributes
        ) as span:
            try:
                yield span
            except Exception as e:
                success = False
                error_message = str(e)
                span.set_status(Status(StatusCode.ERROR, error_message))
                span.record_exception(e)
                raise
            finally:
                end_time = time.time()
                duration = end_time - start_time
                
                # Update plan metrics
                if plan_id in self.plan_metrics:
                    plan_metrics = self.plan_metrics[plan_id]
                    plan_metrics.total_estimated_duration = total_estimated_duration
                    plan_metrics.last_updated = end_time
                
                # Update metrics
                self.plan_creation_duration.record(duration, {
                    "plan_id": plan_id,
                    "operation": "estimation"
                })
    
    @asynccontextmanager
    async def trace_task_creation(self, plan_id: str, task_title: str,
                                estimated_duration: float = 0.0,
                                complexity_score: float = 0.0):
        """Trace task creation process."""
        operation_name = "create_task"
        attributes = {
            "plan_management.plan_id": plan_id,
            "plan_management.task_title": task_title,
            "plan_management.estimated_duration": estimated_duration,
            "plan_management.complexity_score": complexity_score
        }
        
        start_time = time.time()
        success = True
        error_message = None
        task_id = None
        
        async with self.apm.trace_async_operation(
            operation_name, APMOperationType.CPU_INTENSIVE, attributes
        ) as span:
            try:
                yield span
            except Exception as e:
                success = False
                error_message = str(e)
                span.set_status(Status(StatusCode.ERROR, error_message))
                span.record_exception(e)
                raise
            finally:
                end_time = time.time()
                duration = end_time - start_time
                
                # Record task metrics
                if task_id:
                    task_metrics = self.task_metrics[task_id]
                    task_metrics.task_id = task_id
                    task_metrics.plan_id = plan_id
                    task_metrics.creation_duration = duration
                    task_metrics.estimated_duration = estimated_duration
                    task_metrics.complexity_score = complexity_score
                
                # Update metrics
                self.task_creation_counter.add(1, {
                    "plan_id": plan_id,
                    "success": success
                })
                
                self.task_execution_duration.record(duration, {
                    "plan_id": plan_id,
                    "operation": "creation"
                })
    
    @asynccontextmanager
    async def trace_task_execution(self, task_id: str, plan_id: str):
        """Trace task execution process."""
        operation_name = "execute_task"
        attributes = {
            "plan_management.task_id": task_id,
            "plan_management.plan_id": plan_id
        }
        
        start_time = time.time()
        success = True
        error_message = None
        
        async with self.apm.trace_async_operation(
            operation_name, APMOperationType.BUSINESS_TRANSACTION, attributes
        ) as span:
            try:
                yield span
            except Exception as e:
                success = False
                error_message = str(e)
                span.set_status(Status(StatusCode.ERROR, error_message))
                span.record_exception(e)
                raise
            finally:
                end_time = time.time()
                duration = end_time - start_time
                
                # Update task metrics
                if task_id in self.task_metrics:
                    task_metrics = self.task_metrics[task_id]
                    task_metrics.execution_duration = duration
                    task_metrics.actual_duration = duration
                    task_metrics.success = success
                    if error_message:
                        task_metrics.error_message = error_message
                
                # Update metrics
                self.task_execution_duration.record(duration, {
                    "plan_id": plan_id,
                    "operation": "execution",
                    "success": success
                })
    
    @asynccontextmanager
    async def trace_task_completion(self, task_id: str, plan_id: str):
        """Trace task completion process."""
        operation_name = "complete_task"
        attributes = {
            "plan_management.task_id": task_id,
            "plan_management.plan_id": plan_id
        }
        
        start_time = time.time()
        success = True
        error_message = None
        
        async with self.apm.trace_async_operation(
            operation_name, APMOperationType.CPU_INTENSIVE, attributes
        ) as span:
            try:
                yield span
            except Exception as e:
                success = False
                error_message = str(e)
                span.set_status(Status(StatusCode.ERROR, error_message))
                span.record_exception(e)
                raise
            finally:
                end_time = time.time()
                duration = end_time - start_time
                
                # Update task metrics
                if task_id in self.task_metrics:
                    task_metrics = self.task_metrics[task_id]
                    task_metrics.completion_duration = duration
                    task_metrics.success = success
                    if error_message:
                        task_metrics.error_message = error_message
                
                # Update plan metrics
                if plan_id in self.plan_metrics and success:
                    plan_metrics = self.plan_metrics[plan_id]
                    plan_metrics.completed_tasks += 1
                    plan_metrics.last_updated = end_time
                
                # Update metrics
                self.task_completion_counter.add(1, {
                    "plan_id": plan_id,
                    "success": success
                })
    
    @asynccontextmanager
    async def trace_storage_operation(self, operation: str, plan_id: str = None,
                                    task_id: str = None, data_size: int = 0):
        """Trace storage operations."""
        operation_name = f"storage_{operation}"
        attributes = {
            "storage.operation": operation,
            "storage.data_size": data_size
        }
        
        if plan_id:
            attributes["plan_management.plan_id"] = plan_id
        if task_id:
            attributes["plan_management.task_id"] = task_id
        
        start_time = time.time()
        success = True
        error_message = None
        
        async with self.apm.trace_async_operation(
            operation_name, APMOperationType.IO_INTENSIVE, attributes
        ) as span:
            try:
                yield span
            except Exception as e:
                success = False
                error_message = str(e)
                span.set_status(Status(StatusCode.ERROR, error_message))
                span.record_exception(e)
                raise
            finally:
                end_time = time.time()
                duration = end_time - start_time
                
                # Update plan metrics
                if plan_id and plan_id in self.plan_metrics:
                    plan_metrics = self.plan_metrics[plan_id]
                    plan_metrics.storage_operations += 1
                    plan_metrics.last_updated = end_time
                
                # Update metrics
                self.storage_operations_counter.add(1, {
                    "operation": operation,
                    "success": success
                })
    
    def get_plan_performance_summary(self, plan_id: str = None) -> Dict[str, Any]:
        """Get performance summary for plans."""
        if plan_id:
            metrics = self.plan_metrics.get(plan_id)
            if not metrics or metrics.plan_id == "":
                return {"plan_id": plan_id, "message": "No data available"}
            
            return {
                "plan_id": plan_id,
                "creation_duration": metrics.creation_duration,
                "task_count": metrics.task_count,
                "completed_tasks": metrics.completed_tasks,
                "completion_rate": metrics.completion_rate,
                "total_estimated_duration": metrics.total_estimated_duration,
                "actual_duration": metrics.actual_duration,
                "duration_accuracy": metrics.duration_accuracy,
                "consensus_duration": metrics.consensus_duration,
                "validation_duration": metrics.validation_duration,
                "storage_operations": metrics.storage_operations,
                "last_updated": metrics.last_updated
            }
        else:
            # Return summary for all plans
            summary = {}
            for plan_id, metrics in self.plan_metrics.items():
                if metrics.plan_id:
                    summary[plan_id] = self.get_plan_performance_summary(plan_id)
            return summary
    
    def get_task_performance_summary(self, task_id: str = None) -> Dict[str, Any]:
        """Get performance summary for tasks."""
        if task_id:
            metrics = self.task_metrics.get(task_id)
            if not metrics or metrics.task_id == "":
                return {"task_id": task_id, "message": "No data available"}
            
            return {
                "task_id": task_id,
                "plan_id": metrics.plan_id,
                "creation_duration": metrics.creation_duration,
                "execution_duration": metrics.execution_duration,
                "completion_duration": metrics.completion_duration,
                "estimated_duration": metrics.estimated_duration,
                "actual_duration": metrics.actual_duration,
                "duration_accuracy": metrics.duration_accuracy,
                "complexity_score": metrics.complexity_score,
                "dependencies_count": metrics.dependencies_count,
                "success": metrics.success,
                "error_message": metrics.error_message
            }
        else:
            # Return summary for all tasks
            summary = {}
            for task_id, metrics in self.task_metrics.items():
                if metrics.task_id:
                    summary[task_id] = self.get_task_performance_summary(task_id)
            return summary
    
    def get_consensus_summary(self) -> Dict[str, Any]:
        """Get consensus building summary."""
        if not self.consensus_metrics:
            return {"message": "No consensus operations recorded"}
        
        consensus_data = self.consensus_metrics
        total_consensus = len(consensus_data)
        successful_consensus = sum(1 for c in consensus_data if c.success)
        
        # Calculate average duration
        avg_duration = statistics.mean(c.duration for c in consensus_data)
        
        # Calculate average agreement score
        avg_agreement = statistics.mean(c.agreement_score for c in consensus_data)
        
        # Calculate average conflict count
        avg_conflicts = statistics.mean(c.conflict_count for c in consensus_data)
        
        # Get strategy distribution
        strategy_distribution = defaultdict(int)
        for c in consensus_data:
            strategy_distribution[c.strategy_used] += 1
        
        return {
            "total_consensus_operations": total_consensus,
            "success_rate": successful_consensus / total_consensus if total_consensus > 0 else 0,
            "average_duration": avg_duration,
            "average_agreement_score": avg_agreement,
            "average_conflict_count": avg_conflicts,
            "strategy_distribution": dict(strategy_distribution)
        }
    
    def get_performance_insights(self) -> List[Dict[str, Any]]:
        """Get performance insights and recommendations."""
        insights = []
        
        # Analyze plan creation performance
        for plan_id, metrics in self.plan_metrics.items():
            if not metrics.plan_id:
                continue
            
            # Check for slow plan creation
            if metrics.creation_duration > self.slow_plan_creation_threshold:
                insights.append({
                    "type": "slow_plan_creation",
                    "plan_id": plan_id,
                    "severity": "warning",
                    "message": f"Plan {plan_id} took too long to create ({metrics.creation_duration:.2f}s)",
                    "recommendation": "Optimize plan creation process or simplify plan structure"
                })
            
            # Check for low completion rate
            if metrics.completion_rate < 0.5 and metrics.task_count > 5:
                insights.append({
                    "type": "low_completion_rate",
                    "plan_id": plan_id,
                    "severity": "warning",
                    "message": f"Plan {plan_id} has low task completion rate ({metrics.completion_rate:.2%})",
                    "recommendation": "Review task dependencies and resource allocation"
                })
            
            # Check for duration estimation accuracy
            if metrics.duration_accuracy < 0.7 and metrics.actual_duration > 0:
                insights.append({
                    "type": "poor_estimation_accuracy",
                    "plan_id": plan_id,
                    "severity": "info",
                    "message": f"Plan {plan_id} has poor duration estimation accuracy ({metrics.duration_accuracy:.2%})",
                    "recommendation": "Improve estimation process or adjust estimation factors"
                })
        
        # Analyze consensus performance
        if self.consensus_metrics:
            recent_consensus = self.consensus_metrics[-100:]  # Last 100 consensus operations
            
            # Check for slow consensus
            slow_consensus = [c for c in recent_consensus if c.duration > self.slow_consensus_threshold]
            if len(slow_consensus) > 5:
                insights.append({
                    "type": "slow_consensus_building",
                    "severity": "warning",
                    "message": f"High number of slow consensus operations ({len(slow_consensus)} in last 100)",
                    "recommendation": "Optimize consensus strategy or reduce participant count"
                })
            
            # Check for low agreement scores
            low_agreement = [c for c in recent_consensus if c.agreement_score < self.low_consensus_threshold]
            if len(low_agreement) > 10:
                insights.append({
                    "type": "low_consensus_agreement",
                    "severity": "warning",
                    "message": f"High number of low agreement consensus operations ({len(low_agreement)} in last 100)",
                    "recommendation": "Improve consensus criteria or mediation process"
                })
            
            # Check for high conflict counts
            high_conflict = [c for c in recent_consensus if c.conflict_count > self.high_conflict_threshold]
            if len(high_conflict) > 5:
                insights.append({
                    "type": "high_conflict_count",
                    "severity": "warning",
                    "message": f"High number of consensus operations with many conflicts ({len(high_conflict)} in last 100)",
                    "recommendation": "Improve conflict resolution process or review participant selection"
                })
        
        return insights
    
    def set_plan_id(self, plan_id: str):
        """Set the plan ID for the current operation."""
        # Associate metrics with current plan context
        self.current_plan_id = plan_id
    
    def set_task_id(self, task_id: str, plan_id: str):
        """Set the task ID for the current operation."""
        # Associate metrics with task/plan context
        self.current_task_id = task_id
        self.current_plan_id = plan_id
    
    def set_consensus_id(self, consensus_id: str, plan_id: str):
        """Set the consensus ID for the current operation."""
        # Associate metrics with consensus context
        self.current_consensus_id = consensus_id
        self.current_plan_id = plan_id


# Global instance
plan_management_apm = None


def get_plan_management_apm() -> PlanManagementAPM:
    """Get the global Plan Management APM instance."""
    global plan_management_apm
    if plan_management_apm is None:
        plan_management_apm = PlanManagementAPM()
    return plan_management_apm


def initialize_plan_management_apm(config: APMConfig = None):
    """Initialize the global Plan Management APM instance."""
    global plan_management_apm
    plan_management_apm = PlanManagementAPM(config)
    return plan_management_apm


# Decorators for Plan Management operations
def trace_plan_creation(operation_name: str = None):
    """Decorator to trace plan creation operations."""
    def decorator(func):
        name = operation_name or f"plan_creation.{func.__name__}"
        
        async def async_wrapper(*args, **kwargs):
            apm = get_plan_management_apm()
            
            # Extract parameters
            plan_title = kwargs.get('plan_title', '')
            task_count = kwargs.get('task_count', 0)
            complexity = kwargs.get('complexity', 'medium')
            
            async with apm.trace_plan_creation(plan_title, task_count, complexity) as span:
                return await func(*args, **kwargs)
        
        return async_wrapper
    
    return decorator


def trace_task_decomposition(operation_name: str = None):
    """Decorator to trace task decomposition operations."""
    def decorator(func):
        name = operation_name or f"task_decomposition.{func.__name__}"
        
        async def async_wrapper(*args, **kwargs):
            apm = get_plan_management_apm()
            
            # Extract parameters
            plan_id = kwargs.get('plan_id', '')
            input_text = kwargs.get('input_text', '')
            complexity = kwargs.get('complexity', 'medium')
            
            async with apm.trace_task_decomposition(plan_id, input_text, complexity) as span:
                return await func(*args, **kwargs)
        
        return async_wrapper
    
    return decorator


def trace_consensus_building(operation_name: str = None):
    """Decorator to trace consensus building operations."""
    def decorator(func):
        name = operation_name or f"consensus_building.{func.__name__}"
        
        async def async_wrapper(*args, **kwargs):
            apm = get_plan_management_apm()
            
            # Extract parameters
            plan_id = kwargs.get('plan_id', '')
            participant_count = kwargs.get('participant_count', 0)
            strategy = kwargs.get('strategy', 'voting')
            
            async with apm.trace_consensus_building(plan_id, participant_count, strategy) as span:
                return await func(*args, **kwargs)
        
        return async_wrapper
    
    return decorator


def trace_task_execution(operation_name: str = None):
    """Decorator to trace task execution operations."""
    def decorator(func):
        name = operation_name or f"task_execution.{func.__name__}"
        
        async def async_wrapper(*args, **kwargs):
            apm = get_plan_management_apm()
            
            # Extract parameters
            task_id = kwargs.get('task_id', '')
            plan_id = kwargs.get('plan_id', '')
            
            async with apm.trace_task_execution(task_id, plan_id) as span:
                return await func(*args, **kwargs)
        
        return async_wrapper
    
    return decorator
