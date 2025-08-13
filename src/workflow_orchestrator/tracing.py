"""
Workflow Orchestrator service-specific tracing instrumentation.
Provides custom spans and metrics for workflow execution, step coordination, and error recovery.
"""

import logging
from contextlib import asynccontextmanager
import time

from opentelemetry.trace import Status, StatusCode, SpanKind
from src.common.tracing import (
    get_tracing_config,
    get_instrumentation_manager
)

logger = logging.getLogger(__name__)


class WorkflowOrchestratorTracing:
    """Tracing instrumentation specific to Workflow Orchestrator operations."""
    
    def __init__(self):
        self.tracer = None
        self.meter = None
        self._initialize_metrics()
    
    def _initialize_metrics(self):
        """Initialize metrics for workflow orchestrator operations."""
        config = get_tracing_config()
        self.tracer = config.get_tracer()
        self.meter = config.get_meter()
        
        # Create metrics
        self.workflow_execution_counter = self.meter.create_counter(
            "workflow_orchestrator_executions_total",
            description="Total number of workflow executions"
        )
        
        self.workflow_execution_duration = self.meter.create_histogram(
            "workflow_orchestrator_execution_duration_seconds",
            description="Duration of workflow executions"
        )
        
        self.step_execution_counter = self.meter.create_counter(
            "workflow_orchestrator_step_executions_total",
            description="Total number of step executions"
        )
        
        self.step_execution_duration = self.meter.create_histogram(
            "workflow_orchestrator_step_duration_seconds",
            description="Duration of step executions"
        )
        
        self.workflow_completion_counter = self.meter.create_counter(
            "workflow_orchestrator_completions_total",
            description="Total number of workflow completions"
        )
        
        self.workflow_failure_counter = self.meter.create_counter(
            "workflow_orchestrator_failures_total",
            description="Total number of workflow failures"
        )
        
        self.step_retry_counter = self.meter.create_counter(
            "workflow_orchestrator_step_retries_total",
            description="Total number of step retries"
        )
        
        self.error_recovery_counter = self.meter.create_counter(
            "workflow_orchestrator_error_recoveries_total",
            description="Total number of error recovery operations"
        )
        
        self.workflow_error_counter = self.meter.create_counter(
            "workflow_orchestrator_errors_total",
            description="Total number of workflow errors"
        )
        
        self.parallel_execution_counter = self.meter.create_counter(
            "workflow_orchestrator_parallel_executions_total",
            description="Total number of parallel step executions"
        )
        
        self.conditional_execution_counter = self.meter.create_counter(
            "workflow_orchestrator_conditional_executions_total",
            description="Total number of conditional step executions"
        )
    
    @asynccontextmanager
    async def trace_workflow_execution(self, workflow_id: str, workflow_name: str, 
                                    execution_mode: str = "sequential"):
        """Trace workflow execution process."""
        span_name = "workflow_orchestrator.execute_workflow"
        attributes = {
            "workflow_orchestrator.workflow_id": workflow_id,
            "workflow_orchestrator.workflow_name": workflow_name,
            "workflow_orchestrator.execution_mode": execution_mode
        }
        
        with self.tracer.start_as_current_span(span_name, attributes=attributes) as span:
            start_time = time.time()
            try:
                yield span
                duration = time.time() - start_time
                self.workflow_execution_duration.record(duration, {"execution_mode": execution_mode})
                self.workflow_completion_counter.add(1, {"execution_mode": execution_mode})
            except Exception as e:
                duration = time.time() - start_time
                self.workflow_execution_duration.record(duration, {"execution_mode": execution_mode})
                self.workflow_failure_counter.add(1, {"execution_mode": execution_mode})
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                self.workflow_error_counter.add(1, {
                    "operation": "execute_workflow",
                    "error_type": type(e).__name__
                })
                raise
    
    @asynccontextmanager
    async def trace_step_execution(self, workflow_id: str, step_id: str, step_name: str, 
                                 step_type: str, execution_number: int):
        """Trace step execution process."""
        span_name = f"workflow_orchestrator.execute_step.{step_type}"
        attributes = {
            "workflow_orchestrator.workflow_id": workflow_id,
            "workflow_orchestrator.step_id": step_id,
            "workflow_orchestrator.step_name": step_name,
            "workflow_orchestrator.step_type": step_type,
            "workflow_orchestrator.execution_number": execution_number
        }
        
        with self.tracer.start_as_current_span(span_name, attributes=attributes) as span:
            start_time = time.time()
            try:
                yield span
                duration = time.time() - start_time
                self.step_execution_duration.record(duration, {"step_type": step_type})
                self.step_execution_counter.add(1, {"step_type": step_type})
            except Exception as e:
                duration = time.time() - start_time
                self.step_execution_duration.record(duration, {"step_type": step_type})
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                self.workflow_error_counter.add(1, {
                    "operation": "execute_step",
                    "step_type": step_type,
                    "error_type": type(e).__name__
                })
                raise
    
    @asynccontextmanager
    async def trace_parallel_execution(self, workflow_id: str, step_count: int):
        """Trace parallel step execution."""
        span_name = "workflow_orchestrator.execute_parallel"
        attributes = {
            "workflow_orchestrator.workflow_id": workflow_id,
            "workflow_orchestrator.step_count": step_count
        }
        
        with self.tracer.start_as_current_span(span_name, attributes=attributes) as span:
            start_time = time.time()
            try:
                yield span
                duration = time.time() - start_time
                self.workflow_execution_duration.record(duration, {"operation": "parallel"})
                self.parallel_execution_counter.add(1)
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                self.workflow_error_counter.add(1, {
                    "operation": "parallel_execution",
                    "error_type": type(e).__name__
                })
                raise
    
    @asynccontextmanager
    async def trace_conditional_execution(self, workflow_id: str, condition: str):
        """Trace conditional step execution."""
        span_name = "workflow_orchestrator.execute_conditional"
        attributes = {
            "workflow_orchestrator.workflow_id": workflow_id,
            "workflow_orchestrator.condition": condition
        }
        
        with self.tracer.start_as_current_span(span_name, attributes=attributes) as span:
            start_time = time.time()
            try:
                yield span
                duration = time.time() - start_time
                self.workflow_execution_duration.record(duration, {"operation": "conditional"})
                self.conditional_execution_counter.add(1)
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                self.workflow_error_counter.add(1, {
                    "operation": "conditional_execution",
                    "error_type": type(e).__name__
                })
                raise
    
    @asynccontextmanager
    async def trace_error_recovery(self, workflow_id: str, step_id: str, 
                                 error_type: str, recovery_strategy: str):
        """Trace error recovery process."""
        span_name = "workflow_orchestrator.error_recovery"
        attributes = {
            "workflow_orchestrator.workflow_id": workflow_id,
            "workflow_orchestrator.step_id": step_id,
            "workflow_orchestrator.error_type": error_type,
            "workflow_orchestrator.recovery_strategy": recovery_strategy
        }
        
        with self.tracer.start_as_current_span(span_name, attributes=attributes) as span:
            start_time = time.time()
            try:
                yield span
                duration = time.time() - start_time
                self.workflow_execution_duration.record(duration, {"operation": "error_recovery"})
                self.error_recovery_counter.add(1, {"recovery_strategy": recovery_strategy})
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                self.workflow_error_counter.add(1, {
                    "operation": "error_recovery",
                    "error_type": type(e).__name__
                })
                raise
    
    @asynccontextmanager
    async def trace_step_retry(self, workflow_id: str, step_id: str, 
                             retry_count: int, max_retries: int):
        """Trace step retry process."""
        span_name = "workflow_orchestrator.step_retry"
        attributes = {
            "workflow_orchestrator.workflow_id": workflow_id,
            "workflow_orchestrator.step_id": step_id,
            "workflow_orchestrator.retry_count": retry_count,
            "workflow_orchestrator.max_retries": max_retries
        }
        
        with self.tracer.start_as_current_span(span_name, attributes=attributes) as span:
            try:
                yield span
                self.step_retry_counter.add(1)
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                self.workflow_error_counter.add(1, {
                    "operation": "step_retry",
                    "error_type": type(e).__name__
                })
                raise
    
    def record_workflow_metrics(self, workflow_id: str, workflow_name: str, 
                              duration: float, step_count: int, success: bool):
        """Record workflow execution metrics."""
        self.workflow_execution_duration.record(duration, {"workflow_name": workflow_name})
        self.workflow_execution_counter.add(1, {"workflow_name": workflow_name})
        
        if success:
            self.workflow_completion_counter.add(1, {"workflow_name": workflow_name})
        else:
            self.workflow_failure_counter.add(1, {"workflow_name": workflow_name})
    
    def record_step_metrics(self, step_id: str, step_type: str, duration: float, 
                          success: bool, retry_count: int = 0):
        """Record step execution metrics."""
        self.step_execution_duration.record(duration, {"step_type": step_type})
        self.step_execution_counter.add(1, {"step_type": step_type})
        
        if retry_count > 0:
            self.step_retry_counter.add(retry_count, {"step_type": step_type})
        
        if not success:
            self.workflow_error_counter.add(1, {
                "operation": "step_execution",
                "step_type": step_type
            })
    
    def record_parallel_execution_metrics(self, workflow_id: str, step_count: int, 
                                        duration: float, success_count: int):
        """Record parallel execution metrics."""
        self.workflow_execution_duration.record(duration, {"operation": "parallel"})
        self.parallel_execution_counter.add(1)
        
        # Record success rate
        if step_count > 0:
            success_rate = success_count / step_count
            self.workflow_completion_counter.add(success_count, {"operation": "parallel"})
    
    def add_workflow_attributes(self, span, workflow_id: str, workflow_name: str, 
                              execution_mode: str, step_count: int):
        """Add workflow attributes to span."""
        span.set_attribute("workflow_orchestrator.workflow_id", workflow_id)
        span.set_attribute("workflow_orchestrator.workflow_name", workflow_name)
        span.set_attribute("workflow_orchestrator.execution_mode", execution_mode)
        span.set_attribute("workflow_orchestrator.step_count", step_count)
    
    def add_step_attributes(self, span, step_id: str, step_name: str, 
                          step_type: str, execution_number: int):
        """Add step attributes to span."""
        span.set_attribute("workflow_orchestrator.step_id", step_id)
        span.set_attribute("workflow_orchestrator.step_name", step_name)
        span.set_attribute("workflow_orchestrator.step_type", step_type)
        span.set_attribute("workflow_orchestrator.execution_number", execution_number)
    
    def add_execution_attributes(self, span, workflow_id: str, execution_number: int, 
                               status: str, start_time: float, end_time: float = None):
        """Add execution attributes to span."""
        span.set_attribute("workflow_orchestrator.workflow_id", workflow_id)
        span.set_attribute("workflow_orchestrator.execution_number", execution_number)
        span.set_attribute("workflow_orchestrator.status", status)
        span.set_attribute("workflow_orchestrator.start_time", start_time)
        if end_time is not None:
            span.set_attribute("workflow_orchestrator.end_time", end_time)
            span.set_attribute("workflow_orchestrator.duration", end_time - start_time)
    
    def add_error_attributes(self, span, error_type: str, error_message: str, 
                           operation: str = None, workflow_id: str = None, 
                           step_id: str = None):
        """Add error attributes to span."""
        span.set_attribute("error.type", error_type)
        span.set_attribute("error.message", error_message)
        if operation:
            span.set_attribute("workflow_orchestrator.operation", operation)
        if workflow_id:
            span.set_attribute("workflow_orchestrator.workflow_id", workflow_id)
        if step_id:
            span.set_attribute("workflow_orchestrator.step_id", step_id)


# Decorators for workflow orchestrator operations
def trace_workflow_operation(operation_name: str = None):
    """Decorator to trace workflow operations."""
    def decorator(func):
        name = operation_name or f"workflow_orchestrator.{func.__name__}"
        
        async def async_wrapper(*args, **kwargs):
            tracer = get_tracing_config().get_tracer()
            with tracer.start_as_current_span(name, kind=SpanKind.SERVER) as span:
                try:
                    result = await func(*args, **kwargs)
                    span.set_status(Status(StatusCode.OK))
                    return result
                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    raise
        
        if hasattr(func, '__call__') and hasattr(func, '__code__') and func.__code__.co_flags & 0x80:
            return async_wrapper
        return func
    
    return decorator


def trace_step_operation(operation_name: str = None):
    """Decorator to trace step operations."""
    def decorator(func):
        name = operation_name or f"workflow_orchestrator.step.{func.__name__}"
        
        async def async_wrapper(*args, **kwargs):
            tracer = get_tracing_config().get_tracer()
            with tracer.start_as_current_span(name, kind=SpanKind.INTERNAL) as span:
                start_time = time.time()
                try:
                    result = await func(*args, **kwargs)
                    duration = time.time() - start_time
                    
                    # Record metrics
                    workflow_tracing = WorkflowOrchestratorTracing()
                    workflow_tracing.step_execution_duration.record(duration)
                    workflow_tracing.step_execution_counter.add(1)
                    
                    span.set_status(Status(StatusCode.OK))
                    span.set_attribute("workflow_orchestrator.duration_ms", duration * 1000)
                    
                    return result
                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    workflow_tracing = WorkflowOrchestratorTracing()
                    workflow_tracing.workflow_error_counter.add(1, {
                        "operation": "step_execution",
                        "error_type": type(e).__name__
                    })
                    raise
        
        if hasattr(func, '__call__') and hasattr(func, '__code__') and func.__code__.co_flags & 0x80:
            return async_wrapper
        return func
    
    return decorator


def trace_execution_mode(operation_name: str = None, execution_mode: str = "sequential"):
    """Decorator to trace execution mode operations."""
    def decorator(func):
        name = operation_name or f"workflow_orchestrator.{execution_mode}.{func.__name__}"
        
        async def async_wrapper(*args, **kwargs):
            tracer = get_tracing_config().get_tracer()
            attributes = {"workflow_orchestrator.execution_mode": execution_mode}
            
            with tracer.start_as_current_span(name, attributes=attributes, kind=SpanKind.INTERNAL) as span:
                start_time = time.time()
                try:
                    result = await func(*args, **kwargs)
                    duration = time.time() - start_time
                    
                    # Record metrics
                    workflow_tracing = WorkflowOrchestratorTracing()
                    workflow_tracing.workflow_execution_duration.record(duration, {"execution_mode": execution_mode})
                    
                    if execution_mode == "parallel":
                        workflow_tracing.parallel_execution_counter.add(1)
                    elif execution_mode == "conditional":
                        workflow_tracing.conditional_execution_counter.add(1)
                    
                    span.set_status(Status(StatusCode.OK))
                    span.set_attribute("workflow_orchestrator.duration_ms", duration * 1000)
                    
                    return result
                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    workflow_tracing = WorkflowOrchestratorTracing()
                    workflow_tracing.workflow_error_counter.add(1, {
                        "operation": f"{execution_mode}_execution",
                        "error_type": type(e).__name__
                    })
                    raise
        
        if hasattr(func, '__call__') and hasattr(func, '__code__') and func.__code__.co_flags & 0x80:
            return async_wrapper
        return func
    
    return decorator


# Global instance
workflow_orchestrator_tracing = WorkflowOrchestratorTracing()


def get_workflow_orchestrator_tracing() -> WorkflowOrchestratorTracing:
    """Get the global workflow orchestrator tracing instance."""
    return workflow_orchestrator_tracing


def initialize_workflow_orchestrator_tracing():
    """Initialize workflow orchestrator tracing."""
    config = get_tracing_config()
    config.initialize("workflow-orchestrator")
    
    # Instrument database clients
    manager = get_instrumentation_manager()
    manager.instrument_database()
    
    logger.info("Workflow orchestrator tracing initialized")