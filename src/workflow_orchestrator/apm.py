"""
Workflow Orchestrator Application Performance Monitoring (APM) implementation.
Provides comprehensive performance monitoring for workflow execution, agent coordination, and step processing.
"""

import logging
import time
import asyncio
from typing import Dict, Any, Optional, List, Union
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import statistics
import json

from opentelemetry import trace, metrics
from opentelemetry.trace import Status, StatusCode, SpanKind
from opentelemetry.semconv.trace import SpanAttributes

from src.common.apm import (
    APMInstrumentation, 
    APMOperationType, 
    APMConfig, 
    PerformanceMetrics,
    get_apm
)
from src.common.tracing import get_tracing_config

logger = logging.getLogger(__name__)


class WorkflowOrchestratorOperationType(Enum):
    """Workflow Orchestrator specific operation types."""
    WORKFLOW_EXECUTION = "workflow_execution"
    WORKFLOW_CREATION = "workflow_creation"
    STEP_EXECUTION = "step_execution"
    AGENT_COORDINATION = "agent_coordination"
    AGENT_COMMUNICATION = "agent_communication"
    TASK_DISTRIBUTION = "task_distribution"
    RESULT_AGGREGATION = "result_aggregation"
    ERROR_HANDLING = "error_handling"
    RETRY_OPERATION = "retry_operation"
    WORKFLOW_VALIDATION = "workflow_validation"
    WORKFLOW_SCHEDULING = "workflow_scheduling"


@dataclass
class WorkflowMetrics:
    """Workflow-specific performance metrics."""
    workflow_id: str
    creation_duration: float = 0.0
    execution_duration: float = 0.0
    total_steps: int = 0
    completed_steps: int = 0
    failed_steps: int = 0
    total_agents: int = 0
    estimated_duration: float = 0.0
    actual_duration: float = 0.0
    retry_count: int = 0
    success: bool = True
    error_message: Optional[str] = None
    last_updated: float = 0.0
    
    @property
    def completion_rate(self) -> float:
        """Calculate step completion rate."""
        if self.total_steps == 0:
            return 0.0
        return self.completed_steps / self.total_steps
    
    @property
    def failure_rate(self) -> float:
        """Calculate step failure rate."""
        if self.total_steps == 0:
            return 0.0
        return self.failed_steps / self.total_steps
    
    @property
    def duration_accuracy(self) -> float:
        """Calculate duration estimation accuracy."""
        if self.estimated_duration == 0:
            return 0.0
        return min(1.0, self.estimated_duration / max(self.actual_duration, 0.001))


@dataclass
class StepMetrics:
    """Step-specific performance metrics."""
    step_id: str
    workflow_id: str
    agent_id: str
    execution_duration: float = 0.0
    queue_duration: float = 0.0
    processing_duration: float = 0.0
    estimated_duration: float = 0.0
    actual_duration: float = 0.0
    input_size: int = 0
    output_size: int = 0
    retry_count: int = 0
    success: bool = True
    error_message: Optional[str] = None
    dependencies_count: int = 0
    
    @property
    def duration_accuracy(self) -> float:
        """Calculate duration estimation accuracy."""
        if self.estimated_duration == 0:
            return 0.0
        return min(1.0, self.estimated_duration / max(self.actual_duration, 0.001))


@dataclass
class AgentCoordinationMetrics:
    """Agent coordination metrics."""
    coordination_id: str
    workflow_id: str
    agent_count: int
    coordination_type: str
    duration: float
    success: bool
    messages_exchanged: int
    conflicts_resolved: int
    consensus_rounds: int
    strategy_used: str
    error_message: Optional[str] = None


@dataclass
class AgentCommunicationMetrics:
    """Agent communication metrics."""
    communication_id: str
    source_agent: str
    target_agent: str
    workflow_id: str
    message_type: str
    message_size: int
    duration: float
    success: bool
    retry_count: int
    error_message: Optional[str] = None


class WorkflowOrchestratorAPM:
    """APM implementation for Workflow Orchestrator service."""
    
    def __init__(self, config: APMConfig = None):
        """Initialize Workflow Orchestrator APM."""
        self.config = config or APMConfig()
        self.apm = get_apm()
        self.tracer = get_tracing_config().get_tracer()
        self.meter = get_tracing_config().get_meter()
        
        # Performance tracking
        self.workflow_metrics = defaultdict(lambda: WorkflowMetrics(workflow_id=""))
        self.step_metrics = defaultdict(lambda: StepMetrics(step_id="", workflow_id="", agent_id=""))
        self.coordination_metrics = []
        self.communication_metrics = []
        
        # Initialize metrics
        self._initialize_metrics()
        
        # Performance thresholds
        self.slow_workflow_threshold = 300.0  # seconds
        self.slow_step_threshold = 60.0  # seconds
        self.high_failure_threshold = 0.1  # 10%
        self.high_retry_threshold = 3  # retries
        
        # History limits
        self.max_coordination_history = 1000
        self.max_communication_history = 5000
        
        # Current context identifiers
        self.current_workflow_id: Optional[str] = None
        self.current_step_id: Optional[str] = None
        self.current_agent_id: Optional[str] = None
        self.current_coordination_id: Optional[str] = None
        self.current_communication_id: Optional[str] = None
    
    def _initialize_metrics(self):
        """Initialize OpenTelemetry metrics for Workflow Orchestrator."""
        # Counters
        self.workflow_execution_counter = self.meter.create_counter(
            "workflow_orchestrator_workflows_executed_total",
            description="Total number of workflows executed"
        )
        
        self.step_execution_counter = self.meter.create_counter(
            "workflow_orchestrator_steps_executed_total",
            description="Total number of steps executed"
        )
        
        self.agent_coordination_counter = self.meter.create_counter(
            "workflow_orchestrator_agent_coordinations_total",
            description="Total number of agent coordination operations"
        )
        
        self.agent_communication_counter = self.meter.create_counter(
            "workflow_orchestrator_agent_communications_total",
            description="Total number of agent communications"
        )
        
        self.retry_operations_counter = self.meter.create_counter(
            "workflow_orchestrator_retry_operations_total",
            description="Total number of retry operations"
        )
        
        self.error_handling_counter = self.meter.create_counter(
            "workflow_orchestrator_error_handlings_total",
            description="Total number of error handling operations"
        )
        
        # Histograms
        self.workflow_execution_duration = self.meter.create_histogram(
            "workflow_orchestrator_workflow_duration_seconds",
            description="Duration of workflow executions"
        )
        
        self.step_execution_duration = self.meter.create_histogram(
            "workflow_orchestrator_step_duration_seconds",
            description="Duration of step executions"
        )
        
        self.agent_coordination_duration = self.meter.create_histogram(
            "workflow_orchestrator_coordination_duration_seconds",
            description="Duration of agent coordination operations"
        )
        
        self.agent_communication_duration = self.meter.create_histogram(
            "workflow_orchestrator_communication_duration_seconds",
            description="Duration of agent communications"
        )
        
        self.step_queue_duration = self.meter.create_histogram(
            "workflow_orchestrator_step_queue_duration_seconds",
            description="Duration of steps in queue"
        )
        
        # Gauges
        self.active_workflows_gauge = self.meter.create_up_down_counter(
            "workflow_orchestrator_active_workflows",
            description="Number of currently active workflows"
        )
        
        self.active_steps_gauge = self.meter.create_up_down_counter(
            "workflow_orchestrator_active_steps",
            description="Number of currently active steps"
        )
        
        self.active_agents_gauge = self.meter.create_up_down_counter(
            "workflow_orchestrator_active_agents",
            description="Number of currently active agents"
        )
    
    @asynccontextmanager
    async def trace_workflow_execution(self, workflow_id: str, workflow_type: str,
                                     estimated_duration: float = 0.0,
                                     total_steps: int = 0):
        """Trace workflow execution process."""
        operation_name = "execute_workflow"
        attributes = {
            "workflow_orchestrator.workflow_id": workflow_id,
            "workflow_orchestrator.workflow_type": workflow_type,
            "workflow_orchestrator.estimated_duration": estimated_duration,
            "workflow_orchestrator.total_steps": total_steps
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
                
                # Record workflow metrics
                workflow_metrics = self.workflow_metrics[workflow_id]
                workflow_metrics.workflow_id = workflow_id
                workflow_metrics.execution_duration = duration
                workflow_metrics.estimated_duration = estimated_duration
                workflow_metrics.total_steps = total_steps
                workflow_metrics.actual_duration = duration
                workflow_metrics.success = success
                if error_message:
                    workflow_metrics.error_message = error_message
                workflow_metrics.last_updated = end_time
                
                # Update metrics
                self.workflow_execution_counter.add(1, {
                    "workflow_type": workflow_type,
                    "success": success
                })
                
                self.workflow_execution_duration.record(duration, {
                    "workflow_type": workflow_type
                })
                
                self.active_workflows_gauge.add(-1 if success else 0, {
                    "workflow_type": workflow_type
                })
    
    @asynccontextmanager
    async def trace_workflow_creation(self, workflow_id: str, workflow_type: str,
                                    total_steps: int = 0, total_agents: int = 0):
        """Trace workflow creation process."""
        operation_name = "create_workflow"
        attributes = {
            "workflow_orchestrator.workflow_id": workflow_id,
            "workflow_orchestrator.workflow_type": workflow_type,
            "workflow_orchestrator.total_steps": total_steps,
            "workflow_orchestrator.total_agents": total_agents
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
                
                # Record workflow metrics
                workflow_metrics = self.workflow_metrics[workflow_id]
                workflow_metrics.workflow_id = workflow_id
                workflow_metrics.creation_duration = duration
                workflow_metrics.total_steps = total_steps
                workflow_metrics.total_agents = total_agents
                workflow_metrics.last_updated = end_time
                
                # Update metrics
                self.workflow_execution_duration.record(duration, {
                    "workflow_type": workflow_type,
                    "operation": "creation"
                })
    
    @asynccontextmanager
    async def trace_step_execution(self, step_id: str, workflow_id: str, agent_id: str,
                                  step_type: str, estimated_duration: float = 0.0,
                                  input_size: int = 0, dependencies_count: int = 0):
        """Trace step execution process."""
        operation_name = "execute_step"
        attributes = {
            "workflow_orchestrator.step_id": step_id,
            "workflow_orchestrator.workflow_id": workflow_id,
            "workflow_orchestrator.agent_id": agent_id,
            "workflow_orchestrator.step_type": step_type,
            "workflow_orchestrator.estimated_duration": estimated_duration,
            "workflow_orchestrator.input_size": input_size,
            "workflow_orchestrator.dependencies_count": dependencies_count
        }
        
        start_time = time.time()
        queue_start_time = time.time()
        success = True
        error_message = None
        output_size = 0
        
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
                queue_duration = queue_start_time - start_time
                processing_duration = end_time - queue_start_time
                
                # Record step metrics
                step_metrics = self.step_metrics[step_id]
                step_metrics.step_id = step_id
                step_metrics.workflow_id = workflow_id
                step_metrics.agent_id = agent_id
                step_metrics.execution_duration = duration
                step_metrics.queue_duration = queue_duration
                step_metrics.processing_duration = processing_duration
                step_metrics.estimated_duration = estimated_duration
                step_metrics.actual_duration = duration
                step_metrics.input_size = input_size
                step_metrics.output_size = output_size
                step_metrics.dependencies_count = dependencies_count
                step_metrics.success = success
                if error_message:
                    step_metrics.error_message = error_message
                
                # Update workflow metrics
                if workflow_id in self.workflow_metrics:
                    workflow_metrics = self.workflow_metrics[workflow_id]
                    if success:
                        workflow_metrics.completed_steps += 1
                    else:
                        workflow_metrics.failed_steps += 1
                    workflow_metrics.last_updated = end_time
                
                # Update metrics
                self.step_execution_counter.add(1, {
                    "step_type": step_type,
                    "success": success
                })
                
                self.step_execution_duration.record(duration, {
                    "step_type": step_type,
                    "agent_id": agent_id
                })
                
                self.step_queue_duration.record(queue_duration, {
                    "step_type": step_type,
                    "agent_id": agent_id
                })
                
                self.active_steps_gauge.add(-1 if success else 0, {
                    "step_type": step_type,
                    "agent_id": agent_id
                })
    
    @asynccontextmanager
    async def trace_agent_coordination(self, coordination_id: str, workflow_id: str,
                                    coordination_type: str, agent_count: int,
                                    strategy: str = "consensus"):
        """Trace agent coordination process."""
        operation_name = "coordinate_agents"
        attributes = {
            "workflow_orchestrator.coordination_id": coordination_id,
            "workflow_orchestrator.workflow_id": workflow_id,
            "workflow_orchestrator.coordination_type": coordination_type,
            "workflow_orchestrator.agent_count": agent_count,
            "workflow_orchestrator.strategy": strategy
        }
        
        start_time = time.time()
        success = True
        error_message = None
        messages_exchanged = 0
        conflicts_resolved = 0
        consensus_rounds = 0
        
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
                
                # Record coordination metrics
                coord_metrics = AgentCoordinationMetrics(
                    coordination_id=coordination_id,
                    workflow_id=workflow_id,
                    agent_count=agent_count,
                    coordination_type=coordination_type,
                    duration=duration,
                    success=success,
                    messages_exchanged=messages_exchanged,
                    conflicts_resolved=conflicts_resolved,
                    consensus_rounds=consensus_rounds,
                    strategy_used=strategy,
                    error_message=error_message
                )
                self.coordination_metrics.append(coord_metrics)
                
                # Keep only recent coordination data
                if len(self.coordination_metrics) > self.max_coordination_history:
                    self.coordination_metrics.pop(0)
                
                # Update metrics
                self.agent_coordination_counter.add(1, {
                    "coordination_type": coordination_type,
                    "strategy": strategy,
                    "success": success
                })
                
                self.agent_coordination_duration.record(duration, {
                    "coordination_type": coordination_type,
                    "strategy": strategy
                })
    
    @asynccontextmanager
    async def trace_agent_communication(self, communication_id: str, source_agent: str,
                                     target_agent: str, workflow_id: str,
                                     message_type: str, message_size: int):
        """Trace agent communication process."""
        operation_name = "communicate_agents"
        attributes = {
            "workflow_orchestrator.communication_id": communication_id,
            "workflow_orchestrator.source_agent": source_agent,
            "workflow_orchestrator.target_agent": target_agent,
            "workflow_orchestrator.workflow_id": workflow_id,
            "workflow_orchestrator.message_type": message_type,
            "workflow_orchestrator.message_size": message_size
        }
        
        start_time = time.time()
        success = True
        error_message = None
        retry_count = 0
        
        async with self.apm.trace_async_operation(
            operation_name, APMOperationType.EXTERNAL_API, attributes
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
                
                # Record communication metrics
                comm_metrics = AgentCommunicationMetrics(
                    communication_id=communication_id,
                    source_agent=source_agent,
                    target_agent=target_agent,
                    workflow_id=workflow_id,
                    message_type=message_type,
                    message_size=message_size,
                    duration=duration,
                    success=success,
                    retry_count=retry_count,
                    error_message=error_message
                )
                self.communication_metrics.append(comm_metrics)
                
                # Keep only recent communication data
                if len(self.communication_metrics) > self.max_communication_history:
                    self.communication_metrics.pop(0)
                
                # Update metrics
                self.agent_communication_counter.add(1, {
                    "message_type": message_type,
                    "success": success
                })
                
                self.agent_communication_duration.record(duration, {
                    "message_type": message_type,
                    "source_agent": source_agent,
                    "target_agent": target_agent
                })
    
    @asynccontextmanager
    async def trace_retry_operation(self, operation_id: str, operation_type: str,
                                  workflow_id: str, retry_count: int,
                                  max_retries: int):
        """Trace retry operation."""
        operation_name = "retry_operation"
        attributes = {
            "workflow_orchestrator.operation_id": operation_id,
            "workflow_orchestrator.operation_type": operation_type,
            "workflow_orchestrator.workflow_id": workflow_id,
            "workflow_orchestrator.retry_count": retry_count,
            "workflow_orchestrator.max_retries": max_retries
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
                
                # Update metrics
                self.retry_operations_counter.add(1, {
                    "operation_type": operation_type,
                    "success": success
                })
    
    @asynccontextmanager
    async def trace_error_handling(self, error_id: str, error_type: str,
                                 workflow_id: str, step_id: str = None,
                                 handling_strategy: str = "retry"):
        """Trace error handling operation."""
        operation_name = "handle_error"
        attributes = {
            "workflow_orchestrator.error_id": error_id,
            "workflow_orchestrator.error_type": error_type,
            "workflow_orchestrator.workflow_id": workflow_id,
            "workflow_orchestrator.step_id": step_id,
            "workflow_orchestrator.handling_strategy": handling_strategy
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
                
                # Update metrics
                self.error_handling_counter.add(1, {
                    "error_type": error_type,
                    "handling_strategy": handling_strategy,
                    "success": success
                })
    
    def get_workflow_performance_summary(self, workflow_id: str = None) -> Dict[str, Any]:
        """Get performance summary for workflows."""
        if workflow_id:
            metrics = self.workflow_metrics.get(workflow_id)
            if not metrics or metrics.workflow_id == "":
                return {"workflow_id": workflow_id, "message": "No data available"}
            
            return {
                "workflow_id": workflow_id,
                "creation_duration": metrics.creation_duration,
                "execution_duration": metrics.execution_duration,
                "total_steps": metrics.total_steps,
                "completed_steps": metrics.completed_steps,
                "failed_steps": metrics.failed_steps,
                "completion_rate": metrics.completion_rate,
                "failure_rate": metrics.failure_rate,
                "total_agents": metrics.total_agents,
                "estimated_duration": metrics.estimated_duration,
                "actual_duration": metrics.actual_duration,
                "duration_accuracy": metrics.duration_accuracy,
                "retry_count": metrics.retry_count,
                "success": metrics.success,
                "error_message": metrics.error_message,
                "last_updated": metrics.last_updated
            }
        else:
            # Return summary for all workflows
            summary = {}
            for wf_id, metrics in self.workflow_metrics.items():
                if metrics.workflow_id:
                    summary[wf_id] = self.get_workflow_performance_summary(wf_id)
            return summary
    
    def get_step_performance_summary(self, step_id: str = None) -> Dict[str, Any]:
        """Get performance summary for steps."""
        if step_id:
            metrics = self.step_metrics.get(step_id)
            if not metrics or metrics.step_id == "":
                return {"step_id": step_id, "message": "No data available"}
            
            return {
                "step_id": step_id,
                "workflow_id": metrics.workflow_id,
                "agent_id": metrics.agent_id,
                "execution_duration": metrics.execution_duration,
                "queue_duration": metrics.queue_duration,
                "processing_duration": metrics.processing_duration,
                "estimated_duration": metrics.estimated_duration,
                "actual_duration": metrics.actual_duration,
                "duration_accuracy": metrics.duration_accuracy,
                "input_size": metrics.input_size,
                "output_size": metrics.output_size,
                "retry_count": metrics.retry_count,
                "success": metrics.success,
                "error_message": metrics.error_message,
                "dependencies_count": metrics.dependencies_count
            }
        else:
            # Return summary for all steps
            summary = {}
            for s_id, metrics in self.step_metrics.items():
                if metrics.step_id:
                    summary[s_id] = self.get_step_performance_summary(s_id)
            return summary
    
    def get_coordination_summary(self) -> Dict[str, Any]:
        """Get agent coordination summary."""
        if not self.coordination_metrics:
            return {"message": "No agent coordination operations recorded"}
        
        coord_data = self.coordination_metrics
        total_coordinations = len(coord_data)
        successful_coordinations = sum(1 for c in coord_data if c.success)
        
        # Calculate average duration
        avg_duration = statistics.mean(c.duration for c in coord_data)
        
        # Calculate average messages exchanged
        avg_messages = statistics.mean(c.messages_exchanged for c in coord_data)
        
        # Calculate average conflicts resolved
        avg_conflicts = statistics.mean(c.conflicts_resolved for c in coord_data)
        
        # Get coordination type distribution
        type_distribution = defaultdict(int)
        for c in coord_data:
            type_distribution[c.coordination_type] += 1
        
        # Get strategy distribution
        strategy_distribution = defaultdict(int)
        for c in coord_data:
            strategy_distribution[c.strategy_used] += 1
        
        return {
            "total_coordinations": total_coordinations,
            "success_rate": successful_coordinations / total_coordinations if total_coordinations > 0 else 0,
            "average_duration": avg_duration,
            "average_messages_exchanged": avg_messages,
            "average_conflicts_resolved": avg_conflicts,
            "coordination_type_distribution": dict(type_distribution),
            "strategy_distribution": dict(strategy_distribution)
        }
    
    def get_communication_summary(self) -> Dict[str, Any]:
        """Get agent communication summary."""
        if not self.communication_metrics:
            return {"message": "No agent communications recorded"}
        
        comm_data = self.communication_metrics
        total_communications = len(comm_data)
        successful_communications = sum(1 for c in comm_data if c.success)
        
        # Calculate average duration
        avg_duration = statistics.mean(c.duration for c in comm_data)
        
        # Calculate average message size
        avg_message_size = statistics.mean(c.message_size for c in comm_data)
        
        # Calculate average retry count
        avg_retries = statistics.mean(c.retry_count for c in comm_data)
        
        # Get message type distribution
        type_distribution = defaultdict(int)
        for c in comm_data:
            type_distribution[c.message_type] += 1
        
        # Get agent pair distribution
        agent_pairs = defaultdict(int)
        for c in comm_data:
            pair = f"{c.source_agent}->{c.target_agent}"
            agent_pairs[pair] += 1
        
        return {
            "total_communications": total_communications,
            "success_rate": successful_communications / total_communications if total_communications > 0 else 0,
            "average_duration": avg_duration,
            "average_message_size": avg_message_size,
            "average_retry_count": avg_retries,
            "message_type_distribution": dict(type_distribution),
            "agent_pair_distribution": dict(agent_pairs)
        }
    
    def get_performance_insights(self) -> List[Dict[str, Any]]:
        """Get performance insights and recommendations."""
        insights = []
        
        # Analyze workflow performance
        for workflow_id, metrics in self.workflow_metrics.items():
            if not metrics.workflow_id:
                continue
            
            # Check for slow workflows
            if metrics.execution_duration > self.slow_workflow_threshold:
                insights.append({
                    "type": "slow_workflow",
                    "workflow_id": workflow_id,
                    "severity": "warning",
                    "message": f"Workflow {workflow_id} took too long to execute ({metrics.execution_duration:.2f}s)",
                    "recommendation": "Optimize workflow structure or break into smaller workflows"
                })
            
            # Check for high failure rates
            if metrics.failure_rate > self.high_failure_threshold and metrics.total_steps > 5:
                insights.append({
                    "type": "high_failure_rate",
                    "workflow_id": workflow_id,
                    "severity": "error",
                    "message": f"Workflow {workflow_id} has high step failure rate ({metrics.failure_rate:.2%})",
                    "recommendation": "Review error handling and retry strategies"
                })
            
            # Check for duration estimation accuracy
            if metrics.duration_accuracy < 0.7 and metrics.actual_duration > 0:
                insights.append({
                    "type": "poor_estimation_accuracy",
                    "workflow_id": workflow_id,
                    "severity": "info",
                    "message": f"Workflow {workflow_id} has poor duration estimation accuracy ({metrics.duration_accuracy:.2%})",
                    "recommendation": "Improve estimation process or adjust estimation factors"
                })
        
        # Analyze step performance
        for step_id, metrics in self.step_metrics.items():
            if not metrics.step_id:
                continue
            
            # Check for slow steps
            if metrics.execution_duration > self.slow_step_threshold:
                insights.append({
                    "type": "slow_step",
                    "step_id": step_id,
                    "workflow_id": metrics.workflow_id,
                    "severity": "warning",
                    "message": f"Step {step_id} took too long to execute ({metrics.execution_duration:.2f}s)",
                    "recommendation": "Optimize step implementation or agent performance"
                })
            
            # Check for high retry counts
            if metrics.retry_count > self.high_retry_threshold:
                insights.append({
                    "type": "high_retry_count",
                    "step_id": step_id,
                    "workflow_id": metrics.workflow_id,
                    "severity": "warning",
                    "message": f"Step {step_id} has high retry count ({metrics.retry_count})",
                    "recommendation": "Review step implementation or improve error handling"
                })
        
        # Analyze coordination performance
        if self.coordination_metrics:
            recent_coord = self.coordination_metrics[-100:]  # Last 100 coordination operations
            
            # Check for failed coordinations
            failed_coord = [c for c in recent_coord if not c.success]
            if len(failed_coord) > 5:
                insights.append({
                    "type": "failed_coordinations",
                    "severity": "error",
                    "message": f"High number of failed coordination operations ({len(failed_coord)} in last 100)",
                    "recommendation": "Review coordination strategies and agent communication"
                })
        
        # Analyze communication performance
        if self.communication_metrics:
            recent_comm = self.communication_metrics[-1000:]  # Last 1000 communication operations
            
            # Check for failed communications
            failed_comm = [c for c in recent_comm if not c.success]
            if len(failed_comm) > 20:
                insights.append({
                    "type": "failed_communications",
                    "severity": "error",
                    "message": f"High number of failed communication operations ({len(failed_comm)} in last 1000)",
                    "recommendation": "Review agent communication infrastructure and error handling"
                })
            
            # Check for high retry counts
            high_retry_comm = [c for c in recent_comm if c.retry_count > self.high_retry_threshold]
            if len(high_retry_comm) > 10:
                insights.append({
                    "type": "high_communication_retries",
                    "severity": "warning",
                    "message": f"High number of communication operations with many retries ({len(high_retry_comm)} in last 1000)",
                    "recommendation": "Improve agent communication reliability"
                })
        
        return insights
    
    def set_workflow_id(self, workflow_id: str):
        """Set the workflow ID for the current operation."""
        # Associate metrics with the workflow context
        self.current_workflow_id = workflow_id
    
    def set_step_id(self, step_id: str, workflow_id: str, agent_id: str):
        """Set the step ID for the current operation."""
        # Associate metrics with the step context
        self.current_step_id = step_id
        self.current_workflow_id = workflow_id
        self.current_agent_id = agent_id
    
    def set_coordination_id(self, coordination_id: str, workflow_id: str):
        """Set the coordination ID for the current operation."""
        # Associate metrics with the coordination context
        self.current_coordination_id = coordination_id
        self.current_workflow_id = workflow_id
    
    def set_communication_id(self, communication_id: str, workflow_id: str):
        """Set the communication ID for the current operation."""
        # Associate metrics with the communication context
        self.current_communication_id = communication_id
        self.current_workflow_id = workflow_id


# Global instance
workflow_orchestrator_apm = None


def get_workflow_orchestrator_apm() -> WorkflowOrchestratorAPM:
    """Get the global Workflow Orchestrator APM instance."""
    global workflow_orchestrator_apm
    if workflow_orchestrator_apm is None:
        workflow_orchestrator_apm = WorkflowOrchestratorAPM()
    return workflow_orchestrator_apm


def initialize_workflow_orchestrator_apm(config: APMConfig = None):
    """Initialize the global Workflow Orchestrator APM instance."""
    global workflow_orchestrator_apm
    workflow_orchestrator_apm = WorkflowOrchestratorAPM(config)
    return workflow_orchestrator_apm


# Decorators for Workflow Orchestrator operations
def trace_workflow_execution(operation_name: str = None):
    """Decorator to trace workflow execution operations."""
    def decorator(func):
        name = operation_name or f"workflow_execution.{func.__name__}"
        
        async def async_wrapper(*args, **kwargs):
            apm = get_workflow_orchestrator_apm()
            
            # Extract parameters
            workflow_id = kwargs.get('workflow_id', '')
            workflow_type = kwargs.get('workflow_type', '')
            estimated_duration = kwargs.get('estimated_duration', 0.0)
            total_steps = kwargs.get('total_steps', 0)
            
            async with apm.trace_workflow_execution(workflow_id, workflow_type, estimated_duration, total_steps) as span:
                return await func(*args, **kwargs)
        
        return async_wrapper
    
    return decorator


def trace_step_execution(operation_name: str = None):
    """Decorator to trace step execution operations."""
    def decorator(func):
        name = operation_name or f"step_execution.{func.__name__}"
        
        async def async_wrapper(*args, **kwargs):
            apm = get_workflow_orchestrator_apm()
            
            # Extract parameters
            step_id = kwargs.get('step_id', '')
            workflow_id = kwargs.get('workflow_id', '')
            agent_id = kwargs.get('agent_id', '')
            step_type = kwargs.get('step_type', '')
            estimated_duration = kwargs.get('estimated_duration', 0.0)
            input_size = kwargs.get('input_size', 0)
            dependencies_count = kwargs.get('dependencies_count', 0)
            
            async with apm.trace_step_execution(step_id, workflow_id, agent_id, step_type, estimated_duration, input_size, dependencies_count) as span:
                return await func(*args, **kwargs)
        
        return async_wrapper
    
    return decorator


def trace_agent_coordination(operation_name: str = None):
    """Decorator to trace agent coordination operations."""
    def decorator(func):
        name = operation_name or f"agent_coordination.{func.__name__}"
        
        async def async_wrapper(*args, **kwargs):
            apm = get_workflow_orchestrator_apm()
            
            # Extract parameters
            coordination_id = kwargs.get('coordination_id', '')
            workflow_id = kwargs.get('workflow_id', '')
            coordination_type = kwargs.get('coordination_type', '')
            agent_count = kwargs.get('agent_count', 0)
            strategy = kwargs.get('strategy', 'consensus')
            
            async with apm.trace_agent_coordination(coordination_id, workflow_id, coordination_type, agent_count, strategy) as span:
                return await func(*args, **kwargs)
        
        return async_wrapper
    
    return decorator


def trace_agent_communication(operation_name: str = None):
    """Decorator to trace agent communication operations."""
    def decorator(func):
        name = operation_name or f"agent_communication.{func.__name__}"
        
        async def async_wrapper(*args, **kwargs):
            apm = get_workflow_orchestrator_apm()
            
            # Extract parameters
            communication_id = kwargs.get('communication_id', '')
            source_agent = kwargs.get('source_agent', '')
            target_agent = kwargs.get('target_agent', '')
            workflow_id = kwargs.get('workflow_id', '')
            message_type = kwargs.get('message_type', '')
            message_size = kwargs.get('message_size', 0)
            
            async with apm.trace_agent_communication(communication_id, source_agent, target_agent, workflow_id, message_type, message_size) as span:
                return await func(*args, **kwargs)
        
        return async_wrapper
    
    return decorator
