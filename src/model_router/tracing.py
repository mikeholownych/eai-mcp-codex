"""
Model Router service-specific tracing instrumentation.
Provides custom spans and metrics for LLM model routing operations.
"""

import logging
from typing import Dict, Any, Optional, List
from contextlib import asynccontextmanager
import time

from opentelemetry.trace import Status, StatusCode, SpanKind
from src.common.tracing import (
    get_tracing_config,
    get_instrumentation_manager
)

logger = logging.getLogger(__name__)


class ModelRouterTracing:
    """Tracing instrumentation specific to Model Router operations."""
    
    def __init__(self):
        self.tracer = None
        self.meter = None
        self._initialize_metrics()
    
    def _initialize_metrics(self):
        """Initialize metrics for model router operations."""
        config = get_tracing_config()
        self.tracer = config.get_tracer()
        self.meter = config.get_meter()
        
        # Create metrics
        self.routing_decisions_counter = self.meter.create_counter(
            "model_router_routing_decisions_total",
            description="Total number of routing decisions made"
        )
        
        self.model_request_duration = self.meter.create_histogram(
            "model_router_request_duration_seconds",
            description="Duration of model requests"
        )
        
        self.model_request_size = self.meter.create_histogram(
            "model_router_request_size_bytes",
            description="Size of model requests in bytes"
        )
        
        self.model_response_size = self.meter.create_histogram(
            "model_router_response_size_bytes",
            description="Size of model responses in bytes"
        )
        
        self.model_error_counter = self.meter.create_counter(
            "model_router_errors_total",
            description="Total number of model errors"
        )
        
        self.model_health_checks = self.meter.create_counter(
            "model_router_health_checks_total",
            description="Total number of model health checks"
        )
        
        self.token_usage_counter = self.meter.create_counter(
            "model_router_token_usage_total",
            description="Total token usage across all models"
        )
        
        self.model_selection_counter = self.meter.create_counter(
            "model_router_model_selections_total",
            description="Total number of times each model was selected"
        )
    
    @asynccontextmanager
    async def trace_model_selection(self, text: str, context: Optional[Dict[str, Any]] = None):
        """Trace model selection process."""
        span_name = "model_router.model_selection"
        attributes = {
            "model_router.input_length": len(text),
            "model_router.has_context": context is not None
        }
        
        with self.tracer.start_as_current_span(span_name, attributes=attributes) as span:
            start_time = time.time()
            try:
                yield span
                duration = time.time() - start_time
                self.model_request_duration.record(duration, {"operation": "model_selection"})
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                self.model_error_counter.add(1, {"error_type": type(e).__name__})
                raise
    
    @asynccontextmanager
    async def trace_model_request(self, model_name: str, operation: str, 
                                text: str, context: Optional[Dict[str, Any]] = None):
        """Trace a request to a specific model."""
        span_name = f"model_router.{model_name}.{operation}"
        attributes = {
            "llm.model_name": model_name,
            "llm.operation": operation,
            "llm.input_length": len(text),
            "model_router.has_context": context is not None
        }
        
        with self.tracer.start_as_current_span(span_name, attributes=attributes) as span:
            start_time = time.time()
            try:
                yield span
                duration = time.time() - start_time
                self.model_request_duration.record(duration, {
                    "model": model_name,
                    "operation": operation
                })
                self.model_selection_counter.add(1, {"model": model_name})
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                self.model_error_counter.add(1, {
                    "model": model_name,
                    "error_type": type(e).__name__
                })
                raise
    
    @asynccontextmanager
    async def trace_ensemble_routing(self, request_text: str, models: List[str]):
        """Trace ensemble routing operations."""
        span_name = "model_router.ensemble_routing"
        attributes = {
            "model_router.ensemble_models": len(models),
            "model_router.models": ",".join(models),
            "model_router.input_length": len(request_text)
        }
        
        with self.tracer.start_as_current_span(span_name, attributes=attributes) as span:
            start_time = time.time()
            try:
                yield span
                duration = time.time() - start_time
                self.model_request_duration.record(duration, {"operation": "ensemble_routing"})
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                self.model_error_counter.add(1, {
                    "operation": "ensemble_routing",
                    "error_type": type(e).__name__
                })
                raise
    
    @asynccontextmanager
    async def trace_adaptive_routing(self, request_text: str):
        """Trace adaptive routing operations."""
        span_name = "model_router.adaptive_routing"
        attributes = {
            "model_router.input_length": len(request_text)
        }
        
        with self.tracer.start_as_current_span(span_name, attributes=attributes) as span:
            start_time = time.time()
            try:
                yield span
                duration = time.time() - start_time
                self.model_request_duration.record(duration, {"operation": "adaptive_routing"})
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                self.model_error_counter.add(1, {
                    "operation": "adaptive_routing",
                    "error_type": type(e).__name__
                })
                raise
    
    def record_token_usage(self, model_name: str, prompt_tokens: int, completion_tokens: int):
        """Record token usage metrics."""
        total_tokens = prompt_tokens + completion_tokens
        self.token_usage_counter.add(total_tokens, {
            "model": model_name,
            "token_type": "total"
        })
        self.token_usage_counter.add(prompt_tokens, {
            "model": model_name,
            "token_type": "prompt"
        })
        self.token_usage_counter.add(completion_tokens, {
            "model": model_name,
            "token_type": "completion"
        })
    
    def record_model_health_check(self, model_name: str, success: bool, response_time: float):
        """Record model health check metrics."""
        self.model_health_checks.add(1, {
            "model": model_name,
            "success": success
        })
        
        if success:
            self.model_request_duration.record(response_time, {
                "model": model_name,
                "operation": "health_check"
            })
    
    def record_request_size(self, model_name: str, request_size: int, response_size: int):
        """Record request and response size metrics."""
        self.model_request_size.record(request_size, {"model": model_name})
        self.model_response_size.record(response_size, {"model": model_name})
    
    def add_model_selection_attributes(self, span, selected_model: str, 
                                     reasoning: str, confidence: float):
        """Add model selection attributes to span."""
        span.set_attribute("model_router.selected_model", selected_model)
        span.set_attribute("model_router.selection_reasoning", reasoning)
        span.set_attribute("model_router.selection_confidence", confidence)
    
    def add_performance_attributes(self, span, model_name: str, 
                                 response_time: float, token_count: int):
        """Add performance attributes to span."""
        span.set_attribute("llm.model_name", model_name)
        span.set_attribute("llm.response_time_ms", response_time * 1000)
        span.set_attribute("llm.token_count", token_count)
    
    def add_error_attributes(self, span, error_type: str, error_message: str, 
                           model_name: str = None):
        """Add error attributes to span."""
        span.set_attribute("error.type", error_type)
        span.set_attribute("error.message", error_message)
        if model_name:
            span.set_attribute("llm.model_name", model_name)


# Decorators for model router operations
def trace_model_selection(operation_name: str = None):
    """Decorator to trace model selection operations."""
    def decorator(func):
        name = operation_name or f"model_router.{func.__name__}"
        
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


def trace_model_call(model_name: str, operation: str = "generate"):
    """Decorator to trace model calls."""
    def decorator(func):
        name = f"model_router.{model_name}.{operation}"
        
        async def async_wrapper(*args, **kwargs):
            tracer = get_tracing_config().get_tracer()
            attributes = {
                "llm.model_name": model_name,
                "llm.operation": operation
            }
            
            with tracer.start_as_current_span(name, attributes=attributes, kind=SpanKind.CLIENT) as span:
                start_time = time.time()
                try:
                    result = await func(*args, **kwargs)
                    duration = time.time() - start_time
                    
                    # Record metrics
                    model_router_tracing = ModelRouterTracing()
                    model_router_tracing.model_request_duration.record(duration, {
                        "model": model_name,
                        "operation": operation
                    })
                    model_router_tracing.model_selection_counter.add(1, {"model": model_name})
                    
                    span.set_status(Status(StatusCode.OK))
                    span.set_attribute("llm.response_time_ms", duration * 1000)
                    
                    return result
                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    model_router_tracing = ModelRouterTracing()
                    model_router_tracing.model_error_counter.add(1, {
                        "model": model_name,
                        "error_type": type(e).__name__
                    })
                    raise
        
        if hasattr(func, '__call__') and hasattr(func, '__code__') and func.__code__.co_flags & 0x80:
            return async_wrapper
        return func
    
    return decorator


def trace_ensemble_operation(operation_name: str = "ensemble"):
    """Decorator to trace ensemble operations."""
    def decorator(func):
        name = f"model_router.{operation_name}"
        
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


# Global instance
model_router_tracing = ModelRouterTracing()


def get_model_router_tracing() -> ModelRouterTracing:
    """Get the global model router tracing instance."""
    return model_router_tracing


def initialize_model_router_tracing():
    """Initialize model router tracing."""
    config = get_tracing_config()
    config.initialize("model-router")
    
    # Instrument HTTP clients
    manager = get_instrumentation_manager()
    manager.instrument_httpx()
    manager.instrument_requests()
    
    logger.info("Model router tracing initialized")