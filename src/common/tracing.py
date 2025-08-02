"""OpenTelemetry tracing utilities for Tempo integration."""

import os
import functools
from typing import Any, Dict, Optional, Callable
from contextlib import contextmanager

try:
    from opentelemetry import trace
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
    from opentelemetry.instrumentation.psycopg2 import Psycopg2Instrumentor
    from opentelemetry.instrumentation.redis import RedisInstrumentor
    from opentelemetry.instrumentation.requests import RequestsInstrumentor
    from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
    from opentelemetry.propagate import set_global_textmap
    from opentelemetry.propagators.b3 import B3MultiFormat
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    
    TRACING_AVAILABLE = True
except ImportError:
    TRACING_AVAILABLE = False
    trace = None


class TracingManager:
    """Manages OpenTelemetry tracing configuration."""
    
    def __init__(self):
        self.tracer = None
        self.enabled = False
        
    def setup_tracing(self, service_name: str, tempo_endpoint: str = None) -> None:
        """
        Setup OpenTelemetry tracing.
        
        Args:
            service_name: Name of the service
            tempo_endpoint: Tempo OTLP endpoint (defaults to env var)
        """
        if not TRACING_AVAILABLE:
            print(f"Warning: OpenTelemetry not available. Install with: pip install opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp")
            return
            
        # Check if tracing is enabled
        if not os.getenv("TRACING_ENABLED", "true").lower() in ("true", "1", "yes"):
            return
            
        tempo_endpoint = tempo_endpoint or os.getenv("TEMPO_OTLP_ENDPOINT", "http://tempo:4317")
        
        # Create resource
        resource = Resource.create({
            "service.name": service_name,
            "service.version": os.getenv("SERVICE_VERSION", "1.0.0"),
            "deployment.environment": os.getenv("ENVIRONMENT", "development"),
        })
        
        # Create tracer provider
        provider = TracerProvider(resource=resource)
        trace.set_tracer_provider(provider)
        
        # Create OTLP exporter
        otlp_exporter = OTLPSpanExporter(endpoint=tempo_endpoint, insecure=True)
        
        # Create span processor
        span_processor = BatchSpanProcessor(otlp_exporter)
        provider.add_span_processor(span_processor)
        
        # Set propagators
        set_global_textmap(B3MultiFormat())
        
        # Get tracer
        self.tracer = trace.get_tracer(service_name)
        self.enabled = True
        
        print(f"Tracing enabled for {service_name} -> {tempo_endpoint}")
    
    def instrument_fastapi(self, app) -> None:
        """Instrument FastAPI application."""
        if TRACING_AVAILABLE and self.enabled:
            FastAPIInstrumentor.instrument_app(app)
    
    def instrument_libraries(self) -> None:
        """Instrument common libraries."""
        if not TRACING_AVAILABLE or not self.enabled:
            return
            
        try:
            # HTTP clients
            HTTPXClientInstrumentor().instrument()
            RequestsInstrumentor().instrument()
            
            # Databases
            Psycopg2Instrumentor().instrument()
            SQLAlchemyInstrumentor().instrument()
            
            # Redis
            RedisInstrumentor().instrument()
            
        except Exception as e:
            print(f"Warning: Failed to instrument some libraries: {e}")


# Global tracing manager
tracing_manager = TracingManager()


def setup_tracing(service_name: str, tempo_endpoint: str = None) -> None:
    """Setup tracing for the service."""
    tracing_manager.setup_tracing(service_name, tempo_endpoint)


def instrument_fastapi(app) -> None:
    """Instrument FastAPI app for tracing."""
    tracing_manager.instrument_fastapi(app)


def instrument_libraries() -> None:
    """Instrument common libraries for tracing."""
    tracing_manager.instrument_libraries()


def trace_function(name: str = None, attributes: Dict[str, Any] = None):
    """
    Decorator to trace function calls.
    
    Args:
        name: Span name (defaults to function name)
        attributes: Additional span attributes
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            if not tracing_manager.enabled or not tracing_manager.tracer:
                return await func(*args, **kwargs)
                
            span_name = name or f"{func.__module__}.{func.__name__}"
            with tracing_manager.tracer.start_as_current_span(span_name) as span:
                if attributes:
                    span.set_attributes(attributes)
                
                # Add function metadata
                span.set_attribute("function.name", func.__name__)
                span.set_attribute("function.module", func.__module__)
                
                try:
                    result = await func(*args, **kwargs)
                    span.set_attribute("function.result.success", True)
                    return result
                except Exception as e:
                    span.set_attribute("function.result.success", False)
                    span.set_attribute("function.error.type", type(e).__name__)
                    span.set_attribute("function.error.message", str(e))
                    span.record_exception(e)
                    raise
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            if not tracing_manager.enabled or not tracing_manager.tracer:
                return func(*args, **kwargs)
                
            span_name = name or f"{func.__module__}.{func.__name__}"
            with tracing_manager.tracer.start_as_current_span(span_name) as span:
                if attributes:
                    span.set_attributes(attributes)
                
                # Add function metadata
                span.set_attribute("function.name", func.__name__)
                span.set_attribute("function.module", func.__module__)
                
                try:
                    result = func(*args, **kwargs)
                    span.set_attribute("function.result.success", True)
                    return result
                except Exception as e:
                    span.set_attribute("function.result.success", False)
                    span.set_attribute("function.error.type", type(e).__name__)
                    span.set_attribute("function.error.message", str(e))
                    span.record_exception(e)
                    raise
        
        # Return appropriate wrapper based on function type
        if hasattr(func, '__code__') and func.__code__.co_flags & 0x80:  # CO_COROUTINE
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


@contextmanager
def trace_operation(name: str, attributes: Dict[str, Any] = None):
    """
    Context manager for tracing operations.
    
    Args:
        name: Span name
        attributes: Additional span attributes
    """
    if not tracing_manager.enabled or not tracing_manager.tracer:
        yield
        return
        
    with tracing_manager.tracer.start_as_current_span(name) as span:
        if attributes:
            span.set_attributes(attributes)
        
        try:
            yield span
            span.set_attribute("operation.success", True)
        except Exception as e:
            span.set_attribute("operation.success", False)
            span.set_attribute("operation.error.type", type(e).__name__)
            span.set_attribute("operation.error.message", str(e))
            span.record_exception(e)
            raise


def get_current_span():
    """Get the current active span."""
    if not TRACING_AVAILABLE:
        return None
    return trace.get_current_span()


def add_span_attribute(key: str, value: Any) -> None:
    """Add attribute to current span."""
    if not TRACING_AVAILABLE:
        return
        
    span = trace.get_current_span()
    if span:
        span.set_attribute(key, value)


def add_span_event(name: str, attributes: Dict[str, Any] = None) -> None:
    """Add event to current span."""
    if not TRACING_AVAILABLE:
        return
        
    span = trace.get_current_span()
    if span:
        span.add_event(name, attributes or {})


def get_trace_id() -> Optional[str]:
    """Get current trace ID."""
    if not TRACING_AVAILABLE:
        return None
        
    span = trace.get_current_span()
    if span and span.get_span_context().is_valid:
        return format(span.get_span_context().trace_id, "032x")
    return None


def get_span_id() -> Optional[str]:
    """Get current span ID."""
    if not TRACING_AVAILABLE:
        return None
        
    span = trace.get_current_span()
    if span and span.get_span_context().is_valid:
        return format(span.get_span_context().span_id, "016x")
    return None