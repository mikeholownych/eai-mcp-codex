"""
Trace exporters and configuration for MCP services.
Provides Jaeger and OTLP exporters with metrics collection and health checks.
"""

import logging
from typing import Dict, Any, Optional, List, Callable, Union
from contextlib import contextmanager, asynccontextmanager
import asyncio
import time
import json
import os
from dataclasses import dataclass
from enum import Enum

from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
    SimpleSpanProcessor
)
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.exporter.zipkin.json import ZipkinExporter
from opentelemetry.exporter.logging import LoggingSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.semconv.resource import ResourceAttributes
from opentelemetry.semconv.trace import SpanAttributes

from .tracing import get_tracing_config
from .trace_sampling import get_adaptive_sampler

logger = logging.getLogger(__name__)


class ExporterType(Enum):
    """Exporter type enumeration."""
    JAEGER = "jaeger"
    OTLP = "otlp"
    ZIPKIN = "zipkin"
    CONSOLE = "console"
    LOGGING = "logging"
    PROMETHEUS = "prometheus"


@dataclass
class ExporterConfig:
    """Configuration for trace exporters."""
    exporter_type: ExporterType
    enabled: bool = True
    endpoint: Optional[str] = None
    timeout: int = 30
    compression: Optional[str] = None
    headers: Optional[Dict[str, str]] = None
    max_queue_size: int = 2048
    max_export_batch_size: int = 512
    schedule_delay_millis: int = 5000
    export_timeout_millis: int = 30000


class TraceExporterManager:
    """Manager for trace exporters and configuration."""
    
    def __init__(self):
        """Initialize trace exporter manager."""
        self.tracing_config = get_tracing_config()
        self.exporters = {}
        self.span_processors = []
        self.metric_readers = []
        self.tracer_provider = None
        self.meter_provider = None
        self.health_status = {}
        
        # Default exporter configurations
        self.default_configs = {
            ExporterType.JAEGER: ExporterConfig(
                exporter_type=ExporterType.JAEGER,
                enabled=True,
                endpoint="http://jaeger-collector:14268/api/traces",
                timeout=30,
                compression="gzip",
                headers={},
                max_queue_size=2048,
                max_export_batch_size=512,
                schedule_delay_millis=5000,
                export_timeout_millis=30000
            ),
            ExporterType.OTLP: ExporterConfig(
                exporter_type=ExporterType.OTLP,
                enabled=False,
                endpoint="http://otel-collector:4317",
                timeout=30,
                compression="gzip",
                headers={},
                max_queue_size=2048,
                max_export_batch_size=512,
                schedule_delay_millis=5000,
                export_timeout_millis=30000
            ),
            ExporterType.ZIPKIN: ExporterConfig(
                exporter_type=ExporterType.ZIPKIN,
                enabled=False,
                endpoint="http://zipkin:9411/api/v2/spans",
                timeout=30,
                compression="gzip",
                headers={},
                max_queue_size=2048,
                max_export_batch_size=512,
                schedule_delay_millis=5000,
                export_timeout_millis=30000
            ),
            ExporterType.CONSOLE: ExporterConfig(
                exporter_type=ExporterType.CONSOLE,
                enabled=False,
                timeout=30,
                max_queue_size=100,
                max_export_batch_size=10,
                schedule_delay_millis=1000,
                export_timeout_millis=5000
            ),
            ExporterType.LOGGING: ExporterConfig(
                exporter_type=ExporterType.LOGGING,
                enabled=False,
                timeout=30,
                max_queue_size=100,
                max_export_batch_size=10,
                schedule_delay_millis=1000,
                export_timeout_millis=5000
            ),
            ExporterType.PROMETHEUS: ExporterConfig(
                exporter_type=ExporterType.PROMETHEUS,
                enabled=True,
                timeout=30,
                max_queue_size=100,
                max_export_batch_size=10,
                schedule_delay_millis=1000,
                export_timeout_millis=5000
            )
        }
        
        # Load configurations from environment
        self._load_configurations()
    
    def _load_configurations(self):
        """Load exporter configurations from environment variables."""
        env_configs = {
            ExporterType.JAEGER: {
                "enabled": os.getenv("JAEGER_ENABLED", "true").lower() == "true",
                "endpoint": os.getenv("JAEGER_ENDPOINT", "http://jaeger-collector:14268/api/traces"),
                "timeout": int(os.getenv("JAEGER_TIMEOUT", "30")),
                "compression": os.getenv("JAEGER_COMPRESSION", "gzip"),
                "headers": self._parse_headers(os.getenv("JAEGER_HEADERS", "")),
            },
            ExporterType.OTLP: {
                "enabled": os.getenv("OTLP_ENABLED", "false").lower() == "true",
                "endpoint": os.getenv("OTLP_ENDPOINT", "http://otel-collector:4317"),
                "timeout": int(os.getenv("OTLP_TIMEOUT", "30")),
                "compression": os.getenv("OTLP_COMPRESSION", "gzip"),
                "headers": self._parse_headers(os.getenv("OTLP_HEADERS", "")),
            },
            ExporterType.ZIPKIN: {
                "enabled": os.getenv("ZIPKIN_ENABLED", "false").lower() == "true",
                "endpoint": os.getenv("ZIPKIN_ENDPOINT", "http://zipkin:9411/api/v2/spans"),
                "timeout": int(os.getenv("ZIPKIN_TIMEOUT", "30")),
                "compression": os.getenv("ZIPKIN_COMPRESSION", "gzip"),
                "headers": self._parse_headers(os.getenv("ZIPKIN_HEADERS", "")),
            },
            ExporterType.CONSOLE: {
                "enabled": os.getenv("CONSOLE_EXPORTER_ENABLED", "false").lower() == "true",
                "timeout": int(os.getenv("CONSOLE_EXPORTER_TIMEOUT", "30")),
            },
            ExporterType.LOGGING: {
                "enabled": os.getenv("LOGGING_EXPORTER_ENABLED", "false").lower() == "true",
                "timeout": int(os.getenv("LOGGING_EXPORTER_TIMEOUT", "30")),
            },
            ExporterType.PROMETHEUS: {
                "enabled": os.getenv("PROMETHEUS_ENABLED", "true").lower() == "true",
                "timeout": int(os.getenv("PROMETHEUS_TIMEOUT", "30")),
            }
        }
        
        # Update default configurations with environment values
        for exporter_type, config in env_configs.items():
            if exporter_type in self.default_configs:
                for key, value in config.items():
                    if value is not None:
                        setattr(self.default_configs[exporter_type], key, value)
    
    def _parse_headers(self, headers_str: str) -> Dict[str, str]:
        """Parse headers from environment variable string."""
        headers = {}
        if headers_str:
            for header in headers_str.split(","):
                if "=" in header:
                    key, value = header.split("=", 1)
                    headers[key.strip()] = value.strip()
        return headers
    
    def initialize_providers(self, service_name: str, service_version: str = "1.0.0",
                            environment: str = "development"):
        """
        Initialize trace and metrics providers.
        
        Args:
            service_name: Name of the service
            service_version: Version of the service
            environment: Environment (development, staging, production)
        """
        # Create resource with service information
        resource = Resource.create({
            ResourceAttributes.SERVICE_NAME: service_name,
            ResourceAttributes.SERVICE_VERSION: service_version,
            ResourceAttributes.DEPLOYMENT_ENVIRONMENT: environment,
            "service.namespace": "eai-mcp",
            "service.instance.id": os.getenv("HOSTNAME", "unknown"),
        })
        
        # Initialize tracer provider
        self.tracer_provider = TracerProvider(
            resource=resource,
            sampler=get_adaptive_sampler()
        )
        
        # Initialize meter provider
        self.meter_provider = MeterProvider(resource=resource)
        
        # Set global providers
        trace.set_tracer_provider(self.tracer_provider)
        metrics.set_meter_provider(self.meter_provider)
        
        # Initialize exporters
        self._initialize_exporters()
        
        logger.info(f"Initialized trace exporters for service: {service_name}")
    
    def _initialize_exporters(self):
        """Initialize all configured exporters."""
        for exporter_type, config in self.default_configs.items():
            if config.enabled:
                try:
                    self._create_exporter(exporter_type, config)
                except Exception as e:
                    logger.error(f"Failed to initialize {exporter_type.value} exporter: {e}")
                    self.health_status[exporter_type.value] = {
                        "status": "error",
                        "message": str(e),
                        "last_check": time.time()
                    }
    
    def _create_exporter(self, exporter_type: ExporterType, config: ExporterConfig):
        """Create and configure an exporter."""
        if exporter_type == ExporterType.JAEGER:
            self._create_jaeger_exporter(config)
        elif exporter_type == ExporterType.OTLP:
            self._create_otlp_exporter(config)
        elif exporter_type == ExporterType.ZIPKIN:
            self._create_zipkin_exporter(config)
        elif exporter_type == ExporterType.CONSOLE:
            self._create_console_exporter(config)
        elif exporter_type == ExporterType.LOGGING:
            self._create_logging_exporter(config)
        elif exporter_type == ExporterType.PROMETHEUS:
            self._create_prometheus_exporter(config)
    
    def _create_jaeger_exporter(self, config: ExporterConfig):
        """Create Jaeger exporter."""
        exporter = JaegerExporter(
            agent_host_name=config.endpoint.split(":")[1].strip("/"),
            agent_port=6831,
            collector_endpoint=config.endpoint,
            timeout=config.timeout,
            compression=config.compression,
        )
        
        processor = BatchSpanProcessor(
            exporter,
            max_queue_size=config.max_queue_size,
            max_export_batch_size=config.max_export_batch_size,
            schedule_delay_millis=config.schedule_delay_millis,
            export_timeout_millis=config.export_timeout_millis
        )
        
        self.tracer_provider.add_span_processor(processor)
        self.exporters[ExporterType.JAEGER.value] = exporter
        self.span_processors.append(processor)
        
        self.health_status[ExporterType.JAEGER.value] = {
            "status": "healthy",
            "message": "Exporter initialized successfully",
            "last_check": time.time()
        }
        
        logger.info("Jaeger exporter initialized")
    
    def _create_otlp_exporter(self, config: ExporterConfig):
        """Create OTLP exporter."""
        exporter = OTLPSpanExporter(
            endpoint=config.endpoint,
            timeout=config.timeout,
            compression=config.compression,
            headers=config.headers,
        )
        
        processor = BatchSpanProcessor(
            exporter,
            max_queue_size=config.max_queue_size,
            max_export_batch_size=config.max_export_batch_size,
            schedule_delay_millis=config.schedule_delay_millis,
            export_timeout_millis=config.export_timeout_millis
        )
        
        self.tracer_provider.add_span_processor(processor)
        self.exporters[ExporterType.OTLP.value] = exporter
        self.span_processors.append(processor)
        
        # Create OTLP metrics exporter
        metric_exporter = OTLPMetricExporter(
            endpoint=config.endpoint,
            timeout=config.timeout,
            compression=config.compression,
            headers=config.headers,
        )
        
        metric_reader = PeriodicExportingMetricReader(
            metric_exporter,
            export_interval_millis=config.schedule_delay_millis
        )
        
        self.meter_provider.add_metric_reader(metric_reader)
        self.metric_readers.append(metric_reader)
        
        self.health_status[ExporterType.OTLP.value] = {
            "status": "healthy",
            "message": "Exporter initialized successfully",
            "last_check": time.time()
        }
        
        logger.info("OTLP exporter initialized")
    
    def _create_zipkin_exporter(self, config: ExporterConfig):
        """Create Zipkin exporter."""
        exporter = ZipkinExporter(
            endpoint=config.endpoint,
            timeout=config.timeout,
        )
        
        processor = BatchSpanProcessor(
            exporter,
            max_queue_size=config.max_queue_size,
            max_export_batch_size=config.max_export_batch_size,
            schedule_delay_millis=config.schedule_delay_millis,
            export_timeout_millis=config.export_timeout_millis
        )
        
        self.tracer_provider.add_span_processor(processor)
        self.exporters[ExporterType.ZIPKIN.value] = exporter
        self.span_processors.append(processor)
        
        self.health_status[ExporterType.ZIPKIN.value] = {
            "status": "healthy",
            "message": "Exporter initialized successfully",
            "last_check": time.time()
        }
        
        logger.info("Zipkin exporter initialized")
    
    def _create_console_exporter(self, config: ExporterConfig):
        """Create console exporter."""
        exporter = ConsoleSpanExporter()
        
        processor = SimpleSpanProcessor(exporter)
        self.tracer_provider.add_span_processor(processor)
        self.exporters[ExporterType.CONSOLE.value] = exporter
        self.span_processors.append(processor)
        
        self.health_status[ExporterType.CONSOLE.value] = {
            "status": "healthy",
            "message": "Exporter initialized successfully",
            "last_check": time.time()
        }
        
        logger.info("Console exporter initialized")
    
    def _create_logging_exporter(self, config: ExporterConfig):
        """Create logging exporter."""
        exporter = LoggingSpanExporter()
        
        processor = SimpleSpanProcessor(exporter)
        self.tracer_provider.add_span_processor(processor)
        self.exporters[ExporterType.LOGGING.value] = exporter
        self.span_processors.append(processor)
        
        self.health_status[ExporterType.LOGGING.value] = {
            "status": "healthy",
            "message": "Exporter initialized successfully",
            "last_check": time.time()
        }
        
        logger.info("Logging exporter initialized")
    
    def _create_prometheus_exporter(self, config: ExporterConfig):
        """Create Prometheus exporter."""
        reader = PrometheusMetricReader()
        self.meter_provider.add_metric_reader(reader)
        self.metric_readers.append(reader)
        
        self.health_status[ExporterType.PROMETHEUS.value] = {
            "status": "healthy",
            "message": "Exporter initialized successfully",
            "last_check": time.time()
        }
        
        logger.info("Prometheus exporter initialized")
    
    def get_exporter_status(self, exporter_type: ExporterType) -> Dict[str, Any]:
        """Get the status of a specific exporter."""
        return self.health_status.get(exporter_type.value, {
            "status": "unknown",
            "message": "Exporter not found",
            "last_check": time.time()
        })
    
    def get_all_exporter_status(self) -> Dict[str, Dict[str, Any]]:
        """Get the status of all exporters."""
        return self.health_status.copy()
    
    def check_exporter_health(self, exporter_type: ExporterType) -> bool:
        """Check the health of a specific exporter."""
        status = self.get_exporter_status(exporter_type)
        return status.get("status") == "healthy"
    
    def check_all_exporter_health(self) -> Dict[str, bool]:
        """Check the health of all exporters."""
        health_results = {}
        for exporter_type in ExporterType:
            health_results[exporter_type.value] = self.check_exporter_health(exporter_type)
        return health_results
    
    def shutdown(self):
        """Shutdown all exporters and processors."""
        logger.info("Shutting down trace exporters")
        
        # Shutdown span processors
        for processor in self.span_processors:
            try:
                processor.shutdown()
            except Exception as e:
                logger.error(f"Error shutting down span processor: {e}")
        
        # Shutdown metric readers
        for reader in self.metric_readers:
            try:
                reader.shutdown()
            except Exception as e:
                logger.error(f"Error shutting down metric reader: {e}")
        
        # Shutdown providers
        if self.tracer_provider:
            try:
                self.tracer_provider.shutdown()
            except Exception as e:
                logger.error(f"Error shutting down tracer provider: {e}")
        
        if self.meter_provider:
            try:
                self.meter_provider.shutdown()
            except Exception as e:
                logger.error(f"Error shutting down meter provider: {e}")
        
        logger.info("Trace exporters shutdown complete")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get exporter metrics."""
        metrics = {
            "exporters": {},
            "span_processors": len(self.span_processors),
            "metric_readers": len(self.metric_readers),
            "health_status": self.health_status.copy()
        }
        
        for exporter_type, exporter in self.exporters.items():
            metrics["exporters"][exporter_type] = {
                "type": exporter_type,
                "enabled": True,
                "class": exporter.__class__.__name__,
            }
        
        return metrics


class TraceMetricsCollector:
    """Collector for trace-related metrics."""
    
    def __init__(self, meter_provider: MeterProvider):
        """Initialize trace metrics collector."""
        self.meter = meter_provider.get_meter("eai-mcp-tracing")
        self._initialize_metrics()
    
    def _initialize_metrics(self):
        """Initialize trace metrics."""
        # Span metrics
        self.span_counter = self.meter.create_counter(
            "spans_created_total",
            description="Total number of spans created"
        )
        
        self.span_export_counter = self.meter.create_counter(
            "spans_exported_total",
            description="Total number of spans exported"
        )
        
        self.span_error_counter = self.meter.create_counter(
            "span_export_errors_total",
            description="Total number of span export errors"
        )
        
        # Trace metrics
        self.trace_counter = self.meter.create_counter(
            "traces_created_total",
            description="Total number of traces created"
        )
        
        self.trace_sampled_counter = self.meter.create_counter(
            "traces_sampled_total",
            description="Total number of sampled traces"
        )
        
        # Exporter metrics
        self.exporter_up = self.meter.create_up_down_counter(
            "exporter_up",
            description="Exporter health status (1 for healthy, 0 for unhealthy)"
        )
        
        self.exporter_queue_size = self.meter.create_up_down_counter(
            "exporter_queue_size",
            description="Current exporter queue size"
        )
        
        # Duration metrics
        self.span_duration = self.meter.create_histogram(
            "span_duration_seconds",
            description="Duration of spans"
        )
        
        self.export_duration = self.meter.create_histogram(
            "span_export_duration_seconds",
            description="Duration of span export operations"
        )
        
        # Sampling metrics
        self.sampling_rate = self.meter.create_histogram(
            "trace_sampling_rate",
            description="Trace sampling rate"
        )
        
        self.sampling_decision = self.meter.create_counter(
            "sampling_decisions_total",
            description="Total number of sampling decisions"
        )
    
    def record_span_created(self, span_name: str, service_name: str):
        """Record span creation."""
        self.span_counter.add(1, {
            "span_name": span_name,
            "service_name": service_name
        })
    
    def record_span_exported(self, span_name: str, service_name: str, exporter: str):
        """Record span export."""
        self.span_export_counter.add(1, {
            "span_name": span_name,
            "service_name": service_name,
            "exporter": exporter
        })
    
    def record_span_export_error(self, span_name: str, service_name: str, exporter: str, error: str):
        """Record span export error."""
        self.span_error_counter.add(1, {
            "span_name": span_name,
            "service_name": service_name,
            "exporter": exporter,
            "error": error
        })
    
    def record_trace_created(self, service_name: str):
        """Record trace creation."""
        self.trace_counter.add(1, {"service_name": service_name})
    
    def record_trace_sampled(self, service_name: str, sampled: bool):
        """Record trace sampling decision."""
        self.trace_sampled_counter.add(1, {
            "service_name": service_name,
            "sampled": str(sampled).lower()
        })
    
    def record_exporter_health(self, exporter: str, healthy: bool):
        """Record exporter health status."""
        value = 1 if healthy else 0
        self.exporter_up.add(value, {"exporter": exporter})
    
    def record_exporter_queue_size(self, exporter: str, size: int):
        """Record exporter queue size."""
        self.exporter_queue_size.add(size, {"exporter": exporter})
    
    def record_span_duration(self, span_name: str, service_name: str, duration: float):
        """Record span duration."""
        self.span_duration.record(duration, {
            "span_name": span_name,
            "service_name": service_name
        })
    
    def record_export_duration(self, exporter: str, duration: float):
        """Record export duration."""
        self.export_duration.record(duration, {"exporter": exporter})
    
    def record_sampling_rate(self, service_name: str, rate: float):
        """Record sampling rate."""
        self.sampling_rate.record(rate, {"service_name": service_name})
    
    def record_sampling_decision(self, service_name: str, decision: str):
        """Record sampling decision."""
        self.sampling_decision.add(1, {
            "service_name": service_name,
            "decision": decision
        })


# Global instance
trace_exporter_manager = TraceExporterManager()


def get_trace_exporter_manager() -> TraceExporterManager:
    """Get the global trace exporter manager."""
    return trace_exporter_manager


def initialize_trace_exporters(service_name: str, service_version: str = "1.0.0",
                            environment: str = "development"):
    """Initialize trace exporters for a service."""
    trace_exporter_manager.initialize_providers(
        service_name, service_version, environment
    )
    
    # Initialize metrics collector
    metrics_collector = TraceMetricsCollector(trace_exporter_manager.meter_provider)
    
    return trace_exporter_manager, metrics_collector


def shutdown_trace_exporters():
    """Shutdown all trace exporters."""
    trace_exporter_manager.shutdown()


def get_exporter_status(exporter_type: ExporterType) -> Dict[str, Any]:
    """Get the status of a specific exporter."""
    return trace_exporter_manager.get_exporter_status(exporter_type)


def get_all_exporter_status() -> Dict[str, Dict[str, Any]]:
    """Get the status of all exporters."""
    return trace_exporter_manager.get_all_exporter_status()


def check_exporter_health(exporter_type: ExporterType) -> bool:
    """Check the health of a specific exporter."""
    return trace_exporter_manager.check_exporter_health(exporter_type)


def check_all_exporter_health() -> Dict[str, bool]:
    """Check the health of all exporters."""
    return trace_exporter_manager.check_all_exporter_health()


def get_exporter_metrics() -> Dict[str, Any]:
    """Get exporter metrics."""
    return trace_exporter_manager.get_metrics()