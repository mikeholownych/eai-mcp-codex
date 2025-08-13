"""
LLM tracing utilities for MCP services.
Provides custom spans and metrics for LLM operations, model calls, and token usage.
"""

import logging
from typing import Dict, Any, List
from contextlib import asynccontextmanager
import time
import hashlib
import re

from opentelemetry.trace import (
    Span, 
    SpanKind, 
    Status, 
    StatusCode
)
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

from .tracing import get_tracing_config
from .trace_propagation import TracePropagationUtils

logger = logging.getLogger(__name__)

# Global propagator instance
_trace_context_propagator = TraceContextTextMapPropagator()


class LLMTracing:
    """Tracing utilities for LLM operations."""
    
    def __init__(self):
        self.tracer = get_tracing_config().get_tracer()
        self.meter = get_tracing_config().get_meter()
        self.propagator = _trace_context_propagator
        self.propagation_utils = TracePropagationUtils()
        self._initialize_metrics()
        
        # Privacy settings
        self.capture_prompts = False  # Privacy consideration
        self.capture_responses = False  # Privacy consideration
        self.capture_tokens = True
        self.capture_model_params = True
    
    def _initialize_metrics(self):
        """Initialize metrics for LLM operations."""
        # Create counters
        self.llm_request_counter = self.meter.create_counter(
            "llm_requests_total",
            description="Total number of LLM requests"
        )
        
        self.llm_token_counter = self.meter.create_counter(
            "llm_tokens_total",
            description="Total number of tokens processed"
        )
        
        self.llm_error_counter = self.meter.create_counter(
            "llm_errors_total",
            description="Total number of LLM errors"
        )
        
        self.llm_cache_hit_counter = self.meter.create_counter(
            "llm_cache_hits_total",
            description="Total number of LLM cache hits"
        )
        
        self.llm_cache_miss_counter = self.meter.create_counter(
            "llm_cache_misses_total",
            description="Total number of LLM cache misses"
        )
        
        # Create histograms
        self.llm_request_duration = self.meter.create_histogram(
            "llm_request_duration_seconds",
            description="Duration of LLM requests"
        )
        
        self.llm_token_usage = self.meter.create_histogram(
            "llm_token_usage",
            description="Token usage per request"
        )
        
        self.llm_time_to_first_token = self.meter.create_histogram(
            "llm_time_to_first_token_seconds",
            description="Time to first token generation"
        )
        
        self.llm_tokens_per_second = self.meter.create_histogram(
            "llm_tokens_per_second",
            description="Tokens generated per second"
        )
        
        # Create up-down counters
        self.llm_active_requests = self.meter.create_up_down_counter(
            "llm_active_requests",
            description="Number of active LLM requests"
        )
    
    @asynccontextmanager
    async def trace_llm_request(self, model_name: str, request_type: str = "completion",
                              prompt: str = None, parameters: Dict[str, Any] = None,
                              request_id: str = None):
        """Trace LLM request execution."""
        span_name = f"llm.{request_type}"
        attributes = {
            "llm.model_name": model_name,
            "llm.request_type": request_type,
            "llm.system": "mcp"
        }
        
        if request_id:
            attributes["llm.request_id"] = request_id
        
        if prompt and self.capture_prompts:
            # Sanitize prompt for privacy
            sanitized_prompt = self._sanitize_prompt(prompt)
            attributes["llm.prompt"] = sanitized_prompt
            attributes["llm.prompt_length"] = len(prompt)
        
        if parameters and self.capture_model_params:
            # Add model parameters as attributes
            for key, value in parameters.items():
                if isinstance(value, (str, int, float, bool)):
                    attributes[f"llm.param.{key}"] = value
        
        with self.tracer.start_as_current_span(span_name, kind=SpanKind.CLIENT, attributes=attributes) as span:
            start_time = time.time()
            self.llm_active_requests.add(1)
            
            try:
                yield span
                duration = time.time() - start_time
                self.llm_request_duration.record(duration, {"model_name": model_name, "request_type": request_type})
                self.llm_request_counter.add(1, {"model_name": model_name, "request_type": request_type})
                span.set_status(Status(StatusCode.OK))
            except Exception as e:
                duration = time.time() - start_time
                self.llm_request_duration.record(duration, {"model_name": model_name, "request_type": request_type})
                self.llm_request_counter.add(1, {"model_name": model_name, "request_type": request_type})
                self.llm_error_counter.add(1, {"model_name": model_name, "error_type": type(e).__name__})
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                raise
            finally:
                self.llm_active_requests.add(-1)
    
    @asynccontextmanager
    async def trace_llm_response(self, model_name: str, response_text: str = None,
                               token_usage: Dict[str, int] = None,
                               response_id: str = None):
        """Trace LLM response processing."""
        span_name = "llm.response"
        attributes = {
            "llm.model_name": model_name,
            "llm.system": "mcp"
        }
        
        if response_id:
            attributes["llm.response_id"] = response_id
        
        if response_text and self.capture_responses:
            # Sanitize response for privacy
            sanitized_response = self._sanitize_response(response_text)
            attributes["llm.response"] = sanitized_response
            attributes["llm.response_length"] = len(response_text)
        
        if token_usage and self.capture_tokens:
            attributes["llm.tokens.prompt"] = token_usage.get("prompt_tokens", 0)
            attributes["llm.tokens.completion"] = token_usage.get("completion_tokens", 0)
            attributes["llm.tokens.total"] = token_usage.get("total_tokens", 0)
        
        with self.tracer.start_as_current_span(span_name, attributes=attributes) as span:
            start_time = time.time()
            try:
                yield span
                duration = time.time() - start_time
                
                # Record token usage metrics
                if token_usage and self.capture_tokens:
                    prompt_tokens = token_usage.get("prompt_tokens", 0)
                    completion_tokens = token_usage.get("completion_tokens", 0)
                    total_tokens = token_usage.get("total_tokens", 0)
                    
                    self.llm_token_counter.add(prompt_tokens, {"token_type": "prompt", "model_name": model_name})
                    self.llm_token_counter.add(completion_tokens, {"token_type": "completion", "model_name": model_name})
                    self.llm_token_counter.add(total_tokens, {"token_type": "total", "model_name": model_name})
                    self.llm_token_usage.record(total_tokens, {"model_name": model_name})
                
                span.set_status(Status(StatusCode.OK))
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                raise
    
    @asynccontextmanager
    async def trace_llm_streaming(self, model_name: str, request_type: str = "streaming",
                                prompt: str = None, parameters: Dict[str, Any] = None):
        """Trace LLM streaming operations."""
        span_name = f"llm.{request_type}"
        attributes = {
            "llm.model_name": model_name,
            "llm.request_type": request_type,
            "llm.streaming": True,
            "llm.system": "mcp"
        }
        
        if prompt and self.capture_prompts:
            sanitized_prompt = self._sanitize_prompt(prompt)
            attributes["llm.prompt"] = sanitized_prompt
            attributes["llm.prompt_length"] = len(prompt)
        
        if parameters and self.capture_model_params:
            for key, value in parameters.items():
                if isinstance(value, (str, int, float, bool)):
                    attributes[f"llm.param.{key}"] = value
        
        with self.tracer.start_as_current_span(span_name, kind=SpanKind.CLIENT, attributes=attributes) as span:
            start_time = time.time()
            first_token_time = None
            total_tokens = 0
            
            try:
                yield span
                duration = time.time() - start_time
                self.llm_request_duration.record(duration, {"model_name": model_name, "request_type": request_type})
                self.llm_request_counter.add(1, {"model_name": model_name, "request_type": request_type})
                
                # Record streaming metrics
                if first_token_time:
                    time_to_first_token = first_token_time - start_time
                    self.llm_time_to_first_token.record(time_to_first_token, {"model_name": model_name})
                
                if total_tokens > 0 and duration > 0:
                    tokens_per_second = total_tokens / duration
                    self.llm_tokens_per_second.record(tokens_per_second, {"model_name": model_name})
                
                span.set_status(Status(StatusCode.OK))
            except Exception as e:
                duration = time.time() - start_time
                self.llm_request_duration.record(duration, {"model_name": model_name, "request_type": request_type})
                self.llm_request_counter.add(1, {"model_name": model_name, "request_type": request_type})
                self.llm_error_counter.add(1, {"model_name": model_name, "error_type": type(e).__name__})
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                raise
    
    @asynccontextmanager
    async def trace_llm_embedding(self, model_name: str, input_text: str,
                               embedding_dimensions: int = None):
        """Trace LLM embedding operations."""
        span_name = "llm.embedding"
        attributes = {
            "llm.model_name": model_name,
            "llm.request_type": "embedding",
            "llm.system": "mcp",
            "llm.input_length": len(input_text)
        }
        
        if embedding_dimensions:
            attributes["llm.embedding_dimensions"] = embedding_dimensions
        
        with self.tracer.start_as_current_span(span_name, kind=SpanKind.CLIENT, attributes=attributes) as span:
            start_time = time.time()
            try:
                yield span
                duration = time.time() - start_time
                self.llm_request_duration.record(duration, {"model_name": model_name, "request_type": "embedding"})
                self.llm_request_counter.add(1, {"model_name": model_name, "request_type": "embedding"})
                span.set_status(Status(StatusCode.OK))
            except Exception as e:
                duration = time.time() - start_time
                self.llm_request_duration.record(duration, {"model_name": model_name, "request_type": "embedding"})
                self.llm_request_counter.add(1, {"model_name": model_name, "request_type": "embedding"})
                self.llm_error_counter.add(1, {"model_name": model_name, "error_type": type(e).__name__})
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                raise
    
    @asynccontextmanager
    async def trace_llm_cache_operation(self, operation: str, cache_key: str,
                                     model_name: str = None):
        """Trace LLM cache operations."""
        span_name = f"llm.cache.{operation}"
        attributes = {
            "llm.cache.operation": operation,
            "llm.cache.key": self._hash_key(cache_key),
            "llm.system": "mcp"
        }
        
        if model_name:
            attributes["llm.model_name"] = model_name
        
        with self.tracer.start_as_current_span(span_name, attributes=attributes) as span:
            start_time = time.time()
            try:
                yield span
                duration = time.time() - start_time
                
                # Record cache metrics
                if operation == "get":
                    self.llm_cache_hit_counter.add(1, {"model_name": model_name or "unknown"})
                elif operation == "set":
                    self.llm_cache_miss_counter.add(1, {"model_name": model_name or "unknown"})
                
                span.set_status(Status(StatusCode.OK))
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                raise
    
    @asynccontextmanager
    async def trace_llm_model_routing(self, input_text: str, selected_model: str,
                                    available_models: List[str] = None,
                                    routing_strategy: str = "default"):
        """Trace LLM model routing decisions."""
        span_name = "llm.model_routing"
        attributes = {
            "llm.routing.strategy": routing_strategy,
            "llm.routing.selected_model": selected_model,
            "llm.input_length": len(input_text),
            "llm.system": "mcp"
        }
        
        if available_models:
            attributes["llm.routing.available_models"] = ",".join(available_models)
        
        with self.tracer.start_as_current_span(span_name, attributes=attributes) as span:
            start_time = time.time()
            try:
                yield span
                duration = time.time() - start_time
                span.set_attribute("llm.routing.duration_ms", duration * 1000)
                span.set_status(Status(StatusCode.OK))
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                raise
    
    def _sanitize_prompt(self, prompt: str) -> str:
        """Sanitize prompt for privacy."""
        # Remove sensitive information
        sensitive_patterns = [
            r'\bpassword\s*[:=]\s*[^\s]+',
            r'\btoken\s*[:=]\s*[^\s]+',
            r'\bapi[_-]?key\s*[:=]\s*[^\s]+',
            r'\bsecret\s*[:=]\s*[^\s]+',
            r'\bauthorization\s*[:=]\s*[^\s]+',
            r'\bauth\s*[:=]\s*[^\s]+',
            r'\bcredit_card\s*[:=]\s*[^\s]+',
            r'\bssn\s*[:=]\s*[^\s]+',
            r'\bemail\s*[:=]\s*[^\s]+@[^\s]+',
        ]
        
        sanitized = prompt
        for pattern in sensitive_patterns:
            sanitized = re.sub(pattern, '***', sanitized, flags=re.IGNORECASE)
        
        # Truncate long prompts
        if len(sanitized) > 1000:
            sanitized = sanitized[:1000] + "..."
        
        return sanitized
    
    def _sanitize_response(self, response: str) -> str:
        """Sanitize response for privacy."""
        # Similar to prompt sanitization but for responses
        sensitive_patterns = [
            r'\bpassword\s*[:=]\s*[^\s]+',
            r'\btoken\s*[:=]\s*[^\s]+',
            r'\bapi[_-]?key\s*[:=]\s*[^\s]+',
            r'\bsecret\s*[:=]\s*[^\s]+',
            r'\bauthorization\s*[:=]\s*[^\s]+',
            r'\bauth\s*[:=]\s*[^\s]+',
            r'\bcredit_card\s*[:=]\s*\d+',
            r'\bssn\s*[:=]\s*\d{3}[-]?\d{2}[-]?\d{4}',
            r'\bemail\s*[:=]\s*[^\s]+@[^\s]+',
        ]
        
        sanitized = response
        for pattern in sensitive_patterns:
            sanitized = re.sub(pattern, '***', sanitized, flags=re.IGNORECASE)
        
        # Truncate long responses
        if len(sanitized) > 1000:
            sanitized = sanitized[:1000] + "..."
        
        return sanitized
    
    def _hash_key(self, key: str) -> str:
        """Generate hash for cache key."""
        return hashlib.md5(key.encode('utf-8')).hexdigest()
    
    def record_token_usage(self, model_name: str, token_usage: Dict[str, int]):
        """Record token usage metrics."""
        if not self.capture_tokens:
            return
        
        prompt_tokens = token_usage.get("prompt_tokens", 0)
        completion_tokens = token_usage.get("completion_tokens", 0)
        total_tokens = token_usage.get("total_tokens", 0)
        
        self.llm_token_counter.add(prompt_tokens, {"token_type": "prompt", "model_name": model_name})
        self.llm_token_counter.add(completion_tokens, {"token_type": "completion", "model_name": model_name})
        self.llm_token_counter.add(total_tokens, {"token_type": "total", "model_name": model_name})
        self.llm_token_usage.record(total_tokens, {"model_name": model_name})
    
    def record_streaming_metrics(self, model_name: str, duration: float, 
                               time_to_first_token: float, total_tokens: int):
        """Record streaming metrics."""
        self.llm_time_to_first_token.record(time_to_first_token, {"model_name": model_name})
        
        if duration > 0:
            tokens_per_second = total_tokens / duration
            self.llm_tokens_per_second.record(tokens_per_second, {"model_name": model_name})
    
    def add_llm_attributes_to_span(self, span: Span, model_name: str, 
                                 request_id: str = None, response_id: str = None,
                                 token_usage: Dict[str, int] = None):
        """Add LLM attributes to span."""
        span.set_attribute("llm.model_name", model_name)
        span.set_attribute("llm.system", "mcp")
        
        if request_id:
            span.set_attribute("llm.request_id", request_id)
        if response_id:
            span.set_attribute("llm.response_id", response_id)
        if token_usage and self.capture_tokens:
            span.set_attribute("llm.tokens.prompt", token_usage.get("prompt_tokens", 0))
            span.set_attribute("llm.tokens.completion", token_usage.get("completion_tokens", 0))
            span.set_attribute("llm.tokens.total", token_usage.get("total_tokens", 0))
    
    def add_model_parameters_to_span(self, span: Span, parameters: Dict[str, Any]):
        """Add model parameters to span."""
        if not self.capture_model_params:
            return
        
        for key, value in parameters.items():
            if isinstance(value, (str, int, float, bool)):
                span.set_attribute(f"llm.param.{key}", value)
    
    def add_performance_attributes_to_span(self, span: Span, duration: float,
                                         time_to_first_token: float = None,
                                         tokens_per_second: float = None):
        """Add performance attributes to span."""
        span.set_attribute("llm.duration_ms", duration * 1000)
        
        if time_to_first_token is not None:
            span.set_attribute("llm.time_to_first_token_ms", time_to_first_token * 1000)
        
        if tokens_per_second is not None:
            span.set_attribute("llm.tokens_per_second", tokens_per_second)


class LLMRequestTracer:
    """Context manager for tracing LLM requests."""
    
    def __init__(self, llm_tracing: LLMTracing, model_name: str, 
                 request_type: str = "completion", prompt: str = None,
                 parameters: Dict[str, Any] = None, request_id: str = None):
        self.llm_tracing = llm_tracing
        self.model_name = model_name
        self.request_type = request_type
        self.prompt = prompt
        self.parameters = parameters
        self.request_id = request_id
        self.span = None
        self.start_time = None
    
    async def __aenter__(self):
        """Enter context manager."""
        self.start_time = time.time()
        
        # Create request span
        span_name = f"llm.{self.request_type}"
        attributes = {
            "llm.model_name": self.model_name,
            "llm.request_type": self.request_type,
            "llm.system": "mcp"
        }
        
        if self.request_id:
            attributes["llm.request_id"] = self.request_id
        
        if self.prompt and self.llm_tracing.capture_prompts:
            sanitized_prompt = self.llm_tracing._sanitize_prompt(self.prompt)
            attributes["llm.prompt"] = sanitized_prompt
            attributes["llm.prompt_length"] = len(self.prompt)
        
        if self.parameters and self.llm_tracing.capture_model_params:
            for key, value in self.parameters.items():
                if isinstance(value, (str, int, float, bool)):
                    attributes[f"llm.param.{key}"] = value
        
        self.span = self.llm_tracing.tracer.start_as_current_span(
            span_name, kind=SpanKind.CLIENT, attributes=attributes
        )
        self.llm_tracing.llm_active_requests.add(1)
        
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager."""
        duration = time.time() - self.start_time
        self.llm_tracing.llm_active_requests.add(-1)
        
        if self.span:
            if exc_type is None:
                self.llm_tracing.llm_request_duration.record(
                    duration, {"model_name": self.model_name, "request_type": self.request_type}
                )
                self.llm_tracing.llm_request_counter.add(
                    1, {"model_name": self.model_name, "request_type": self.request_type}
                )
                self.span.set_status(Status(StatusCode.OK))
            else:
                self.llm_tracing.llm_request_duration.record(
                    duration, {"model_name": self.model_name, "request_type": self.request_type}
                )
                self.llm_tracing.llm_request_counter.add(
                    1, {"model_name": self.model_name, "request_type": self.request_type}
                )
                self.llm_tracing.llm_error_counter.add(
                    1, {"model_name": self.model_name, "error_type": exc_type.__name__}
                )
                self.span.set_status(Status(StatusCode.ERROR, str(exc_val)))
                self.span.record_exception(exc_val)
            
            self.span.end()
    
    def record_response(self, response_text: str = None, token_usage: Dict[str, int] = None,
                       response_id: str = None):
        """Record response information."""
        if not self.span:
            return
        
        # Create response span
        response_span_name = "llm.response"
        response_attributes = {
            "llm.model_name": self.model_name,
            "llm.system": "mcp"
        }
        
        if response_id:
            response_attributes["llm.response_id"] = response_id
        
        if response_text and self.llm_tracing.capture_responses:
            sanitized_response = self.llm_tracing._sanitize_response(response_text)
            response_attributes["llm.response"] = sanitized_response
            response_attributes["llm.response_length"] = len(response_text)
        
        if token_usage and self.llm_tracing.capture_tokens:
            response_attributes["llm.tokens.prompt"] = token_usage.get("prompt_tokens", 0)
            response_attributes["llm.tokens.completion"] = token_usage.get("completion_tokens", 0)
            response_attributes["llm.tokens.total"] = token_usage.get("total_tokens", 0)
            
            # Record token usage metrics
            self.llm_tracing.record_token_usage(self.model_name, token_usage)
        
        with self.llm_tracing.tracer.start_as_current_span(
            response_span_name, attributes=response_attributes
        ) as response_span:
            response_span.set_status(Status(StatusCode.OK))


# Decorators for LLM operations
def trace_llm_request(model_name: str, request_type: str = "completion"):
    """Decorator to trace LLM requests."""
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            llm_tracing = LLMTracing()
            
            # Extract prompt and parameters from kwargs
            prompt = kwargs.get('prompt') or (args[0] if args else None)
            parameters = kwargs.get('parameters') or {}
            request_id = kwargs.get('request_id')
            
            async with llm_tracing.trace_llm_request(
                model_name, request_type, prompt, parameters, request_id
            ) as span:
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


def trace_llm_response(model_name: str):
    """Decorator to trace LLM responses."""
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            llm_tracing = LLMTracing()
            
            # Extract response information from kwargs
            response_text = kwargs.get('response_text') or (args[0] if args else None)
            token_usage = kwargs.get('token_usage') or {}
            response_id = kwargs.get('response_id')
            
            async with llm_tracing.trace_llm_response(
                model_name, response_text, token_usage, response_id
            ) as span:
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


def trace_llm_embedding(model_name: str):
    """Decorator to trace LLM embedding operations."""
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            llm_tracing = LLMTracing()
            
            # Extract input text from kwargs
            input_text = kwargs.get('input_text') or (args[0] if args else None)
            embedding_dimensions = kwargs.get('embedding_dimensions')
            
            async with llm_tracing.trace_llm_embedding(
                model_name, input_text, embedding_dimensions
            ) as span:
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


def trace_llm_model_routing():
    """Decorator to trace LLM model routing."""
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            llm_tracing = LLMTracing()
            
            # Extract routing information from kwargs
            input_text = kwargs.get('input_text') or (args[0] if args else None)
            selected_model = kwargs.get('selected_model')
            available_models = kwargs.get('available_models', [])
            routing_strategy = kwargs.get('routing_strategy', 'default')
            
            async with llm_tracing.trace_llm_model_routing(
                input_text, selected_model, available_models, routing_strategy
            ) as span:
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
llm_tracing = LLMTracing()


def get_llm_tracing() -> LLMTracing:
    """Get the global LLM tracing instance."""
    return llm_tracing


def create_llm_request_tracer(model_name: str, request_type: str = "completion",
                            prompt: str = None, parameters: Dict[str, Any] = None,
                            request_id: str = None):
    """Create an LLM request tracer context manager."""
    return LLMRequestTracer(llm_tracing, model_name, request_type, prompt, parameters, request_id)