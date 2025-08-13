"""
Comprehensive metrics testing and validation utilities for MCP System.

This module provides advanced testing capabilities for metrics collection and export,
including validation, performance testing, and integration testing for Prometheus metrics.
"""

import logging
import asyncio
import time
import httpx
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum
from prometheus_client import (
    Counter, Histogram, CollectorRegistry
)

from ..common.metrics import (
    MetricsCollector, get_metrics_output
)

logger = logging.getLogger(__name__)


class MetricsTestScenario(Enum):
    """Test scenario types for metrics."""
    BASIC_METRICS_COLLECTION = "basic_metrics_collection"
    COUNTER_METRICS = "counter_metrics"
    HISTOGRAM_METRICS = "histogram_metrics"
    GAUGE_METRICS = "gauge_metrics"
    METRICS_EXPORT = "metrics_export"
    METRICS_ENDPOINT = "metrics_endpoint"
    PERFORMANCE_MONITORING = "performance_monitoring"
    CUSTOM_METRICS = "custom_metrics"
    METRICS_VALIDATION = "metrics_validation"
    METRICS_LABELS = "metrics_labels"
    METRICS_REGISTRY = "metrics_registry"
    METRICS_RESET = "metrics_reset"
    METRICS_SCRAPE = "metrics_scrape"
    METRICS_INTEGRATION = "metrics_integration"
    METRICS_PERFORMANCE = "metrics_performance"
    METRICS_RECOVERY = "metrics_recovery"


@dataclass
class MetricsTestResult:
    """Result of a metrics test."""
    test_name: str
    scenario: MetricsTestScenario
    status: str  # "PASSED", "FAILED", "WARNING", "ERROR"
    duration_ms: float
    metrics: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    metrics_collected: int = 0
    timestamp: float = field(default_factory=time.time)


@dataclass
class MetricsTestConfig:
    """Configuration for metrics testing."""
    test_timeout: float = 30.0
    max_metrics_per_test: int = 1000
    performance_threshold_ms: float = 100.0
    enable_comprehensive_validation: bool = True
    metrics_endpoint_url: str = "http://localhost:8000/metrics"
    scrape_interval_seconds: float = 15.0
    validation_tolerance: float = 0.01  # 1% tolerance for metric value validation
    test_registry: bool = True
    test_custom_metrics: bool = True
    test_performance_monitoring: bool = True
    test_metrics_export: bool = True


class MetricsTestingManager:
    """Comprehensive testing manager for metrics collection and export."""
    
    def __init__(self, config: MetricsTestConfig = None):
        """Initialize metrics testing manager."""
        self.config = config or MetricsTestConfig()
        self.test_registry = CollectorRegistry()
        self.service_collectors: Dict[str, MetricsCollector] = {}
        
        # Test metrics
        self.test_counter = Counter(
            'observability_metrics_tests_total',
            'Total number of metrics tests executed',
            ['test_name', 'scenario', 'status'],
            registry=self.test_registry
        )
        
        self.test_duration = Histogram(
            'observability_metrics_test_duration_seconds',
            'Duration of metrics tests',
            ['test_name', 'scenario'],
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0],
            registry=self.test_registry
        )
        
        self.validation_errors = Counter(
            'observability_metrics_validation_errors_total',
            'Total number of metrics validation errors',
            ['validation_type', 'severity'],
            registry=self.test_registry
        )
        
        # Test results storage
        self.test_results: List[MetricsTestResult] = []
        self.active_tests: Dict[str, asyncio.Task] = {}
        
        # HTTP client for metrics endpoint testing
        self.http_client = httpx.AsyncClient(timeout=self.config.test_timeout)
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """
        Run all metrics tests and return comprehensive results.
        
        Returns:
            Dictionary with test results and summary statistics
        """
        logger.info("Starting comprehensive metrics testing suite")
        
        start_time = time.time()
        results = {
            "tests": {},
            "summary": {
                "total_tests": 0,
                "passed": 0,
                "failed": 0,
                "warning": 0,
                "error": 0,
                "total_duration_ms": 0
            },
            "performance": {},
            "validation": {},
            "recommendations": []
        }
        
        # Run all test scenarios
        test_scenarios = [
            (MetricsTestScenario.BASIC_METRICS_COLLECTION, self._test_basic_metrics_collection),
            (MetricsTestScenario.COUNTER_METRICS, self._test_counter_metrics),
            (MetricsTestScenario.HISTOGRAM_METRICS, self._test_histogram_metrics),
            (MetricsTestScenario.GAUGE_METRICS, self._test_gauge_metrics),
            (MetricsTestScenario.METRICS_EXPORT, self._test_metrics_export),
            (MetricsTestScenario.METRICS_ENDPOINT, self._test_metrics_endpoint),
            (MetricsTestScenario.PERFORMANCE_MONITORING, self._test_performance_monitoring),
            (MetricsTestScenario.CUSTOM_METRICS, self._test_custom_metrics),
            (MetricsTestScenario.METRICS_VALIDATION, self._test_metrics_validation),
            (MetricsTestScenario.METRICS_LABELS, self._test_metrics_labels),
            (MetricsTestScenario.METRICS_REGISTRY, self._test_metrics_registry),
            (MetricsTestScenario.METRICS_RESET, self._test_metrics_reset),
            (MetricsTestScenario.METRICS_SCRAPE, self._test_metrics_scrape),
            (MetricsTestScenario.METRICS_INTEGRATION, self._test_metrics_integration),
            (MetricsTestScenario.METRICS_PERFORMANCE, self._test_metrics_performance),
            (MetricsTestScenario.METRICS_RECOVERY, self._test_metrics_recovery)
        ]
        
        for scenario, test_func in test_scenarios:
            try:
                test_result = await test_func()
                results["tests"][scenario.value] = test_result
                
                # Update summary statistics
                results["summary"]["total_tests"] += 1
                if test_result.status == "PASSED":
                    results["summary"]["passed"] += 1
                elif test_result.status == "FAILED":
                    results["summary"]["failed"] += 1
                elif test_result.status == "WARNING":
                    results["summary"]["warning"] += 1
                elif test_result.status == "ERROR":
                    results["summary"]["error"] += 1
                
                # Store test result
                self.test_results.append(test_result)
                
                # Update metrics
                self.test_counter.labels(
                    test_name=test_result.test_name,
                    scenario=scenario.value,
                    status=test_result.status
                ).inc()
                
                self.test_duration.labels(
                    test_name=test_result.test_name,
                    scenario=scenario.value
                ).observe(test_result.duration_ms / 1000.0)
                
            except Exception as e:
                logger.error(f"Test {scenario.value} failed with exception: {e}")
                error_result = MetricsTestResult(
                    test_name=scenario.value,
                    scenario=scenario,
                    status="ERROR",
                    duration_ms=0,
                    error_message=str(e)
                )
                results["tests"][scenario.value] = error_result
                results["summary"]["total_tests"] += 1
                results["summary"]["error"] += 1
                self.test_results.append(error_result)
        
        # Calculate total duration
        results["summary"]["total_duration_ms"] = (time.time() - start_time) * 1000
        
        # Generate performance summary
        results["performance"] = self._generate_performance_summary()
        
        # Generate validation summary
        results["validation"] = self._generate_validation_summary()
        
        # Generate recommendations
        results["recommendations"] = self._generate_recommendations(results)
        
        logger.info(f"Metrics testing suite completed in {results['summary']['total_duration_ms']:.2f}ms")
        return results
    
    async def _test_basic_metrics_collection(self) -> MetricsTestResult:
        """Test basic metrics collection functionality."""
        start_time = time.time()
        test_name = "basic_metrics_collection"
        
        try:
            # Create a test metrics collector
            test_collector = MetricsCollector("test_service")
            
            # Record various types of metrics
            test_collector.record_request("GET", "/test", "success")
            test_collector.record_db_query("SELECT", "test_table", 0.1)
            test_collector.record_business_operation("test_operation", "success", 0.2)
            test_collector.record_error("test_error", "low", "Test error message")
            test_collector.set_active_connections(5)
            test_collector.set_queue_size("test_queue", 10)
            test_collector.record_cache_operation("get", "hit")
            test_collector.record_message_sent()
            test_collector.record_message_received()
            
            # Get metrics output
            metrics_output = get_metrics_output()
            
            # Validate metrics output
            validation_results = {
                "has_request_metrics": "mcp_requests_total" in metrics_output,
                "has_db_metrics": "mcp_db_queries_total" in metrics_output,
                "has_business_metrics": "mcp_business_operations_total" in metrics_output,
                "has_error_metrics": "mcp_errors_total" in metrics_output,
                "has_system_metrics": "mcp_active_connections" in metrics_output,
                "has_cache_metrics": "mcp_cache_operations_total" in metrics_output,
                "has_messaging_metrics": "mcp_a2a_messages_sent_total" in metrics_output,
                "metrics_output_length": len(metrics_output),
                "service_stats": test_collector.get_service_stats()
            }
            
            # Calculate success rate
            success_count = sum(1 for v in validation_results.values() if isinstance(v, bool) and v)
            total_checks = sum(1 for v in validation_results.values() if isinstance(v, bool))
            success_rate = success_count / total_checks if total_checks > 0 else 0
            
            duration_ms = (time.time() - start_time) * 1000
            
            # Determine test status
            if success_rate >= 0.8:  # 80% success rate threshold
                status = "PASSED"
            elif success_rate >= 0.5:  # 50% success rate threshold
                status = "WARNING"
            else:
                status = "FAILED"
            
            return MetricsTestResult(
                test_name=test_name,
                scenario=MetricsTestScenario.BASIC_METRICS_COLLECTION,
                status=status,
                duration_ms=duration_ms,
                metrics=validation_results,
                metrics_collected=total_checks
            )
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return MetricsTestResult(
                test_name=test_name,
                scenario=MetricsTestScenario.BASIC_METRICS_COLLECTION,
                status="ERROR",
                duration_ms=duration_ms,
                error_message=str(e)
            )
    
    async def _test_counter_metrics(self) -> MetricsTestResult:
        """Test counter metrics functionality."""
