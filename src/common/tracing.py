"""
Shared OpenTelemetry tracing configuration for all MCP services.
Provides centralized setup and instrumentation for distributed tracing.
"""

import os
import yaml
import logging
from typing import Dict, Any
from contextlib import contextmanager
from functools import wraps

from opentelemetry import trace, metrics
from opentelemetry.trace import Status, StatusCode, SpanKind
from opentelemetry.sdk.trace import TracerProvider, sampling
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.asyncpg import AsyncPGInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.semconv.resource import ResourceAttributes
from opentelemetry.sdk.resources import Resource
from opentelemetry.propagate import set_global_textmap, get_global_textmap
from opentelemetry.propagators.composite import CompositePropagator
from opentelemetry.propagators.b3 import B3MultiFormat
from opentelemetry.propagators.jaeger import JaegerPropagator
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
from fastapi import Request, Response

logger = logging.getLogger(__name__)


class TracingConfig:
    """Configuration for OpenTelemetry tracing."""
    
    def __init__(self, config_path: str = "config/tracing.yml"):
        self.config_path = config_path
        self.config = self._load_config()
        self.tracer_provider = None
        self.meter_provider = None
        self.tracer = None
        self.meter = None
        self._initialized = False
        
    def _load_config(self) -> Dict[str, Any]:
        """Load tracing configuration from YAML file."""
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            return config.get('tracing', {})
        except Exception as e:
            logger.warning(f"Failed to load tracing config from {self.config_path}: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default tracing configuration."""
        return {
            'enabled': True,
            'service_name': os.getenv('SERVICE_NAME', 'unknown-service'),
            'service_version': os.getenv('SERVICE_VERSION', '1.0.0'),
            'environment': os.getenv('ENVIRONMENT', 'development'),
            'otel': {
                'collector': {
                    'endpoint': 'http://jaeger-collector:14268/api/traces',
                    'timeout': '10s',
                    'compression': 'gzip'
                },
                'exporters': {
                    'jaeger': {
                        'enabled': True,
                        'endpoint': 'http://jaeger:14268/api/traces'
                    },
                    'otlp': {
                        'enabled': False,
                        'endpoint': 'http://otel-collector:4317',
                        'insecure': True
                    }
                },
                'sampling': {
                    'ratio': 1.0,
                    'adaptive': {
                        'enabled': True,
                        'target_tps': 10,
                        'max_tps': 100
                    }
                }
            }
        }
    
    def initialize(self, service_name: str = None) -> None:
        """Initialize OpenTelemetry tracing."""
        if self._initialized:
            return
        
        # In testing mode, return no-op tracer/meter without exporters
        testing_mode = os.getenv('TESTING_MODE', '').lower() == 'true'
        service_name = service_name or self.config.get('service_name', 'unknown-service')
        if testing_mode:
            self.tracer = trace.get_tracer(service_name)
            self.meter = metrics.get_meter(service_name)
            self._initialized = True
            logger.info("Tracing initialized in testing mode (no exporters)")
            return
        
        if not self.config.get('enabled', True):
            logger.info("Tracing is disabled")
            return
            
        
        # Set up resource
        resource = Resource.create(attributes={
            ResourceAttributes.SERVICE_NAME: service_name,
            ResourceAttributes.SERVICE_VERSION: self.config.get('service_version', '1.0.0'),
            ResourceAttributes.DEPLOYMENT_ENVIRONMENT: self.config.get('environment', 'development'),
            'service.namespace': 'eai-mcp',
            'service.instance.id': os.getenv('HOSTNAME', 'unknown')
        })
        
        # Set up sampling
        sampler = self._create_sampler()
        
        # Initialize tracer provider
        self.tracer_provider = TracerProvider(
            resource=resource,
            sampler=sampler
        )
        
        # Set up exporters
        self._setup_exporters()
        
        # Set global tracer provider
        trace.set_tracer_provider(self.tracer_provider)
        
        # Initialize metrics
        self._initialize_metrics(resource)
        
        # Set up propagators
        self._setup_propagators()
        
        # Get tracer and meter
        self.tracer = trace.get_tracer(service_name)
        self.meter = metrics.get_meter(service_name)
        
        self._initialized = True
        logger.info(f"Tracing initialized for service: {service_name}")
    
    def _create_sampler(self) -> sampling.Sampler:
        """Create appropriate sampler based on configuration."""
        sampling_config = self.config.get('otel', {}).get('sampling', {})
        raw_ratio = sampling_config.get('ratio', 1.0)
        # Support env-style placeholders that may appear in YAML defaults
        if isinstance(raw_ratio, str) and raw_ratio.startswith("${"):
            # Default to 1.0 when placeholder not expanded
            ratio = 1.0
        else:
            ratio = float(raw_ratio)
        
        # Use simple ratio-based sampling (Adaptive is not available in standard SDK)
        return sampling.TraceIdRatioBased(ratio)
    
    def _setup_exporters(self) -> None:
        """Set up trace exporters."""
        exporters_config = self.config.get('otel', {}).get('exporters', {})
        
        processors = []
        
        # Jaeger exporter
        if exporters_config.get('jaeger', {}).get('enabled', True):
            try:
                jaeger_config = exporters_config.get('jaeger', {})
                jaeger_exporter = JaegerExporter(
                    agent_host_name=jaeger_config.get('agent_host', 'jaeger-agent'),
                    agent_port=int(jaeger_config.get('agent_port', 6831)),
                    collector_endpoint=jaeger_config.get('endpoint', 'http://jaeger:14268/api/traces')
                )
                processors.append(BatchSpanProcessor(jaeger_exporter))
                logger.info("Jaeger exporter configured")
            except Exception as e:
                logger.warning(f"Jaeger exporter not configured: {e}")
        
        # OTLP exporter
        if exporters_config.get('otlp', {}).get('enabled', False):
            try:
                otlp_config = exporters_config.get('otlp', {})
                otlp_exporter = OTLPSpanExporter(
                    endpoint=otlp_config.get('endpoint', 'http://otel-collector:4317'),
                    insecure=otlp_config.get('insecure', True)
                )
                processors.append(BatchSpanProcessor(otlp_exporter))
                logger.info("OTLP exporter configured")
            except Exception as e:
                logger.error(f"Failed to configure OTLP exporter: {e}")
        
        # Console exporter for development
        if self.config.get('environment', 'development') == 'development':
            try:
                console_exporter = ConsoleSpanExporter()
                processors.append(BatchSpanProcessor(console_exporter))
            except Exception as e:
                logger.warning(f"Console exporter not configured: {e}")
        
        # Add processors to tracer provider
        for processor in processors:
            self.tracer_provider.add_span_processor(processor)
    
    def _initialize_metrics(self, resource: Resource) -> None:
        """Initialize metrics collection."""
        try:
            metric_readers = []
            
            # OTLP metric exporter
            if self.config.get('otel', {}).get('exporters', {}).get('otlp', {}).get('enabled', False):
                otlp_metric_exporter = OTLPMetricExporter(
                    endpoint=self.config.get('otel', {}).get('exporters', {}).get('otlp', {}).get('endpoint', 'http://otel-collector:4317'),
                    insecure=self.config.get('otel', {}).get('exporters', {}).get('otlp', {}).get('insecure', True)
                )
                metric_readers.append(PeriodicExportingMetricReader(otlp_metric_exporter))
            
            self.meter_provider = MeterProvider(resource=resource, metric_readers=metric_readers)
            metrics.set_meter_provider(self.meter_provider)
            logger.info("Metrics initialized")
        except Exception as e:
            logger.error(f"Failed to initialize metrics: {e}")
    
    def _setup_propagators(self) -> None:
        """Set up trace context propagators."""
        propagators = [
            TraceContextTextMapPropagator(),
            B3MultiFormat(),
            JaegerPropagator()
        ]
        set_global_textmap(CompositePropagator(propagators))
    
    def get_tracer(self):
        """Get the configured tracer."""
        if not self._initialized:
            self.initialize()
        return self.tracer
    
    def get_meter(self):
        """Get the configured meter."""
        if not self._initialized:
            self.initialize()
        return self.meter


class TraceContextManager:
    """Manages trace context for service-to-service communication."""
    
    @staticmethod
    def inject_trace_context(headers: Dict[str, str]) -> Dict[str, str]:
        """Inject trace context into HTTP headers."""
        propagator = get_global_textmap()
        carrier = {}
        propagator.inject(carrier)
        headers.update(carrier)
        return headers
    
    @staticmethod
    def extract_trace_context(headers: Dict[str, str]) -> Dict[str, str]:
        """Extract trace context from HTTP headers."""
        propagator = get_global_textmap()
        return propagator.extract(headers)
    
    @staticmethod
    @contextmanager
    def start_span(name: str, attributes: Dict[str, Any] = None, kind: SpanKind = SpanKind.INTERNAL):
        """Start a new span with context management."""
        tracer = trace.get_tracer(__name__)
        attributes = attributes or {}
        
        with tracer.start_span(name, attributes=attributes, kind=kind) as span:
            try:
                yield span
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                raise


class TracingUtils:
    """Utility functions for tracing operations."""
    
    @staticmethod
    def create_llm_span(tracer, model_name: str, operation: str, 
                       prompt_tokens: int = None, completion_tokens: int = None):
        """Create a span for LLM operations."""
        attributes = {
            'llm.model_name': model_name,
            'llm.operation': operation,
        }
        
        if prompt_tokens is not None:
            attributes['llm.prompt_tokens'] = prompt_tokens
        if completion_tokens is not None:
            attributes['llm.completion_tokens'] = completion_tokens
        
        return tracer.start_span(f'llm.{operation}', attributes=attributes)
    
    @staticmethod
    def create_database_span(tracer, operation: str, table: str, 
                           query_type: str = 'SELECT'):
        """Create a span for database operations."""
        attributes = {
            'db.operation': operation,
            'db.table': table,
            'db.type': 'postgresql',
            'db.query_type': query_type,
        }
        
        return tracer.start_span(f'db.{operation}', attributes=attributes)
    
    @staticmethod
    def create_http_span(tracer, method: str, url: str, status_code: int = None):
        """Create a span for HTTP operations."""
        attributes = {
            'http.method': method,
            'http.url': url,
        }
        
        if status_code is not None:
            attributes['http.status_code'] = status_code
        
        return tracer.start_span(f'http.{method.lower()}', attributes=attributes)
    
    @staticmethod
    def create_workflow_span(tracer, workflow_name: str, step_name: str):
        """Create a span for workflow operations."""
        attributes = {
            'workflow.name': workflow_name,
            'workflow.step': step_name,
        }
        
        return tracer.start_span(f'workflow.{step_name}', attributes=attributes)
    
    @staticmethod
    def create_agent_span(tracer, agent_name: str, operation: str):
        """Create a span for agent operations."""
        attributes = {
            'agent.name': agent_name,
            'agent.operation': operation,
        }
        
        return tracer.start_span(f'agent.{operation}', attributes=attributes)


def traced(operation_name: str = None, attributes: Dict[str, Any] = None):
    """Decorator to trace function calls."""
    def decorator(func):
        name = operation_name or f"{func.__module__}.{func.__name__}"
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            tracer = trace.get_tracer(__name__)
            with tracer.start_as_current_span(name) as span:
                if attributes:
                    for key, value in attributes.items():
                        span.set_attribute(key, value)
                
                try:
                    result = func(*args, **kwargs)
                    span.set_status(Status(StatusCode.OK))
                    return result
                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    raise
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            tracer = trace.get_tracer(__name__)
            with tracer.start_as_current_span(name) as span:
                if attributes:
                    for key, value in attributes.items():
                        span.set_attribute(key, value)
                
                try:
                    result = await func(*args, **kwargs)
                    span.set_status(Status(StatusCode.OK))
                    return result
                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    raise
        
        if hasattr(func, '__call__'):
            if hasattr(func, '__code__') and func.__code__.co_flags & 0x80:  # Check if coroutine
                return async_wrapper
            else:
                return sync_wrapper
        return sync_wrapper

    
    return decorator


class InstrumentationManager:
    """Manages instrumentation for various libraries and frameworks."""
    
    def __init__(self, tracing_config: TracingConfig):
        self.tracing_config = tracing_config
        self.instrumentation_config = self.tracing_config.config.get('instrumentation', {})
    
    def instrument_fastapi(self, app) -> None:
        """Instrument FastAPI application."""
        if not self.instrumentation_config.get('http', {}).get('enabled', True):
            return
        
        try:
            FastAPIInstrumentor.instrument_app(
                app,
                excluded_urls=self.instrumentation_config.get('http', {}).get('exclude_urls', [
                    "/health", "/metrics", "/favicon.ico"
                ]),
                request_hook=self._fastapi_request_hook,
                response_hook=self._fastapi_response_hook
            )
            logger.info("FastAPI instrumentation configured")
        except Exception as e:
            logger.error(f"Failed to instrument FastAPI: {e}")
    
    def instrument_httpx(self) -> None:
        """Instrument httpx client."""
        if not self.instrumentation_config.get('http', {}).get('enabled', True):
            return
        
        try:
            HTTPXClientInstrumentor().instrument()
            logger.info("HTTPX instrumentation configured")
        except Exception as e:
            logger.error(f"Failed to instrument HTTPX: {e}")
    
    def instrument_database(self) -> None:
        """Instrument database clients."""
        if not self.instrumentation_config.get('database', {}).get('enabled', True):
            return
        
        try:
            AsyncPGInstrumentor().instrument()
            logger.info("AsyncPG instrumentation configured")
        except Exception as e:
            logger.error(f"Failed to instrument AsyncPG: {e}")
        
        try:
            RedisInstrumentor().instrument()
            logger.info("Redis instrumentation configured")
        except Exception as e:
            logger.error(f"Failed to instrument Redis: {e}")
    
    def instrument_requests(self) -> None:
        """Instrument requests library."""
        if not self.instrumentation_config.get('http', {}).get('enabled', True):
            return
        
        try:
            RequestsInstrumentor().instrument()
            logger.info("Requests instrumentation configured")
        except Exception as e:
            logger.error(f"Failed to instrument Requests: {e}")
    
    def _fastapi_request_hook(self, span: trace.Span, request: Request) -> None:
        """Hook for FastAPI request processing."""
        if self.instrumentation_config.get('http', {}).get('capture_headers', True):
            for key, value in request.headers.items():
                if key.lower() not in ['authorization', 'cookie']:  # Skip sensitive headers
                    span.set_attribute(f"http.request.header.{key}", value)
    
    def _fastapi_response_hook(self, span: trace.Span, request: Request, response: Response) -> None:
        """Hook for FastAPI response processing."""
        span.set_attribute("http.status_code", response.status_code)
        
        if self.instrumentation_config.get('http', {}).get('capture_headers', True):
            for key, value in response.headers.items():
                span.set_attribute(f"http.response.header.{key}", value)


# Global tracing configuration instance
_tracing_config = None
_instrumentation_manager = None


def get_tracing_config() -> TracingConfig:
    """Get the global tracing configuration."""
    global _tracing_config
    if _tracing_config is None:
        _tracing_config = TracingConfig()
    return _tracing_config


def get_instrumentation_manager() -> InstrumentationManager:
    """Get the global instrumentation manager."""
    global _instrumentation_manager
    if _instrumentation_manager is None:
        _instrumentation_manager = InstrumentationManager(get_tracing_config())
    return _instrumentation_manager


def initialize_tracing(service_name: str = None) -> None:
    """Initialize tracing for a service."""
    config = get_tracing_config()
    config.initialize(service_name)


def get_tracer():
    """Get the global tracer instance."""
    config = get_tracing_config()
    return config.get_tracer()


def instrument_service(app = None) -> None:
    """Instrument a service with all available instrumentation."""
    manager = get_instrumentation_manager()
    
    if app:
        manager.instrument_fastapi(app)
    
    manager.instrument_httpx()
    manager.instrument_database()
    manager.instrument_requests()

