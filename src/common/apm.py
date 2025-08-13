"""
Application Performance Monitoring (APM) framework for MCP services.
Provides comprehensive performance monitoring, profiling, and analysis capabilities.
"""

import logging
import os
import time
import threading
import asyncio
import psutil
from typing import Dict, Any, Optional, List, Callable, Union
from contextlib import contextmanager, asynccontextmanager
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
import statistics
import numpy as np
from datetime import datetime

from opentelemetry.trace import Status, StatusCode

from .tracing import get_tracing_config

logger = logging.getLogger(__name__)


class APMOperationType(Enum):
    """APM operation types."""
    HTTP_REQUEST = "http_request"
    DATABASE_QUERY = "database_query"
    EXTERNAL_API = "external_api"
    BUSINESS_TRANSACTION = "business_transaction"
    CUSTOM_OPERATION = "custom_operation"
    CPU_INTENSIVE = "cpu_intensive"
    MEMORY_INTENSIVE = "memory_intensive"
    IO_INTENSIVE = "io_intensive"


class APMSeverity(Enum):
    """APM alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class APMConfig:
    """Configuration for APM framework."""
    enabled: bool = True
    profiling_enabled: bool = True
    memory_profiling_enabled: bool = True
    cpu_profiling_enabled: bool = True
    database_monitoring_enabled: bool = True
    external_api_monitoring_enabled: bool = True
    business_transaction_monitoring_enabled: bool = True
    anomaly_detection_enabled: bool = True
    baseline_estimation_enabled: bool = True
    
    # Performance thresholds
    slow_request_threshold: float = 1.0  # seconds
    memory_usage_threshold: float = 0.8  # 80%
    cpu_usage_threshold: float = 0.8  # 80%
    database_query_threshold: float = 0.5  # seconds
    external_api_threshold: float = 2.0  # seconds
    
    # Sampling configuration
    profiling_sample_rate: float = 0.1  # 10%
    memory_sample_rate: float = 0.05  # 5%
    
    # Baseline configuration
    baseline_window_size: int = 100  # number of samples
    baseline_update_interval: int = 300  # seconds
    
    # Anomaly detection configuration
    anomaly_detection_sensitivity: float = 2.0  # standard deviations
    anomaly_window_size: int = 20  # number of recent samples


@dataclass
class PerformanceMetrics:
    """Performance metrics data structure."""
    operation_name: str
    operation_type: APMOperationType
    start_time: float
    end_time: float
    duration: float
    success: bool
    error_message: Optional[str] = None
    attributes: Dict[str, Any] = field(default_factory=dict)
    resource_usage: Dict[str, float] = field(default_factory=dict)
    custom_metrics: Dict[str, Union[int, float]] = field(default_factory=dict)
    
    @property
    def timestamp(self) -> datetime:
        """Get timestamp of the operation."""
        return datetime.fromtimestamp(self.start_time)


@dataclass
class ResourceUsage:
    """Resource usage metrics."""
    cpu_percent: float
    memory_percent: float
    memory_rss: int  # bytes
    memory_vms: int  # bytes
    thread_count: int
    open_files: int
    network_io: Dict[str, int] = field(default_factory=dict)
    disk_io: Dict[str, int] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "cpu_percent": self.cpu_percent,
            "memory_percent": self.memory_percent,
            "memory_rss": self.memory_rss,
            "memory_vms": self.memory_vms,
            "thread_count": self.thread_count,
            "open_files": self.open_files,
            "network_io": self.network_io,
            "disk_io": self.disk_io
        }


@dataclass
class PerformanceBaseline:
    """Performance baseline data."""
    operation_name: str
    operation_type: APMOperationType
    sample_count: int
    mean_duration: float
    median_duration: float
    p95_duration: float
    p99_duration: float
    std_duration: float
    min_duration: float
    max_duration: float
    last_updated: datetime
    
    def is_anomaly(self, duration: float, sensitivity: float = 2.0) -> bool:
        """Check if duration is an anomaly."""
        if self.std_duration == 0:
            return False
        z_score = abs(duration - self.mean_duration) / self.std_duration
        return z_score > sensitivity


class APMInstrumentation:
    """APM instrumentation framework."""
    
    def __init__(self, config: APMConfig = None):
        """Initialize APM instrumentation."""
        self.config = config or APMConfig()
        self.tracer = get_tracing_config().get_tracer()
        self.meter = get_tracing_config().get_meter()
        
        # Initialize metrics
        self._initialize_metrics()
        
        # Performance data storage
        self.performance_data = defaultdict(list)
        self.baselines = {}
        self.resource_monitor = ResourceMonitor()
        
        # Anomaly detection
        self.anomaly_detector = AnomalyDetector(self.config)
        
        # Background tasks
        self._running = False
        self._background_thread = None
        
        # Start background tasks if enabled
        if self.config.enabled:
            self.start()
    
    def _initialize_metrics(self):
        """Initialize OpenTelemetry metrics."""
        # Counters
        self.operation_counter = self.meter.create_counter(
            "apm_operations_total",
            description="Total number of operations monitored"
        )
        
        self.error_counter = self.meter.create_counter(
            "apm_errors_total",
            description="Total number of operation errors"
        )
        
        self.slow_operation_counter = self.meter.create_counter(
            "apm_slow_operations_total",
            description="Total number of slow operations"
        )
        
        # Histograms
        self.duration_histogram = self.meter.create_histogram(
            "apm_operation_duration_seconds",
            description="Duration of operations"
        )
        
        self.memory_usage_histogram = self.meter.create_histogram(
            "apm_memory_usage_bytes",
            description="Memory usage during operations"
        )
        
        self.cpu_usage_histogram = self.meter.create_histogram(
            "apm_cpu_usage_percent",
            description="CPU usage during operations"
        )
        
        # Gauges
        self.active_operations_gauge = self.meter.create_up_down_counter(
            "apm_active_operations",
            description="Number of currently active operations"
        )
        
        self.resource_usage_gauge = self.meter.create_up_down_counter(
            "apm_resource_usage",
            description="Current resource usage"
        )
    
    def start(self):
        """Start APM instrumentation."""
        if self._running:
            return
        
        self._running = True
        self.resource_monitor.start()
        
        # Start background thread for baseline updates
        self._background_thread = threading.Thread(target=self._background_worker, daemon=True)
        self._background_thread.start()
        
        logger.info("APM instrumentation started")
    
    def stop(self):
        """Stop APM instrumentation."""
        if not self._running:
            return
        
        self._running = False
        self.resource_monitor.stop()
        
        if self._background_thread:
            self._background_thread.join(timeout=5)
        
        logger.info("APM instrumentation stopped")
    
    def _background_worker(self):
        """Background worker for periodic tasks."""
        while self._running:
            try:
                # Update baselines
                if self.config.baseline_estimation_enabled:
                    self._update_baselines()
                
                # Update resource metrics
                self._update_resource_metrics()
                
                # Sleep for update interval
                time.sleep(self.config.baseline_update_interval)
            except Exception as e:
                logger.error(f"Error in APM background worker: {e}")
    
    def _update_baselines(self):
        """Update performance baselines."""
        for operation_name, metrics_list in self.performance_data.items():
            if len(metrics_list) >= self.config.baseline_window_size:
                # Calculate baseline statistics
                durations = [m.duration for m in metrics_list[-self.config.baseline_window_size:]]
                
                baseline = PerformanceBaseline(
                    operation_name=operation_name,
                    operation_type=metrics_list[-1].operation_type,
                    sample_count=len(durations),
                    mean_duration=statistics.mean(durations),
                    median_duration=statistics.median(durations),
                    p95_duration=np.percentile(durations, 95),
                    p99_duration=np.percentile(durations, 99),
                    std_duration=statistics.stdev(durations) if len(durations) > 1 else 0,
                    min_duration=min(durations),
                    max_duration=max(durations),
                    last_updated=datetime.now()
                )
                
                self.baselines[operation_name] = baseline
    
    def _update_resource_metrics(self):
        """Update resource usage metrics."""
        resource_usage = self.resource_monitor.get_current_usage()
        
        # Update resource usage gauge
        self.resource_usage_gauge.add(1, {
            "cpu_percent": resource_usage.cpu_percent,
            "memory_percent": resource_usage.memory_percent,
            "memory_rss": resource_usage.memory_rss,
            "memory_vms": resource_usage.memory_vms
        })
    
    @contextmanager
    def trace_operation(self, operation_name: str, operation_type: APMOperationType,
                       attributes: Dict[str, Any] = None):
        """Trace an operation with APM instrumentation."""
        if not self.config.enabled:
            yield None
            return
        
        span_name = f"apm.{operation_type.value}.{operation_name}"
        span_attributes = attributes or {}
        span_attributes["apm.operation_name"] = operation_name
        span_attributes["apm.operation_type"] = operation_type.value
        
        # Get initial resource usage
        initial_resource = self.resource_monitor.get_current_usage()
        
        # Increment active operations counter
        self.active_operations_gauge.add(1)
        
        start_time = time.time()
        success = True
        error_message = None
        
        with self.tracer.start_as_current_span(span_name, attributes=span_attributes) as span:
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
                
                # Get final resource usage
                final_resource = self.resource_monitor.get_current_usage()
                
                # Calculate resource usage delta
                resource_delta = {
                    "cpu_percent": final_resource.cpu_percent - initial_resource.cpu_percent,
                    "memory_percent": final_resource.memory_percent - initial_resource.memory_percent,
                    "memory_rss": final_resource.memory_rss - initial_resource.memory_rss,
                    "memory_vms": final_resource.memory_vms - initial_resource.memory_vms
                }
                
                # Create performance metrics
                metrics = PerformanceMetrics(
                    operation_name=operation_name,
                    operation_type=operation_type,
                    start_time=start_time,
                    end_time=end_time,
                    duration=duration,
                    success=success,
                    error_message=error_message,
                    attributes=span_attributes,
                    resource_usage=resource_delta
                )
                
                # Store performance data
                self.performance_data[operation_name].append(metrics)
                
                # Update metrics
                self._update_metrics(metrics)
                
                # Check for anomalies
                if self.config.anomaly_detection_enabled:
                    self._check_anomaly(metrics)
                
                # Add span attributes
                span.set_attribute("apm.duration_ms", duration * 1000)
                span.set_attribute("apm.success", success)
                span.set_attribute("apm.cpu_delta", resource_delta["cpu_percent"])
                span.set_attribute("apm.memory_delta", resource_delta["memory_percent"])
                
                # Decrement active operations counter
                self.active_operations_gauge.add(-1)
    
    @asynccontextmanager
    async def trace_async_operation(self, operation_name: str, operation_type: APMOperationType,
                                  attributes: Dict[str, Any] = None):
        """Trace an async operation with APM instrumentation."""
        if not self.config.enabled:
            yield None
            return
        
        span_name = f"apm.{operation_type.value}.{operation_name}"
        span_attributes = attributes or {}
        span_attributes["apm.operation_name"] = operation_name
        span_attributes["apm.operation_type"] = operation_type.value
        
        # Get initial resource usage
        initial_resource = self.resource_monitor.get_current_usage()
        
        # Increment active operations counter
        self.active_operations_gauge.add(1)
        
        start_time = time.time()
        success = True
        error_message = None
        
        with self.tracer.start_as_current_span(span_name, attributes=span_attributes) as span:
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
                
                # Get final resource usage
                final_resource = self.resource_monitor.get_current_usage()
                
                # Calculate resource usage delta
                resource_delta = {
                    "cpu_percent": final_resource.cpu_percent - initial_resource.cpu_percent,
                    "memory_percent": final_resource.memory_percent - initial_resource.memory_percent,
                    "memory_rss": final_resource.memory_rss - initial_resource.memory_rss,
                    "memory_vms": final_resource.memory_vms - initial_resource.memory_vms
                }
                
                # Create performance metrics
                metrics = PerformanceMetrics(
                    operation_name=operation_name,
                    operation_type=operation_type,
                    start_time=start_time,
                    end_time=end_time,
                    duration=duration,
                    success=success,
                    error_message=error_message,
                    attributes=span_attributes,
                    resource_usage=resource_delta
                )
                
                # Store performance data
                self.performance_data[operation_name].append(metrics)
                
                # Update metrics
                self._update_metrics(metrics)
                
                # Check for anomalies
                if self.config.anomaly_detection_enabled:
                    self._check_anomaly(metrics)
                
                # Add span attributes
                span.set_attribute("apm.duration_ms", duration * 1000)
                span.set_attribute("apm.success", success)
                span.set_attribute("apm.cpu_delta", resource_delta["cpu_percent"])
                span.set_attribute("apm.memory_delta", resource_delta["memory_percent"])
                
                # Decrement active operations counter
                self.active_operations_gauge.add(-1)
    
    def _update_metrics(self, metrics: PerformanceMetrics):
        """Update OpenTelemetry metrics."""
        # Update counters
        self.operation_counter.add(1, {
            "operation_name": metrics.operation_name,
            "operation_type": metrics.operation_type.value,
            "success": metrics.success
        })
        
        if not metrics.success:
            self.error_counter.add(1, {
                "operation_name": metrics.operation_name,
                "operation_type": metrics.operation_type.value
            })
        
        # Check for slow operation
        if metrics.duration > self.config.slow_request_threshold:
            self.slow_operation_counter.add(1, {
                "operation_name": metrics.operation_name,
                "operation_type": metrics.operation_type.value
            })
        
        # Update histograms
        self.duration_histogram.record(metrics.duration, {
            "operation_name": metrics.operation_name,
            "operation_type": metrics.operation_type.value
        })
        
        if metrics.resource_usage:
            self.memory_usage_histogram.record(metrics.resource_usage.get("memory_rss", 0), {
                "operation_name": metrics.operation_name,
                "operation_type": metrics.operation_type.value
            })
            
            self.cpu_usage_histogram.record(metrics.resource_usage.get("cpu_percent", 0), {
                "operation_name": metrics.operation_name,
                "operation_type": metrics.operation_type.value
            })
    
    def _check_anomaly(self, metrics: PerformanceMetrics):
        """Check for performance anomalies."""
        baseline = self.baselines.get(metrics.operation_name)
        if baseline and baseline.is_anomaly(metrics.duration, self.config.anomaly_detection_sensitivity):
            # Log anomaly
            logger.warning(
                f"Performance anomaly detected for {metrics.operation_name}: "
                f"duration={metrics.duration:.3f}s, "
                f"baseline_mean={baseline.mean_duration:.3f}s, "
                f"baseline_std={baseline.std_duration:.3f}s"
            )
            
            # Create anomaly event
            self.anomaly_detector.record_anomaly(metrics, baseline)
    
    def get_performance_summary(self, operation_name: str = None) -> Dict[str, Any]:
        """Get performance summary for operations."""
        if operation_name:
            metrics_list = self.performance_data.get(operation_name, [])
            if not metrics_list:
                return {"operation_name": operation_name, "message": "No data available"}
            
            durations = [m.duration for m in metrics_list]
            return {
                "operation_name": operation_name,
                "total_operations": len(metrics_list),
                "success_rate": sum(1 for m in metrics_list if m.success) / len(metrics_list),
                "mean_duration": statistics.mean(durations),
                "median_duration": statistics.median(durations),
                "p95_duration": np.percentile(durations, 95) if durations else 0,
                "p99_duration": np.percentile(durations, 99) if durations else 0,
                "min_duration": min(durations),
                "max_duration": max(durations),
                "baseline": self.baselines.get(operation_name).__dict__ if operation_name in self.baselines else None
            }
        else:
            # Return summary for all operations
            summary = {}
            for op_name, metrics_list in self.performance_data.items():
                if metrics_list:
                    summary[op_name] = self.get_performance_summary(op_name)
            return summary
    
    def get_current_resource_usage(self) -> ResourceUsage:
        """Get current resource usage."""
        return self.resource_monitor.get_current_usage()
    
    def get_baselines(self) -> Dict[str, PerformanceBaseline]:
        """Get all performance baselines."""
        return self.baselines.copy()
    
    def get_recent_anomalies(self, count: int = 10) -> List[Dict[str, Any]]:
        """Get recent performance anomalies."""
        return self.anomaly_detector.get_recent_anomalies(count)


class ResourceMonitor:
    """Monitor system resource usage."""
    
    def __init__(self, sample_interval: float = 1.0):
        """Initialize resource monitor."""
        self.sample_interval = sample_interval
        self._running = False
        self._monitor_thread = None
        self._current_usage = None
        self._usage_history = deque(maxlen=1000)
        self._process = psutil.Process()
    
    def start(self):
        """Start resource monitoring."""
        if self._running:
            return
        
        self._running = True
        self._monitor_thread = threading.Thread(target=self._monitor_resources, daemon=True)
        self._monitor_thread.start()
    
    def stop(self):
        """Stop resource monitoring."""
        if not self._running:
            return
        
        self._running = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=2)
    
    def _monitor_resources(self):
        """Monitor resource usage in background thread."""
        while self._running:
            try:
                usage = self._collect_resource_usage()
                self._current_usage = usage
                self._usage_history.append(usage)
                time.sleep(self.sample_interval)
            except Exception as e:
                logger.error(f"Error in resource monitoring: {e}")
    
    def _collect_resource_usage(self) -> ResourceUsage:
        """Collect current resource usage."""
        process = self._process
        
        # Get process-specific metrics
        cpu_percent = process.cpu_percent()
        memory_info = process.memory_info()
        memory_percent = process.memory_percent()
        thread_count = process.num_threads()
        
        # Get system-wide metrics
        try:
            open_files = process.num_fds() if hasattr(process, 'num_fds') else process.num_handles()
        except Exception:
            open_files = 0
        
        # Get network and disk I/O
        try:
            net_io = process.io_counters()
            network_io = {
                "bytes_sent": net_io.write_bytes,
                "bytes_recv": net_io.read_bytes
            }
        except Exception:
            network_io = {}
        
        try:
            disk_io = process.io_counters()
            disk_io_dict = {
                "write_bytes": disk_io.write_bytes,
                "read_bytes": disk_io.read_bytes
            }
        except Exception:
            disk_io_dict = {}
        
        return ResourceUsage(
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            memory_rss=memory_info.rss,
            memory_vms=memory_info.vms,
            thread_count=thread_count,
            open_files=open_files,
            network_io=network_io,
            disk_io=disk_io_dict
        )
    
    def get_current_usage(self) -> ResourceUsage:
        """Get current resource usage."""
        return self._current_usage or self._collect_resource_usage()
    
    def get_usage_history(self, count: int = 100) -> List[ResourceUsage]:
        """Get resource usage history."""
        return list(self._usage_history)[-count:]


class AnomalyDetector:
    """Detect performance anomalies."""
    
    def __init__(self, config: APMConfig):
        """Initialize anomaly detector."""
        self.config = config
        self.anomalies = deque(maxlen=1000)
        self.anomaly_callbacks = []
    
    def record_anomaly(self, metrics: PerformanceMetrics, baseline: PerformanceBaseline):
        """Record a performance anomaly."""
        anomaly = {
            "timestamp": datetime.now(),
            "operation_name": metrics.operation_name,
            "operation_type": metrics.operation_type.value,
            "duration": metrics.duration,
            "baseline_mean": baseline.mean_duration,
            "baseline_std": baseline.std_duration,
            "z_score": abs(metrics.duration - baseline.mean_duration) / baseline.std_duration if baseline.std_duration > 0 else 0,
            "severity": self._calculate_severity(metrics, baseline),
            "attributes": metrics.attributes
        }
        
        self.anomalies.append(anomaly)
        
        # Trigger callbacks
        for callback in self.anomaly_callbacks:
            try:
                callback(anomaly)
            except Exception as e:
                logger.error(f"Error in anomaly callback: {e}")
    
    def _calculate_severity(self, metrics: PerformanceMetrics, baseline: PerformanceBaseline) -> APMSeverity:
        """Calculate anomaly severity."""
        if baseline.std_duration == 0:
            return APMSeverity.INFO
        
        z_score = abs(metrics.duration - baseline.mean_duration) / baseline.std_duration
        
        if z_score > 5:
            return APMSeverity.CRITICAL
        elif z_score > 3:
            return APMSeverity.ERROR
        elif z_score > 2:
            return APMSeverity.WARNING
        else:
            return APMSeverity.INFO
    
    def add_anomaly_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """Add callback for anomaly notifications."""
        self.anomaly_callbacks.append(callback)
    
    def get_recent_anomalies(self, count: int = 10) -> List[Dict[str, Any]]:
        """Get recent anomalies."""
        return list(self.anomalies)[-count:]


# Global APM instance
_apm_instance = None


def get_apm() -> APMInstrumentation:
    """Get the global APM instance."""
    global _apm_instance
    if _apm_instance is None:
        testing_mode = os.getenv("TESTING_MODE", "").lower() == "true"
        apm_enabled_env = os.getenv("APM_ENABLED", "true").lower() == "true"
        config = APMConfig(enabled=(not testing_mode) and apm_enabled_env)
        _apm_instance = APMInstrumentation(config)
    return _apm_instance


def initialize_apm(config: APMConfig = None):
    """Initialize the global APM instance."""
    global _apm_instance
    # Respect testing mode and env override when initializing explicitly
    if config is None:
        testing_mode = os.getenv("TESTING_MODE", "").lower() == "true"
        apm_enabled_env = os.getenv("APM_ENABLED", "true").lower() == "true"
        config = APMConfig(enabled=(not testing_mode) and apm_enabled_env)
    else:
        if os.getenv("TESTING_MODE", "").lower() == "true":
            config.enabled = False
    _apm_instance = APMInstrumentation(config)
    return _apm_instance


# Decorators for APM instrumentation
def apm_traced(operation_name: str = None, operation_type: APMOperationType = APMOperationType.CUSTOM_OPERATION,
              attributes: Dict[str, Any] = None):
    """Decorator to trace functions with APM."""
    def decorator(func):
        op_name = operation_name or f"{func.__module__}.{func.__name__}"
        
        if asyncio.iscoroutinefunction(func):
            async def async_wrapper(*args, **kwargs):
                apm = get_apm()
                async with apm.trace_async_operation(op_name, operation_type, attributes):
                    return await func(*args, **kwargs)
            return async_wrapper
        else:
            def sync_wrapper(*args, **kwargs):
                apm = get_apm()
                with apm.trace_operation(op_name, operation_type, attributes):
                    return func(*args, **kwargs)
            return sync_wrapper
    
    return decorator


# Convenience functions for common operations
def trace_http_request(method: str, url: str, status_code: int, duration: float):
    """Trace HTTP request with APM."""
    apm = get_apm()
    attributes = {
        "http.method": method,
        "http.url": url,
        "http.status_code": status_code
    }
    
    with apm.trace_operation(f"{method} {url}", APMOperationType.HTTP_REQUEST, attributes) as span:
        if span is not None:
            span.set_attribute("http.reported_duration_ms", duration * 1000)


def trace_database_query(query: str, duration: float, success: bool = True):
    """Trace database query with APM."""
    apm = get_apm()
    attributes = {
        "db.query": query,
        "db.success": success
    }
    
    with apm.trace_operation("database_query", APMOperationType.DATABASE_QUERY, attributes) as span:
        if span is not None:
            span.set_attribute("db.reported_duration_ms", duration * 1000)


def trace_external_api(service: str, endpoint: str, duration: float, success: bool = True):
    """Trace external API call with APM."""
    apm = get_apm()
    attributes = {
        "external_api.service": service,
        "external_api.endpoint": endpoint,
        "external_api.success": success
    }
    
    with apm.trace_operation(f"{service}_{endpoint}", APMOperationType.EXTERNAL_API, attributes) as span:
        if span is not None:
            span.set_attribute("external_api.reported_duration_ms", duration * 1000)
