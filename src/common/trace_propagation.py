"""
Trace context propagation utilities for MCP services.
Handles HTTP request tracing, message queue tracing, and database correlation.
"""

import logging
from typing import Dict, Any, Optional, List, Callable
from contextlib import contextmanager, asynccontextmanager
import asyncio
import json
import time

from opentelemetry import trace, context
from opentelemetry.trace import (
    Span, 
    SpanKind, 
    Status, 
    StatusCode,
    set_span_in_context,
    get_current_span,
    get_value_from_span
)
from opentelemetry.propagate import extract, inject
from opentelemetry.semconv.trace import SpanAttributes
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
from fastapi import Request, Response
from fastapi.responses import JSONResponse
import httpx
import aiohttp
import redis.asyncio as redis
import asyncpg

from .tracing import get_tracing_config

logger = logging.getLogger(__name__)

# Global propagator instance
_trace_context_propagator = TraceContextTextMapPropagator()


class TracePropagationUtils:
    """Utilities for trace context propagation across different communication channels."""
    
    def __init__(self):
        self.tracer = get_tracing_config().get_tracer()
        self.propagator = _trace_context_propagator
    
    @asynccontextmanager
    async def trace_http_request(self, method: str, url: str, headers: Dict[str, str] = None, 
                               service_name: str = None):
        """Trace an HTTP request with context propagation."""
        span_name = f"http.{method.lower()}"
        attributes = {
            "http.method": method,
            "http.url": url,
            "http.scheme": url.split("://")[0] if "://" in url else "http"
        }
        
        if service_name:
            attributes["peer.service"] = service_name
        
        with self.tracer.start_as_current_span(span_name, kind=SpanKind.CLIENT, attributes=attributes) as span:
            # Prepare headers with trace context
            carrier = {}
            if headers:
                carrier.update(headers)
            
            # Inject trace context into headers
            self.propagator.inject(carrier)
            
            try:
                yield carrier, span
                span.set_status(Status(StatusCode.OK))
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                raise
    
    @asynccontextmanager
    async def trace_http_response(self, request: Request, response: Response):
        """Trace HTTP response processing."""
        span = get_current_span()
        if span:
            span.set_attribute("http.status_code", response.status_code)
            span.set_attribute("http.response_content_length", len(str(response.body)))
            
            # Add response headers
            for key, value in response.headers.items():
                if key.lower() not in ['authorization', 'cookie']:
                    span.set_attribute(f"http.response.header.{key}", value)
        
        try:
            yield
        except Exception as e:
            if span:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
            raise
    
    def extract_trace_context_from_request(self, request: Request) -> Dict[str, Any]:
        """Extract trace context from incoming HTTP request."""
        carrier = {}
        for key, value in request.headers.items():
            carrier[key] = value
        
        try:
            ctx = self.propagator.extract(carrier)
            return ctx
        except Exception as e:
            logger.warning(f"Failed to extract trace context from request: {e}")
            return {}
    
    def inject_trace_context_to_headers(self, headers: Dict[str, str] = None) -> Dict[str, str]:
        """Inject trace context into HTTP headers."""
        carrier = headers or {}
        try:
            self.propagator.inject(carrier)
            return carrier
        except Exception as e:
            logger.warning(f"Failed to inject trace context to headers: {e}")
            return headers or {}
    
    @asynccontextmanager
    async def trace_message_queue_operation(self, operation: str, queue_name: str, 
                                         message_id: str = None, correlation_id: str = None):
        """Trace message queue operations with context propagation."""
        span_name = f"message_queue.{operation}"
        attributes = {
            "messaging.system": "rabbitmq",
            "messaging.destination": queue_name,
            "messaging.operation": operation
        }
        
        if message_id:
            attributes["messaging.message_id"] = message_id
        if correlation_id:
            attributes["messaging.conversation_id"] = correlation_id
        
        with self.tracer.start_as_current_span(span_name, attributes=attributes) as span:
            try:
                yield span
                span.set_status(Status(StatusCode.OK))
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                raise
    
    def inject_trace_context_to_message(self, message: Dict[str, Any], 
                                      headers_key: str = "headers") -> Dict[str, Any]:
        """Inject trace context into message headers."""
        if headers_key not in message:
            message[headers_key] = {}
        
        carrier = message[headers_key]
        try:
            self.propagator.inject(carrier)
            return message
        except Exception as e:
            logger.warning(f"Failed to inject trace context to message: {e}")
            return message
    
    def extract_trace_context_from_message(self, message: Dict[str, Any], 
                                        headers_key: str = "headers") -> Dict[str, Any]:
        """Extract trace context from message headers."""
        if headers_key not in message:
            return {}
        
        carrier = message.get(headers_key, {})
        try:
            ctx = self.propagator.extract(carrier)
            return ctx
        except Exception as e:
            logger.warning(f"Failed to extract trace context from message: {e}")
            return {}
    
    @asynccontextmanager
    async def trace_database_operation(self, operation: str, table_name: str, 
                                    query_type: str = "query", database_name: str = None):
        """Trace database operations with correlation."""
        span_name = f"database.{operation}"
        attributes = {
            "db.system": "postgresql",
            "db.name": database_name or "unknown",
            "db.operation": operation,
            "db.sql.table": table_name,
            "db.statement_type": query_type
        }
        
        with self.tracer.start_as_current_span(span_name, attributes=attributes) as span:
            start_time = time.time()
            try:
                yield span
                duration = time.time() - start_time
                span.set_attribute("db.duration_ms", duration * 1000)
                span.set_status(Status(StatusCode.OK))
            except Exception as e:
                duration = time.time() - start_time
                span.set_attribute("db.duration_ms", duration * 1000)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                raise
    
    def add_database_correlation_attributes(self, span, connection_id: str, 
                                          transaction_id: str = None, query_hash: str = None):
        """Add database correlation attributes to span."""
        if span:
            span.set_attribute("db.connection_id", connection_id)
            if transaction_id:
                span.set_attribute("db.transaction_id", transaction_id)
            if query_hash:
                span.set_attribute("db.statement_hash", query_hash)
    
    @contextmanager
    def trace_service_communication(self, target_service: str, operation: str, 
                                 communication_type: str = "http"):
        """Trace inter-service communication."""
        span_name = f"service_communication.{operation}"
        attributes = {
            "service_communication.target_service": target_service,
            "service_communication.operation": operation,
            "service_communication.type": communication_type
        }
        
        with self.tracer.start_as_current_span(span_name, attributes=attributes) as span:
            start_time = time.time()
            try:
                yield span
                duration = time.time() - start_time
                span.set_attribute("service_communication.duration_ms", duration * 1000)
                span.set_status(Status(StatusCode.OK))
            except Exception as e:
                duration = time.time() - start_time
                span.set_attribute("service_communication.duration_ms", duration * 1000)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                raise


class HTTPXTracingMiddleware:
    """Middleware for tracing HTTPX client requests."""
    
    def __init__(self, propagation_utils: TracePropagationUtils):
        self.propagation_utils = propagation_utils
    
    async def __call__(self, request: httpx.Request) -> httpx.Request:
        """Middleware to add tracing to HTTPX requests."""
        method = request.method
        url = str(request.url)
        
        async with self.propagation_utils.trace_http_request(method, url) as (headers, span):
            # Add trace context to request headers
            for key, value in headers.items():
                request.headers[key] = value
            
            # Add additional attributes
            span.set_attribute("http.request_content_length", len(request.content or ""))
            
            return request


class AioHTTPTracingMiddleware:
    """Middleware for tracing aiohttp client requests."""
    
    def __init__(self, propagation_utils: TracePropagationUtils):
        self.propagation_utils = propagation_utils
    
    async def on_request_start(self, session, trace_config_ctx, params):
        """Called when request starts."""
        method = params.method
        url = str(params.url)
        
        async with self.propagation_utils.trace_http_request(method, url) as (headers, span):
            # Add trace context to request headers
            for key, value in headers.items():
                params.headers[key] = value
            
            # Store span in trace config context
            trace_config_ctx.span = span
    
    async def on_request_end(self, session, trace_config_ctx, params):
        """Called when request ends."""
        span = getattr(trace_config_ctx, 'span', None)
        if span:
            span.set_attribute("http.status_code", params.response.status)
            span.set_status(Status(StatusCode.OK))
    
    async def on_request_exception(self, session, trace_config_ctx, params):
        """Called when request fails."""
        span = getattr(trace_config_ctx, 'span', None)
        if span:
            span.set_status(Status(StatusCode.ERROR, str(params.exception)))
            span.record_exception(params.exception)


class FastAPITracingMiddleware:
    """Middleware for tracing FastAPI requests."""
    
    def __init__(self, propagation_utils: TracePropagationUtils):
        self.propagation_utils = propagation_utils
    
    async def __call__(self, request: Request, call_next):
        """Middleware to add tracing to FastAPI requests."""
        # Extract trace context from incoming request
        ctx = self.propagation_utils.extract_trace_context_from_request(request)
        
        # Create span for the request
        span_name = f"{request.method} {request.url.path}"
        attributes = {
            "http.method": request.method,
            "http.url": str(request.url),
            "http.scheme": request.url.scheme,
            "http.host": request.url.hostname,
            "http.target": request.url.path,
            "net.host.port": request.url.port
        }
        
        with self.tracer.start_as_current_span(span_name, kind=SpanKind.SERVER, attributes=attributes) as span:
            # Add request attributes
            span.set_attribute("http.request_content_length", request.headers.get("content-length", 0))
            
            # Add user agent
            user_agent = request.headers.get("user-agent", "")
            if user_agent:
                span.set_attribute("http.user_agent", user_agent)
            
            try:
                # Process the request
                response = await call_next(request)
                
                # Add response attributes
                span.set_attribute("http.status_code", response.status_code)
                span.set_attribute("http.response_content_length", response.headers.get("content-length", 0))
                
                # Determine span status based on response code
                if 400 <= response.status_code < 500:
                    span.set_status(Status(StatusCode.ERROR, f"Client error: {response.status_code}"))
                elif response.status_code >= 500:
                    span.set_status(Status(StatusCode.ERROR, f"Server error: {response.status_code}"))
                else:
                    span.set_status(Status(StatusCode.OK))
                
                return response
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                raise


# Decorators for trace propagation
def trace_http_client(service_name: str = None):
    """Decorator to trace HTTP client calls."""
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            propagation_utils = TracePropagationUtils()
            
            # Extract URL and method from kwargs or args
            url = kwargs.get('url') or (args[0] if args else None)
            method = kwargs.get('method') or 'GET'
            
            if not url:
                return await func(*args, **kwargs)
            
            async with propagation_utils.trace_http_request(method, url, service_name=service_name) as (headers, span):
                # Add headers to kwargs
                if 'headers' not in kwargs:
                    kwargs['headers'] = {}
                kwargs['headers'].update(headers)
                
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


def trace_message_queue_operation(queue_name: str, operation: str):
    """Decorator to trace message queue operations."""
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            propagation_utils = TracePropagationUtils()
            
            # Extract message ID and correlation ID from kwargs
            message_id = kwargs.get('message_id')
            correlation_id = kwargs.get('correlation_id')
            
            async with propagation_utils.trace_message_queue_operation(
                operation, queue_name, message_id, correlation_id
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


def trace_database_operation(table_name: str, operation: str, query_type: str = "query"):
    """Decorator to trace database operations."""
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            propagation_utils = TracePropagationUtils()
            
            async with propagation_utils.trace_database_operation(
                operation, table_name, query_type
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
trace_propagation_utils = TracePropagationUtils()


def get_trace_propagation_utils() -> TracePropagationUtils:
    """Get the global trace propagation utilities instance."""
    return trace_propagation_utils


def create_httpx_tracing_middleware():
    """Create HTTPX tracing middleware."""
    return HTTPXTracingMiddleware(trace_propagation_utils)


def create_aiohttp_tracing_middleware():
    """Create aiohttp tracing middleware."""
    return AioHTTPTracingMiddleware(trace_propagation_utils)


def create_fastapi_tracing_middleware():
    """Create FastAPI tracing middleware."""
    return FastAPITracingMiddleware(trace_propagation_utils)