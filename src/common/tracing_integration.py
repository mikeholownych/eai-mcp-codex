"""
Comprehensive tracing integration for MCP services.
Provides initialization, configuration, and utilities for distributed tracing.
"""

import logging
import os
import sys
from typing import Dict, Any, Optional, List, Callable, Union
from contextlib import contextmanager, asynccontextmanager
import asyncio
import time
import yaml

from .tracing import get_tracing_config, TracingConfig
from .trace_propagation import TracePropagationUtils
from .message_queue_tracing import MessageQueueTracing
from .database_tracing import DatabaseTracing
from .llm_tracing import LLMTracing
from .trace_sampling import TraceSamplingManager
from .trace_exporters import TraceExporterManager, initialize_trace_exporters
from .trace_validation import TraceValidator, TraceHealthChecker, TraceIntegrationTester

logger = logging.getLogger(__name__)


class TracingIntegration:
    """Main integration class for distributed tracing in MCP services."""
    
    def __init__(self, service_name: str, service_version: str = "1.0.0",
                 environment: str = "development", config_path: str = None):
        """
        Initialize tracing integration.
        
        Args:
            service_name: Name of the service
            service_version: Version of the service
            environment: Environment (development, staging, production)
            config_path: Path to tracing configuration file
        """
        self.service_name = service_name
        self.service_version = service_version
        self.environment = environment
        self.config_path = config_path
        self.initialized = False
        
        # Initialize components
        self.tracing_config = get_tracing_config()
        self.propagation_utils = TracePropagationUtils()
        self.message_queue_tracing = MessageQueueTracing()
        self.database_tracing = DatabaseTracing()
        self.llm_tracing = LLMTracing()
        self.sampling_manager = TraceSamplingManager()
        self.exporter_manager = None
        self.validator = TraceValidator()
        self.health_checker = TraceHealthChecker()
        self.integration_tester = TraceIntegrationTester()
        
        # Load configuration
        self._load_configuration()
    
    def _load_configuration(self):
        """Load tracing configuration from file or environment."""
        if self.config_path and os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    config = yaml.safe_load(f)
                    self._apply_configuration(config)
                    logger.info(f"Loaded tracing configuration from {self.config_path}")
            except Exception as e:
                logger.error(f"Failed to load tracing configuration from {self.config_path}: {e}")
        else:
            logger.info("Using default tracing configuration")
    
    def _apply_configuration(self, config: Dict[str, Any]):
        """Apply configuration from loaded config."""
        tracing_config = config.get('tracing', {})
        
        # Apply sampling configuration
        if 'sampling' in tracing_config:
            sampling_config = tracing_config['sampling']
            if 'ratio' in sampling_config:
                base_rate = float(sampling_config['ratio'])
                self.sampling_manager.configure_sampler(base_sample_rate=base_rate)
            
            if 'adaptive' in sampling_config:
                adaptive_config = sampling_config['adaptive']
                if 'target_tps' in adaptive_config:
                    target_tps = int(adaptive_config['target_tps'])
                if 'max_tps' in adaptive_config:
                    max_tps = int(adaptive_config['max_tps'])
                self.sampling_manager.configure_sampler(
                    target_tps=target_tps,
                    max_tps=max_tps
                )
        
        # Apply exporter configuration
        if 'otel' in tracing_config:
            otel_config = tracing_config['otel']
            if 'exporters' in otel_config:
                exporters_config = otel_config['exporters']
                for exporter_name, exporter_config in exporters_config.items():
                    if exporter_name == 'jaeger' and exporter_config.get('enabled', False):
                        os.environ['JAEGER_ENABLED'] = 'true'
                        if 'endpoint' in exporter_config:
                            os.environ['JAEGER_ENDPOINT'] = exporter_config['endpoint']
                    elif exporter_name == 'otlp' and exporter_config.get('enabled', False):
                        os.environ['OTLP_ENABLED'] = 'true'
                        if 'endpoint' in exporter_config:
                            os.environ['OTLP_ENDPOINT'] = exporter_config['endpoint']
                    elif exporter_name == 'zipkin' and exporter_config.get('enabled', False):
                        os.environ['ZIPKIN_ENABLED'] = 'true'
                        if 'endpoint' in exporter_config:
                            os.environ['ZIPKIN_ENDPOINT'] = exporter_config['endpoint']
    
    def initialize(self) -> bool:
        """
        Initialize the complete tracing system.
        
        Returns:
            True if initialization was successful, False otherwise
        """
        try:
            logger.info(f"Initializing tracing for {self.service_name} v{self.service_version}")
            
            # Initialize exporters (no-op in testing mode)
            self.exporter_manager, metrics_collector = initialize_trace_exporters(
                self.service_name, self.service_version, self.environment
            )
            
            # Initialize sampling manager
            self.sampling_manager = TraceSamplingManager()
            
            # Set environment variables for configuration
            os.environ['SERVICE_NAME'] = self.service_name
            os.environ['SERVICE_VERSION'] = self.service_version
            os.environ['ENVIRONMENT'] = self.environment
            
            # Mark as initialized
            self.initialized = True
            
            logger.info(f"Tracing initialized successfully for {self.service_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize tracing for {self.service_name}: {e}")
            return False
    
    def shutdown(self):
        """Shutdown the tracing system."""
        try:
            if self.exporter_manager:
                self.exporter_manager.shutdown()
            
            logger.info(f"Tracing shutdown complete for {self.service_name}")
        except Exception as e:
            logger.error(f"Error during tracing shutdown: {e}")
    
    def get_tracer(self):
        """Get a tracer for the service."""
        if not self.initialized:
            logger.warning("Tracing not initialized, returning default tracer")
        return self.tracing_config.get_tracer()
    
    def get_meter(self):
        """Get a meter for the service."""
        if not self.initialized:
            logger.warning("Tracing not initialized, returning default meter")
        return self.tracing_config.get_meter()
    
    def get_propagation_utils(self) -> TracePropagationUtils:
        """Get trace propagation utilities."""
        return self.propagation_utils
    
    def get_message_queue_tracing(self) -> MessageQueueTracing:
        """Get message queue tracing utilities."""
        return self.message_queue_tracing
    
    def get_database_tracing(self) -> DatabaseTracing:
        """Get database tracing utilities."""
        return self.database_tracing
    
    def get_llm_tracing(self) -> LLMTracing:
        """Get LLM tracing utilities."""
        return self.llm_tracing
    
    def get_sampling_manager(self) -> TraceSamplingManager:
        """Get sampling manager."""
        return self.sampling_manager
    
    def get_validator(self) -> TraceValidator:
        """Get trace validator."""
        return self.validator
    
    def get_health_checker(self) -> TraceHealthChecker:
        """Get health checker."""
        return self.health_checker
    
    def get_integration_tester(self) -> TraceIntegrationTester:
        """Get integration tester."""
        return self.integration_tester
    
    def get_status(self) -> Dict[str, Any]:
        """Get the current status of the tracing system."""
        return {
            "service_name": self.service_name,
            "service_version": self.service_version,
            "environment": self.environment,
            "initialized": self.initialized,
            "timestamp": time.time()
        }
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get the health status of the tracing system."""
        if not self.initialized:
            return {
                "overall_status": "unhealthy",
                "message": "Tracing system not initialized",
                "timestamp": time.time()
            }
        
        return self.health_checker.check_tracing_health()
    
    async def run_integration_tests(self) -> Dict[str, Any]:
        """Run integration tests for the tracing system."""
        if not self.initialized:
            return {
                "overall_status": "failed",
                "message": "Tracing system not initialized",
                "timestamp": time.time()
            }
        
        return await self.integration_tester.run_integration_tests()
    
    @contextmanager
    def trace_operation(self, operation_name: str, attributes: Dict[str, Any] = None):
        """
        Context manager for tracing operations.
        
        Args:
            operation_name: Name of the operation
            attributes: Additional attributes for the span
        """
        tracer = self.get_tracer()
        span_attributes = {
            "service.name": self.service_name,
            "service.version": self.service_version,
            "deployment.environment": self.environment,
            "operation.name": operation_name,
        }
        
        if attributes:
            span_attributes.update(attributes)
        
        with tracer.start_as_current_span(operation_name, attributes=span_attributes) as span:
            try:
                yield span
                span.set_status(Status(StatusCode.OK))
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                raise
    
    @asynccontextmanager
    async def trace_async_operation(self, operation_name: str, attributes: Dict[str, Any] = None):
        """
        Async context manager for tracing operations.
        
        Args:
            operation_name: Name of the operation
            attributes: Additional attributes for the span
        """
        tracer = self.get_tracer()
        span_attributes = {
            "service.name": self.service_name,
            "service.version": self.service_version,
            "deployment.environment": self.environment,
            "operation.name": operation_name,
        }
        
        if attributes:
            span_attributes.update(attributes)
        
        with tracer.start_as_current_span(operation_name, attributes=span_attributes) as span:
            try:
                yield span
                span.set_status(Status(StatusCode.OK))
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                raise


# Global tracing integration instance
_tracing_integration = None


def initialize_tracing(service_name: str, service_version: str = "1.0.0",
                      environment: str = "development", config_path: str = None) -> TracingIntegration:
    """
    Initialize global tracing integration.
    
    Args:
        service_name: Name of the service
        service_version: Version of the service
        environment: Environment (development, staging, production)
        config_path: Path to tracing configuration file
        
    Returns:
        TracingIntegration instance
    """
    global _tracing_integration
    
    if _tracing_integration is None:
        _tracing_integration = TracingIntegration(
            service_name, service_version, environment, config_path
        )
        _tracing_integration.initialize()
    else:
        logger.warning("Tracing integration already initialized")
    
    return _tracing_integration


def get_tracing_integration() -> Optional[TracingIntegration]:
    """
    Get the global tracing integration instance.
    
    Returns:
        TracingIntegration instance or None if not initialized
    """
    return _tracing_integration


def shutdown_tracing():
    """Shutdown the global tracing integration."""
    global _tracing_integration
    
    if _tracing_integration is not None:
        _tracing_integration.shutdown()
        _tracing_integration = None


def get_tracer():
    """Get a tracer for the current service."""
    if _tracing_integration is None:
        logger.warning("Tracing integration not initialized, returning default tracer")
        return get_tracing_config().get_tracer()
    
    return _tracing_integration.get_tracer()


def get_meter():
    """Get a meter for the current service."""
    if _tracing_integration is None:
        logger.warning("Tracing integration not initialized, returning default meter")
        return get_tracing_config().get_meter()
    
    return _tracing_integration.get_meter()


def trace_operation(operation_name: str, attributes: Dict[str, Any] = None):
    """
    Context manager for tracing operations.
    
    Args:
        operation_name: Name of the operation
        attributes: Additional attributes for the span
    """
    if _tracing_integration is None:
        logger.warning("Tracing integration not initialized, using simple context")
        return _dummy_context_manager()
    
    return _tracing_integration.trace_operation(operation_name, attributes)


def trace_async_operation(operation_name: str, attributes: Dict[str, Any] = None):
    """
    Async context manager for tracing operations.
    
    Args:
        operation_name: Name of the operation
        attributes: Additional attributes for the span
    """
    if _tracing_integration is None:
        logger.warning("Tracing integration not initialized, using simple context")
        return _dummy_async_context_manager()
    
    return _tracing_integration.trace_async_operation(operation_name, attributes)


def get_tracing_status() -> Dict[str, Any]:
    """Get the current status of the tracing system."""
    if _tracing_integration is None:
        return {
            "status": "not_initialized",
            "message": "Tracing integration not initialized",
            "timestamp": time.time()
        }
    
    return _tracing_integration.get_status()


def get_tracing_health() -> Dict[str, Any]:
    """Get the health status of the tracing system."""
    if _tracing_integration is None:
        return {
            "overall_status": "unhealthy",
            "message": "Tracing integration not initialized",
            "timestamp": time.time()
        }
    
    return _tracing_integration.get_health_status()


async def run_tracing_integration_tests() -> Dict[str, Any]:
    """Run integration tests for the tracing system."""
    if _tracing_integration is None:
        return {
            "overall_status": "failed",
            "message": "Tracing integration not initialized",
            "timestamp": time.time()
        }
    
    return await _tracing_integration.run_integration_tests()


@contextmanager
def _dummy_context_manager():
    """Dummy context manager when tracing is not initialized."""
    yield None


@asynccontextmanager
async def _dummy_async_context_manager():
    """Dummy async context manager when tracing is not initialized."""
    yield None


# Decorators for tracing
def traced(operation_name: str = None, attributes: Dict[str, Any] = None):
    """
    Decorator to trace function calls.
    
    Args:
        operation_name: Name for the span (defaults to function name)
        attributes: Additional attributes for the span
    """
    def decorator(func):
        op_name = operation_name or f"{func.__module__}.{func.__name__}"
        
        if asyncio.iscoroutinefunction(func):
            async def async_wrapper(*args, **kwargs):
                async with trace_async_operation(op_name, attributes) as span:
                    try:
                        result = await func(*args, **kwargs)
                        return result
                    except Exception as e:
                        if span:
                            span.set_status(Status(StatusCode.ERROR, str(e)))
                            span.record_exception(e)
                        raise
            return async_wrapper
        else:
            def sync_wrapper(*args, **kwargs):
                with trace_operation(op_name, attributes) as span:
                    try:
                        result = func(*args, **kwargs)
                        return result
                    except Exception as e:
                        if span:
                            span.set_status(Status(StatusCode.ERROR, str(e)))
                            span.record_exception(e)
                        raise
            return sync_wrapper
    
    return decorator


# Service-specific initialization functions
def initialize_model_router_tracing(config_path: str = None) -> TracingIntegration:
    """Initialize tracing for model-router service."""
    return initialize_tracing(
        "model-router",
        service_version="1.0.0",
        environment=os.getenv("ENVIRONMENT", "development"),
        config_path=config_path
    )


def initialize_plan_management_tracing(config_path: str = None) -> TracingIntegration:
    """Initialize tracing for plan-management service."""
    return initialize_tracing(
        "plan-management",
        service_version="1.0.0",
        environment=os.getenv("ENVIRONMENT", "development"),
        config_path=config_path
    )


def initialize_git_worktree_tracing(config_path: str = None) -> TracingIntegration:
    """Initialize tracing for git-worktree-manager service."""
    return initialize_tracing(
        "git-worktree-manager",
        service_version="1.0.0",
        environment=os.getenv("ENVIRONMENT", "development"),
        config_path=config_path
    )


def initialize_workflow_orchestrator_tracing(config_path: str = None) -> TracingIntegration:
    """Initialize tracing for workflow-orchestrator service."""
    return initialize_tracing(
        "workflow-orchestrator",
        service_version="1.0.0",
        environment=os.getenv("ENVIRONMENT", "development"),
        config_path=config_path
    )


def initialize_verification_feedback_tracing(config_path: str = None) -> TracingIntegration:
    """Initialize tracing for verification-feedback service."""
    return initialize_tracing(
        "verification-feedback",
        service_version="1.0.0",
        environment=os.getenv("ENVIRONMENT", "development"),
        config_path=config_path
    )


# Convenience functions for common tracing operations
def trace_http_request(method: str, url: str, status_code: int, duration: float):
    """Trace HTTP request."""
    tracer = get_tracer()
    
    with tracer.start_as_current_span("http.request") as span:
        span.set_attribute("http.method", method)
        span.set_attribute("http.url", url)
        span.set_attribute("http.status_code", status_code)
        span.set_attribute("http.duration_ms", duration * 1000)
        
        if status_code >= 400:
            span.set_status(Status(StatusCode.ERROR, f"HTTP {status_code}"))
        else:
            span.set_status(Status(StatusCode.OK))


def trace_database_operation(operation: str, table: str, duration: float, error: str = None):
    """Trace database operation."""
    tracer = get_tracer()
    
    with tracer.start_as_current_span("database.operation") as span:
        span.set_attribute("db.operation", operation)
        span.set_attribute("db.table", table)
        span.set_attribute("db.duration_ms", duration * 1000)
        
        if error:
            span.set_attribute("db.error", error)
            span.set_status(Status(StatusCode.ERROR, error))
        else:
            span.set_status(Status(StatusCode.OK))


def trace_message_queue_operation(operation: str, queue: str, message_count: int, duration: float):
    """Trace message queue operation."""
    tracer = get_tracer()
    
    with tracer.start_as_current_span("message_queue.operation") as span:
        span.set_attribute("messaging.operation", operation)
        span.set_attribute("messaging.queue", queue)
        span.set_attribute("messaging.message_count", message_count)
        span.set_attribute("messaging.duration_ms", duration * 1000)
        span.set_status(Status(StatusCode.OK))


def trace_llm_call(model: str, prompt_length: int, response_length: int, duration: float,
                  token_usage: Dict[str, int] = None, error: str = None):
    """Trace LLM call."""
    tracer = get_tracer()
    
    with tracer.start_as_current_span("llm.call") as span:
        span.set_attribute("llm.model", model)
        span.set_attribute("llm.prompt_length", prompt_length)
        span.set_attribute("llm.response_length", response_length)
        span.set_attribute("llm.duration_ms", duration * 1000)
        
        if token_usage:
            span.set_attribute("llm.tokens.prompt", token_usage.get("prompt_tokens", 0))
            span.set_attribute("llm.tokens.completion", token_usage.get("completion_tokens", 0))
            span.set_attribute("llm.tokens.total", token_usage.get("total_tokens", 0))
        
        if error:
            span.set_attribute("llm.error", error)
            span.set_status(Status(StatusCode.ERROR, error))
        else:
            span.set_status(Status(StatusCode.OK))