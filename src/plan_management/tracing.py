"""
Plan Management service-specific tracing instrumentation.
Provides custom spans and metrics for plan creation, task management, and consensus operations.
"""

import logging
from typing import Dict, Any, Optional, List
from contextlib import asynccontextmanager
import time

from opentelemetry import trace, metrics
from opentelemetry.trace import Status, StatusCode, SpanKind
from opentelemetry.semconv.trace import SpanAttributes
from src.common.tracing import (
    TracingUtils, 
    traced, 
    TraceContextManager,
    get_tracing_config,
    get_instrumentation_manager
)

logger = logging.getLogger(__name__)


class PlanManagementTracing:
    """Tracing instrumentation specific to Plan Management operations."""
    
    def __init__(self):
        self.tracer = None
        self.meter = None
        self._initialize_metrics()
    
    def _initialize_metrics(self):
        """Initialize metrics for plan management operations."""
        config = get_tracing_config()
        self.tracer = config.get_tracer()
        self.meter = config.get_meter()
        
        # Create metrics
        self.plan_creation_counter = self.meter.create_counter(
            "plan_management_plans_created_total",
            description="Total number of plans created"
        )
        
        self.plan_creation_duration = self.meter.create_histogram(
            "plan_management_creation_duration_seconds",
            description="Duration of plan creation operations"
        )
        
        self.task_creation_counter = self.meter.create_counter(
            "plan_management_tasks_created_total",
            description="Total number of tasks created"
        )
        
        self.task_completion_counter = self.meter.create_counter(
            "plan_management_tasks_completed_total",
            description="Total number of tasks completed"
        )
        
        self.consensus_building_duration = self.meter.create_histogram(
            "plan_management_consensus_duration_seconds",
            description="Duration of consensus building operations"
        )
        
        self.plan_validation_counter = self.meter.create_counter(
            "plan_management_validations_total",
            description="Total number of plan validations"
        )
        
        self.plan_estimation_duration = self.meter.create_histogram(
            "plan_management_estimation_duration_seconds",
            description="Duration of plan estimation operations"
        )
        
        self.plan_error_counter = self.meter.create_counter(
            "plan_management_errors_total",
            description="Total number of plan management errors"
        )
        
        self.milestone_creation_counter = self.meter.create_counter(
            "plan_management_milestones_created_total",
            description="Total number of milestones created"
        )
    
    @asynccontextmanager
    async def trace_plan_creation(self, plan_title: str, task_count: int = 0):
        """Trace plan creation process."""
        span_name = "plan_management.create_plan"
        attributes = {
            "plan_management.plan_title": plan_title,
            "plan_management.task_count": task_count
        }
        
        with self.tracer.start_as_current_span(span_name, attributes=attributes) as span:
            start_time = time.time()
            try:
                yield span
                duration = time.time() - start_time
                self.plan_creation_duration.record(duration)
                self.plan_creation_counter.add(1)
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                self.plan_error_counter.add(1, {
                    "operation": "create_plan",
                    "error_type": type(e).__name__
                })
                raise
    
    @asynccontextmanager
    async def trace_task_decomposition(self, plan_title: str, complexity: str = "medium"):
        """Trace task decomposition process."""
        span_name = "plan_management.task_decomposition"
        attributes = {
            "plan_management.plan_title": plan_title,
            "plan_management.complexity": complexity
        }
        
        with self.tracer.start_as_current_span(span_name, attributes=attributes) as span:
            start_time = time.time()
            try:
                yield span
                duration = time.time() - start_time
                self.plan_creation_duration.record(duration, {"operation": "task_decomposition"})
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                self.plan_error_counter.add(1, {
                    "operation": "task_decomposition",
                    "error_type": type(e).__name__
                })
                raise
    
    @asynccontextmanager
    async def trace_consensus_building(self, plan_id: str, participant_count: int):
        """Trace consensus building process."""
        span_name = "plan_management.consensus_building"
        attributes = {
            "plan_management.plan_id": plan_id,
            "plan_management.participant_count": participant_count
        }
        
        with self.tracer.start_as_current_span(span_name, attributes=attributes) as span:
            start_time = time.time()
            try:
                yield span
                duration = time.time() - start_time
                self.consensus_building_duration.record(duration)
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                self.plan_error_counter.add(1, {
                    "operation": "consensus_building",
                    "error_type": type(e).__name__
                })
                raise
    
    @asynccontextmanager
    async def trace_plan_validation(self, plan_id: str, validation_type: str = "completeness"):
        """Trace plan validation process."""
        span_name = "plan_management.plan_validation"
        attributes = {
            "plan_management.plan_id": plan_id,
            "plan_management.validation_type": validation_type
        }
        
        with self.tracer.start_as_current_span(span_name, attributes=attributes) as span:
            start_time = time.time()
            try:
                yield span
                duration = time.time() - start_time
                self.plan_creation_duration.record(duration, {"operation": "validation"})
                self.plan_validation_counter.add(1, {"validation_type": validation_type})
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                self.plan_error_counter.add(1, {
                    "operation": "plan_validation",
                    "error_type": type(e).__name__
                })
                raise
    
    @asynccontextmanager
    async def trace_plan_estimation(self, plan_id: str, estimation_method: str = "simple"):
        """Trace plan estimation process."""
        span_name = "plan_management.plan_estimation"
        attributes = {
            "plan_management.plan_id": plan_id,
            "plan_management.estimation_method": estimation_method
        }
        
        with self.tracer.start_as_current_span(span_name, attributes=attributes) as span:
            start_time = time.time()
            try:
                yield span
                duration = time.time() - start_time
                self.plan_estimation_duration.record(duration, {"method": estimation_method})
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                self.plan_error_counter.add(1, {
                    "operation": "plan_estimation",
                    "error_type": type(e).__name__
                })
                raise
    
    @asynccontextmanager
    async def trace_task_creation(self, plan_id: str, task_title: str):
        """Trace task creation process."""
        span_name = "plan_management.create_task"
        attributes = {
            "plan_management.plan_id": plan_id,
            "plan_management.task_title": task_title
        }
        
        with self.tracer.start_as_current_span(span_name, attributes=attributes) as span:
            try:
                yield span
                self.task_creation_counter.add(1)
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                self.plan_error_counter.add(1, {
                    "operation": "create_task",
                    "error_type": type(e).__name__
                })
                raise
    
    @asynccontextmanager
    async def trace_task_completion(self, plan_id: str, task_id: str):
        """Trace task completion process."""
        span_name = "plan_management.complete_task"
        attributes = {
            "plan_management.plan_id": plan_id,
            "plan_management.task_id": task_id
        }
        
        with self.tracer.start_as_current_span(span_name, attributes=attributes) as span:
            try:
                yield span
                self.task_completion_counter.add(1)
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                self.plan_error_counter.add(1, {
                    "operation": "complete_task",
                    "error_type": type(e).__name__
                })
                raise
    
    def record_plan_metrics(self, plan_id: str, task_count: int, 
                          estimated_hours: float, complexity: str):
        """Record plan-related metrics."""
        self.plan_creation_counter.add(1, {
            "plan_id": plan_id,
            "task_count": task_count,
            "complexity": complexity
        })
        
        if estimated_hours > 0:
            self.plan_estimation_duration.record(estimated_hours, {
                "plan_id": plan_id,
                "metric_type": "estimated_hours"
            })
    
    def record_consensus_metrics(self, plan_id: str, participant_count: int, 
                               consensus_reached: bool, duration: float):
        """Record consensus-related metrics."""
        self.consensus_building_duration.record(duration, {
            "plan_id": plan_id,
            "participant_count": participant_count,
            "consensus_reached": consensus_reached
        })
    
    def add_plan_attributes(self, span, plan_id: str, plan_title: str, 
                          task_count: int, status: str):
        """Add plan attributes to span."""
        span.set_attribute("plan_management.plan_id", plan_id)
        span.set_attribute("plan_management.plan_title", plan_title)
        span.set_attribute("plan_management.task_count", task_count)
        span.set_attribute("plan_management.status", status)
    
    def add_task_attributes(self, span, task_id: str, task_title: str, 
                          task_status: str, estimated_hours: float):
        """Add task attributes to span."""
        span.set_attribute("plan_management.task_id", task_id)
        span.set_attribute("plan_management.task_title", task_title)
        span.set_attribute("plan_management.task_status", task_status)
        span.set_attribute("plan_management.estimated_hours", estimated_hours)
    
    def add_consensus_attributes(self, span, plan_id: str, participant_count: int, 
                               consensus_score: float, voting_method: str):
        """Add consensus attributes to span."""
        span.set_attribute("plan_management.plan_id", plan_id)
        span.set_attribute("plan_management.participant_count", participant_count)
        span.set_attribute("plan_management.consensus_score", consensus_score)
        span.set_attribute("plan_management.voting_method", voting_method)
    
    def add_error_attributes(self, span, error_type: str, error_message: str, 
                           operation: str = None):
        """Add error attributes to span."""
        span.set_attribute("error.type", error_type)
        span.set_attribute("error.message", error_message)
        if operation:
            span.set_attribute("plan_management.operation", operation)


# Decorators for plan management operations
def trace_plan_operation(operation_name: str = None):
    """Decorator to trace plan operations."""
    def decorator(func):
        name = operation_name or f"plan_management.{func.__name__}"
        
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


def trace_task_operation(operation_name: str = None):
    """Decorator to trace task operations."""
    def decorator(func):
        name = operation_name or f"plan_management.task.{func.__name__}"
        
        async def async_wrapper(*args, **kwargs):
            tracer = get_tracing_config().get_tracer()
            with tracer.start_as_current_span(name, kind=SpanKind.INTERNAL) as span:
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


def trace_consensus_operation(operation_name: str = None):
    """Decorator to trace consensus operations."""
    def decorator(func):
        name = operation_name or f"plan_management.consensus.{func.__name__}"
        
        async def async_wrapper(*args, **kwargs):
            tracer = get_tracing_config().get_tracer()
            with tracer.start_as_current_span(name, kind=SpanKind.INTERNAL) as span:
                start_time = time.time()
                try:
                    result = await func(*args, **kwargs)
                    duration = time.time() - start_time
                    
                    # Record metrics
                    plan_tracing = PlanManagementTracing()
                    plan_tracing.consensus_building_duration.record(duration)
                    
                    span.set_status(Status(StatusCode.OK))
                    span.set_attribute("plan_management.duration_ms", duration * 1000)
                    
                    return result
                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    raise
        
        if hasattr(func, '__call__') and hasattr(func, '__code__') and func.__code__.co_flags & 0x80:
            return async_wrapper
        return func
    
    return decorator


# Global instance
plan_management_tracing = PlanManagementTracing()


def get_plan_management_tracing() -> PlanManagementTracing:
    """Get the global plan management tracing instance."""
    return plan_management_tracing


def initialize_plan_management_tracing():
    """Initialize plan management tracing."""
    config = get_tracing_config()
    config.initialize("plan-management")
    
    # Instrument database clients
    manager = get_instrumentation_manager()
    manager.instrument_database()
    
    logger.info("Plan management tracing initialized")