"""
Performance baselines and anomaly detection for MCP services.
Provides baseline establishment, anomaly detection, trend analysis, and performance degradation alerting.
"""

import logging
import time
import asyncio
import statistics
from typing import Dict, Any, Optional, List, Union, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
import json
import numpy as np
from datetime import datetime, timedelta
import threading
import queue

from opentelemetry import trace, metrics
from opentelemetry.trace import Status, StatusCode, SpanKind
from opentelemetry.semconv.trace import SpanAttributes

from src.common.apm import (
    APMInstrumentation, 
    APMOperationType, 
    APMConfig, 
    PerformanceMetrics,
    get_apm
)
from src.common.tracing import get_tracing_config
from src.common.performance_profiling import get_performance_profiler

logger = logging.getLogger(__name__)


class AnomalyType(Enum):
    """Types of anomalies that can be detected."""
    SPIKE = "spike"
    DIP = "dip"
    DRIFT = "drift"
    OUTLIER = "outlier"
    PATTERN_CHANGE = "pattern_change"
    THRESHOLD_BREACH = "threshold_breach"
    TREND_CHANGE = "trend_change"


class SeverityLevel(Enum):
    """Severity levels for anomalies."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class PerformanceBaseline:
    """Performance baseline data."""
    metric_name: str
    service_name: str
    operation_name: str = ""
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    sample_count: int = 0
    mean: float = 0.0
    median: float = 0.0
    std_dev: float = 0.0
    min_value: float = 0.0
    max_value: float = 0.0
    percentile_25: float = 0.0
    percentile_75: float = 0.0
    percentile_95: float = 0.0
    percentile_99: float = 0.0
    trend: float = 0.0  # Slope of trend line
    seasonality: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AnomalyDetection:
    """Anomaly detection configuration and results."""
    metric_name: str
    service_name: str
    operation_name: str = ""
    detection_method: str = "statistical"
    threshold_multiplier: float = 3.0  # For statistical methods
    threshold_absolute: float = 0.0  # For absolute threshold methods
    min_samples: int = 30
    window_size: int = 100
    sensitivity: float = 0.05  # 5% change considered significant
    enabled: bool = True
    last_check: float = 0.0
    anomaly_count: int = 0
    last_anomaly: Optional[Dict[str, Any]] = None


@dataclass
class Anomaly:
    """Detected anomaly information."""
    anomaly_id: str
    metric_name: str
    service_name: str
    operation_name: str
    anomaly_type: AnomalyType
    severity: SeverityLevel
    detected_at: float
    value: float
    expected_range: Tuple[float, float]
    baseline: PerformanceBaseline
    description: str
    confidence: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    resolved: bool = False
    resolved_at: Optional[float] = None
    resolution_notes: Optional[str] = None


@dataclass
class PerformanceTrend:
    """Performance trend analysis data."""
    metric_name: str
    service_name: str
    operation_name: str = ""
    trend_direction: str = "stable"  # increasing, decreasing, stable
    trend_strength: float = 0.0  # 0.0 to 1.0
    change_rate: float = 0.0  # Rate of change per unit time
    r_squared: float = 0.0  # Goodness of fit for trend line
    period_start: float = 0.0
    period_end: float = 0.0
    sample_count: int = 0
    forecast: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class PerformanceAlert:
    """Performance alert information."""
    alert_id: str
    metric_name: str
    service_name: str
    operation_name: str
    alert_type: str
    severity: SeverityLevel
    triggered_at: float
    condition: str
    value: float
    threshold: float
    description: str
    acknowledged: bool = False
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[float] = None
    resolved: bool = False
    resolved_at: Optional[float] = None
    resolution_notes: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class PerformanceBaselineManager:
    """Manages performance baselines, anomaly detection, and alerting."""
    
    def __init__(self, config: APMConfig = None):
        """Initialize performance baseline manager."""
        self.config = config or APMConfig()
        self.apm = get_apm()
        self.tracer = get_tracing_config().get_tracer()
        self.meter = get_tracing_config().get_meter()
        self.profiler = get_performance_profiler()
        
        # Data storage
        self.baselines = {}  # (metric_name, service_name, operation_name) -> PerformanceBaseline
        self.anomaly_configs = {}  # (metric_name, service_name, operation_name) -> AnomalyDetection
        self.anomalies = deque(maxlen=10000)
        self.trends = {}  # (metric_name, service_name, operation_name) -> PerformanceTrend
        self.alerts = deque(maxlen=5000)
        
        # Metric history for analysis
        self.metric_history = defaultdict(lambda: deque(maxlen=10000))
        
        # Alerting configuration
        self.alert_rules = []
        self.alert_thresholds = {
            "response_time_p95": 5.0,  # seconds
            "error_rate": 0.05,  # 5%
            "cpu_usage": 0.8,  # 80%
            "memory_usage": 0.9,  # 90%
            "throughput_decrease": 0.2,  # 20% decrease
            "latency_increase": 0.5  # 50% increase
        }
        
        # Background processing
        self.running = False
        self.baseline_update_interval = 3600  # 1 hour
        self.anomaly_check_interval = 60  # 1 minute
        self.trend_analysis_interval = 300  # 5 minutes
        self.background_thread = None
        self.task_queue = queue.Queue()
        
        # Initialize metrics
        self._initialize_metrics()
        
        # Start background processing
        self.start_background_processing()
    
    def _initialize_metrics(self):
        """Initialize OpenTelemetry metrics for performance baselines."""
        # Counters
        self.baseline_updates_counter = self.meter.create_counter(
            "performance_baselines_updates_total",
            description="Total number of baseline updates"
        )
        
        self.anomalies_detected_counter = self.meter.create_counter(
            "performance_baselines_anomalies_total",
            description="Total number of anomalies detected"
        )
        
        self.alerts_triggered_counter = self.meter.create_counter(
            "performance_baselines_alerts_total",
            description="Total number of alerts triggered"
        )
        
        # Histograms
        self.baseline_accuracy_histogram = self.meter.create_histogram(
            "performance_baselines_accuracy",
            description="Accuracy of performance baselines"
        )
        
        self.anomaly_confidence_histogram = self.meter.create_histogram(
            "performance_baselines_anomaly_confidence",
            description="Confidence level of detected anomalies"
        )
        
        # Gauges
        self.active_baselines_gauge = self.meter.create_up_down_counter(
            "performance_baselines_active",
            description="Number of active performance baselines"
        )
        
        self.active_anomalies_gauge = self.meter.create_up_down_counter(
            "performance_baselines_active_anomalies",
            description="Number of active anomalies"
        )
        
        self.active_alerts_gauge = self.meter.create_up_down_counter(
            "performance_baselines_active_alerts",
            description="Number of active alerts"
        )
    
    def start_background_processing(self):
        """Start background processing threads."""
        if not self.running:
            self.running = True
            self.background_thread = threading.Thread(target=self._background_processor)
            self.background_thread.daemon = True
            self.background_thread.start()
            logger.info("Performance baseline background processing started")
    
    def stop_background_processing(self):
        """Stop background processing threads."""
        self.running = False
        if self.background_thread:
            self.background_thread.join()
        logger.info("Performance baseline background processing stopped")
    
    def _background_processor(self):
        """Background processor for periodic tasks."""
        while self.running:
            try:
                # Process tasks from queue
                try:
                    task = self.task_queue.get(timeout=1.0)
                    task()
                    self.task_queue.task_done()
                except queue.Empty:
                    pass
                
                # Check if it's time to update baselines
                current_time = time.time()
                if current_time % self.baseline_update_interval < 60:
                    self._update_all_baselines()
                
                # Check for anomalies
                if current_time % self.anomaly_check_interval < 10:
                    self._check_all_anomalies()
                
                # Analyze trends
                if current_time % self.trend_analysis_interval < 30:
                    self._analyze_all_trends()
                
                # Sleep for a short interval
                time.sleep(10)
            except Exception as e:
                logger.error(f"Error in background processor: {e}")
    
    def record_metric(self, metric_name: str, service_name: str, value: float,
                     operation_name: str = "", timestamp: float = None):
        """Record a metric value for baseline analysis."""
        if timestamp is None:
            timestamp = time.time()
        
        # Store metric value
        key = (metric_name, service_name, operation_name)
        self.metric_history[key].append({
            "timestamp": timestamp,
            "value": value
        })
        
        # Queue for processing
        self.task_queue.put(lambda: self._process_metric(key, value, timestamp))
    
    def _process_metric(self, key: Tuple[str, str, str], value: float, timestamp: float):
        """Process a metric value."""
        metric_name, service_name, operation_name = key
        
        # Check for anomalies if we have a baseline
        if key in self.baselines:
            self._check_for_anomaly(key, value, timestamp)
        
        # Check alert rules
        self._check_alert_rules(metric_name, service_name, operation_name, value, timestamp)
    
    def establish_baseline(self, metric_name: str, service_name: str, 
                         operation_name: str = "", sample_size: int = 100) -> PerformanceBaseline:
        """Establish a performance baseline for a metric."""
        key = (metric_name, service_name, operation_name)
        
        # Get metric history
        history = self.metric_history[key]
        if len(history) < sample_size:
            logger.warning(f"Insufficient data for baseline: {key}, only {len(history)} samples")
            return None
        
        # Get recent samples
        samples = [item["value"] for item in list(history)[-sample_size:]]
        
        # Calculate statistics
        mean = statistics.mean(samples)
        median = statistics.median(samples)
        std_dev = statistics.stdev(samples) if len(samples) > 1 else 0.0
        min_value = min(samples)
        max_value = max(samples)
        
        # Calculate percentiles
        sorted_samples = sorted(samples)
        percentile_25 = np.percentile(sorted_samples, 25)
        percentile_75 = np.percentile(sorted_samples, 75)
        percentile_95 = np.percentile(sorted_samples, 95)
        percentile_99 = np.percentile(sorted_samples, 99)
        
        # Calculate trend
        trend = self._calculate_trend_slope(samples)
        
        # Create baseline
        baseline = PerformanceBaseline(
            metric_name=metric_name,
            service_name=service_name,
            operation_name=operation_name,
            sample_count=len(samples),
            mean=mean,
            median=median,
            std_dev=std_dev,
            min_value=min_value,
            max_value=max_value,
            percentile_25=percentile_25,
