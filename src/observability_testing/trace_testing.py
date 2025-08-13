"""
Comprehensive distributed tracing testing utilities for MCP System.

This module provides advanced testing capabilities for distributed tracing components,
including validation, performance testing, and integration testing.
"""

import logging
import logging
import asyncio
import time
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum
from prometheus_client import Counter, Histogram

from opentelemetry.trace import (
    Status, StatusCode
)

from ..common.tracing import get_tracing_config, get_tracer
from ..common.trace_validation import (
    TraceValidator, TraceHealthChecker, TraceIntegrationTester,
    ValidationLevel, ValidationStatus
)
from ..common.trace_propagation import TracePropagationUtils
from ..common.trace_sampling import get_trace_sampling_manager
import os
from ..common.trace_exporters import get_trace_exporter_manager

logger = logging.getLogger(__name__)


class TestScenario(Enum):
    """Test scenario types for tracing."""
    BASIC_SPAN_CREATION = "basic_span_creation"
    SPAN_HIERARCHY = "span_hierarchy"
    TRACE_CONTEXT_PROPAGATION = "trace_context_propagation"
    CROSS_SERVICE_TRACING = "cross_service_tracing"
    ERROR_HANDLING = "error_handling"
    PERFORMANCE_BENCHMARK = "performance_benchmark"
    SAMPLING_VALIDATION = "sampling_validation"
    EXPORTER_RELIABILITY = "exporter_reliability"
    RECOVERY_TESTING = "recovery_testing"


@dataclass
class TraceTestResult:
    """Result of a trace test."""
    test_name: str
    scenario: TestScenario
    status: ValidationStatus
    duration_ms: float
    metrics: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    trace_id: Optional[str] = None
    spans_count: int = 0
    timestamp: float = field(default_factory=time.time)


@dataclass
class TraceTestConfig:
    """Configuration for trace testing."""
    test_timeout: float = 30.0
    max_spans_per_test: int = 1000
    performance_threshold_ms: float = 100.0
    enable_comprehensive_validation: bool = True
    sampling_validation_enabled: bool = True
    exporter_validation_enabled: bool = True
    error_injection_enabled: bool = False
    performance_benchmark_enabled: bool = True


class TraceTestingManager:
    """Comprehensive testing manager for distributed tracing."""
    
    def __init__(self, config: TraceTestConfig = None):
        """Initialize trace testing manager."""
        self.config = config or TraceTestConfig()
        self.tracing_config = get_tracing_config()
        self.validator = TraceValidator()
        self.health_checker = TraceHealthChecker()
        self.integration_tester = TraceIntegrationTester()
        self.propagation_utils = TracePropagationUtils()
        self.sampling_manager = get_trace_sampling_manager()
        # In testing mode, disable exporter manager to avoid network calls
        if os.getenv("TESTING_MODE", "").lower() == "true":
            self.exporter_manager = None
        else:
            self.exporter_manager = get_trace_exporter_manager()
        
        # Test metrics
        self.test_counter = Counter(
            'observability_trace_tests_total',
            'Total number of trace tests executed',
            ['test_name', 'scenario', 'status']
        )
        
        self.test_duration = Histogram(
            'observability_trace_test_duration_seconds',
            'Duration of trace tests',
            ['test_name', 'scenario'],
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0]
        )
        
        self.validation_errors = Counter(
            'observability_trace_validation_errors_total',
            'Total number of trace validation errors',
            ['validation_type', 'severity']
        )
        
        # Test results storage
        self.test_results: List[TraceTestResult] = []
        self.active_tests: Dict[str, asyncio.Task] = {}
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """
        Run all trace tests and return comprehensive results.
        
        Returns:
            Dictionary with test results and summary statistics
        """
        logger.info("Starting comprehensive trace testing suite")
        
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
            (TestScenario.BASIC_SPAN_CREATION, self._test_basic_span_creation),
            (TestScenario.SPAN_HIERARCHY, self._test_span_hierarchy),
            (TestScenario.TRACE_CONTEXT_PROPAGATION, self._test_trace_context_propagation),
            (TestScenario.CROSS_SERVICE_TRACING, self._test_cross_service_tracing),
            (TestScenario.ERROR_HANDLING, self._test_error_handling),
            (TestScenario.PERFORMANCE_BENCHMARK, self._test_performance_benchmark),
            (TestScenario.SAMPLING_VALIDATION, self._test_sampling_validation),
            (TestScenario.EXPORTER_RELIABILITY, self._test_exporter_reliability),
            (TestScenario.RECOVERY_TESTING, self._test_recovery_testing)
        ]
        
        for scenario, test_func in test_scenarios:
            try:
                test_result = await test_func()
                results["tests"][scenario.value] = test_result
                
                # Update summary statistics
                results["summary"]["total_tests"] += 1
                if test_result.status == ValidationStatus.PASSED:
                    results["summary"]["passed"] += 1
                elif test_result.status == ValidationStatus.FAILED:
                    results["summary"]["failed"] += 1
                elif test_result.status == ValidationStatus.WARNING:
                    results["summary"]["warning"] += 1
                elif test_result.status == ValidationStatus.ERROR:
                    results["summary"]["error"] += 1
                
                # Store test result
                self.test_results.append(test_result)
                
                # Update metrics
                self.test_counter.labels(
                    test_name=test_result.test_name,
                    scenario=scenario.value,
                    status=test_result.status.value
                ).inc()
                
                self.test_duration.labels(
                    test_name=test_result.test_name,
                    scenario=scenario.value
                ).observe(test_result.duration_ms / 1000.0)
                
            except Exception as e:
                logger.error(f"Test {scenario.value} failed with exception: {e}")
                error_result = TraceTestResult(
                    test_name=scenario.value,
                    scenario=scenario,
                    status=ValidationStatus.ERROR,
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
        
        logger.info(f"Trace testing suite completed in {results['summary']['total_duration_ms']:.2f}ms")
        return results
    
    async def _test_basic_span_creation(self) -> TraceTestResult:
        """Test basic span creation functionality."""
        start_time = time.time()
        test_name = "basic_span_creation"
        
        try:
            tracer = get_tracer()
            spans = []
            
            # Create multiple test spans
            for i in range(10):
                with tracer.start_as_current_span(f"test_span_{i}") as span:
                    span.set_attribute("test.attribute", f"value_{i}")
                    span.set_status(Status(StatusCode.OK))
                    spans.append(span)
            
            # Validate spans
            validation_report = self.validator.validate_trace(
                spans, 
                ValidationLevel.BASIC
            )
            
            # Check performance
            duration_ms = (time.time() - start_time) * 1000
            performance_ok = duration_ms < self.config.performance_threshold_ms
            
            # Determine test status
            if validation_report.overall_status == ValidationStatus.PASSED and performance_ok:
                status = ValidationStatus.PASSED
            elif validation_report.overall_status == ValidationStatus.ERROR:
                status = ValidationStatus.ERROR
            else:
                status = ValidationStatus.WARNING
            
            return TraceTestResult(
                test_name=test_name,
                scenario=TestScenario.BASIC_SPAN_CREATION,
                status=status,
                duration_ms=duration_ms,
                metrics={
                    "spans_created": len(spans),
                    "validation_results": len(validation_report.results),
                    "performance_threshold_ms": self.config.performance_threshold_ms
                },
                spans_count=len(spans)
            )
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return TraceTestResult(
                test_name=test_name,
                scenario=TestScenario.BASIC_SPAN_CREATION,
                status=ValidationStatus.ERROR,
                duration_ms=duration_ms,
                error_message=str(e)
            )
    
    async def _test_span_hierarchy(self) -> TraceTestResult:
        """Test span hierarchy and parent-child relationships."""
        start_time = time.time()
        test_name = "span_hierarchy"
        
        try:
            tracer = get_tracer()
            spans = []
            
            # Create hierarchical spans
            with tracer.start_as_current_span("root_span") as root_span:
                spans.append(root_span)
                
                # Create child spans
                for i in range(3):
                    with tracer.start_as_current_span(f"child_span_{i}") as child_span:
                        spans.append(child_span)
                        
                        # Create grandchild spans
                        for j in range(2):
                            with tracer.start_as_current_span(f"grandchild_span_{i}_{j}") as grandchild_span:
                                spans.append(grandchild_span)
            
            # Validate hierarchy
            validation_report = self.validator.validate_trace(
                spans, 
                ValidationLevel.STRICT
            )
            
            # Check hierarchy integrity
            hierarchy_issues = 0
            for span in spans:
                if span != spans[0] and span.parent is None:
                    hierarchy_issues += 1
            
            duration_ms = (time.time() - start_time) * 1000
            
            # Determine test status
            if validation_report.overall_status == ValidationStatus.PASSED and hierarchy_issues == 0:
                status = ValidationStatus.PASSED
            elif hierarchy_issues > 0:
                status = ValidationStatus.WARNING
            else:
                status = ValidationStatus.FAILED
            
            return TraceTestResult(
                test_name=test_name,
                scenario=TestScenario.SPAN_HIERARCHY,
                status=status,
                duration_ms=duration_ms,
                metrics={
                    "spans_created": len(spans),
                    "hierarchy_issues": hierarchy_issues,
                    "validation_results": len(validation_report.results)
                },
                spans_count=len(spans)
            )
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return TraceTestResult(
                test_name=test_name,
                scenario=TestScenario.SPAN_HIERARCHY,
                status=ValidationStatus.ERROR,
                duration_ms=duration_ms,
                error_message=str(e)
            )
    
    async def _test_trace_context_propagation(self) -> TraceTestResult:
        """Test trace context propagation across service boundaries."""
        start_time = time.time()
        test_name = "trace_context_propagation"
        
        try:
            tracer = get_tracer()
            propagated_contexts = []
            
            # Create parent span with context
            with tracer.start_as_current_span("parent_span") as parent_span:
                parent_trace_id = parent_span.context.trace_id
                
                # Simulate context extraction and injection
                for i in range(5):
                    # Extract current context
                    carrier = {}
                    self.propagation_utils.inject_trace_context(carrier)
                    
                    # Simulate service boundary
                    propagated_contexts.append(carrier)
                    
                    # Create child span with extracted context
                    with tracer.start_as_current_span(f"service_{i}_span") as child_span:
                        child_trace_id = child_span.context.trace_id
                        
                        # Verify trace ID consistency
                        if parent_trace_id != child_trace_id:
                            raise ValueError(f"Trace ID mismatch in service {i}")
            
            # Validate all contexts
            context_validation_issues = 0
            for i, context in enumerate(propagated_contexts):
                if not context.get("traceparent"):
                    context_validation_issues += 1
            
            duration_ms = (time.time() - start_time) * 1000
            
            # Determine test status
            if context_validation_issues == 0:
                status = ValidationStatus.PASSED
            else:
                status = ValidationStatus.FAILED
            
            return TraceTestResult(
                test_name=test_name,
                scenario=TestScenario.TRACE_CONTEXT_PROPAGATION,
                status=status,
                duration_ms=duration_ms,
                metrics={
                    "contexts_tested": len(propagated_contexts),
                    "context_validation_issues": context_validation_issues
                }
            )
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return TraceTestResult(
                test_name=test_name,
                scenario=TestScenario.TRACE_CONTEXT_PROPAGATION,
                status=ValidationStatus.ERROR,
                duration_ms=duration_ms,
                error_message=str(e)
            )
    
    async def _test_cross_service_tracing(self) -> TraceTestResult:
        """Test cross-service tracing with simulated HTTP calls."""
        start_time = time.time()
        test_name = "cross_service_tracing"
        
        try:
            tracer = get_tracer()
            spans = []
            
            # Simulate cross-service call
            with tracer.start_as_current_span("service_a_request") as service_a_span:
                spans.append(service_a_span)
                
                # Simulate HTTP call to service B
                with tracer.start_as_current_span("http_call_to_service_b") as http_span:
                    spans.append(http_span)
                    http_span.set_attribute("http.method", "GET")
                    http_span.set_attribute("http.url", "http://service-b/api/endpoint")
                    http_span.set_attribute("http.status_code", 200)
                    
                    # Simulate processing in service B
                    with tracer.start_as_current_span("service_b_processing") as service_b_span:
                        spans.append(service_b_span)
                        service_b_span.set_attribute("service.name", "service-b")
                        
                        # Simulate database call
                        with tracer.start_as_current_span("database_query") as db_span:
                            spans.append(db_span)
                            db_span.set_attribute("db.system", "postgresql")
                            db_span.set_attribute("db.statement", "SELECT * FROM users")
            
            # Validate cross-service trace
            validation_report = self.validator.validate_trace(
                spans, 
                ValidationLevel.COMPREHENSIVE
            )
            
            # Check for service-specific attributes
            service_attributes_ok = all(
                span.attributes.get("service.name") or 
                span.attributes.get("http.method") or 
                span.attributes.get("db.system")
                for span in spans
            )
            
            duration_ms = (time.time() - start_time) * 1000
            
            # Determine test status
            if validation_report.overall_status == ValidationStatus.PASSED and service_attributes_ok:
                status = ValidationStatus.PASSED
            else:
                status = ValidationStatus.WARNING
            
            return TraceTestResult(
                test_name=test_name,
                scenario=TestScenario.CROSS_SERVICE_TRACING,
                status=status,
                duration_ms=duration_ms,
                metrics={
                    "spans_created": len(spans),
                    "services_simulated": 2,
                    "service_attributes_ok": service_attributes_ok,
                    "validation_results": len(validation_report.results)
                },
                spans_count=len(spans)
            )
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return TraceTestResult(
                test_name=test_name,
                scenario=TestScenario.CROSS_SERVICE_TRACING,
                status=ValidationStatus.ERROR,
                duration_ms=duration_ms,
                error_message=str(e)
            )
    
    async def _test_error_handling(self) -> TraceTestResult:
        """Test error handling and exception tracing."""
        start_time = time.time()
        test_name = "error_handling"
        
        try:
            tracer = get_tracer()
            spans = []
            errors_created = 0
            
            # Create spans with errors
            for i in range(3):
                try:
                    with tracer.start_as_current_span(f"error_span_{i}") as span:
                        spans.append(span)
                        
                        # Simulate different types of errors
                        if i == 0:
                            raise ValueError("Test value error")
                        elif i == 1:
                            raise ConnectionError("Test connection error")
                        else:
                            raise RuntimeError("Test runtime error")
                            
                except Exception:
                    errors_created += 1
                    # Exception should be recorded in span
            
            # Validate error handling
            validation_report = self.validator.validate_trace(
                spans, 
                ValidationLevel.STRICT
            )
            
            # Check for error status in spans
            error_spans = sum(1 for span in spans if span.status and span.status.status_code == StatusCode.ERROR)
            
            duration_ms = (time.time() - start_time) * 1000
            
            # Determine test status
            if error_spans == errors_created and validation_report.overall_status != ValidationStatus.ERROR:
                status = ValidationStatus.PASSED
            else:
                status = ValidationStatus.FAILED
            
            return TraceTestResult(
                test_name=test_name,
                scenario=TestScenario.ERROR_HANDLING,
                status=status,
                duration_ms=duration_ms,
                metrics={
                    "spans_created": len(spans),
                    "errors_created": errors_created,
                    "error_spans_recorded": error_spans,
                    "error_recording_accuracy": error_spans / errors_created if errors_created > 0 else 0
                },
                spans_count=len(spans)
            )
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return TraceTestResult(
                test_name=test_name,
                scenario=TestScenario.ERROR_HANDLING,
                status=ValidationStatus.ERROR,
                duration_ms=duration_ms,
                error_message=str(e)
            )
    
    async def _test_performance_benchmark(self) -> TraceTestResult:
        """Test performance benchmarks for tracing operations."""
        start_time = time.time()
        test_name = "performance_benchmark"
        
        try:
            tracer = get_tracer()
            spans = []
            span_creation_times = []
            
            # Benchmark span creation
            for i in range(100):
                span_start = time.time()
                
                with tracer.start_as_current_span(f"benchmark_span_{i}") as span:
                    span.set_attribute("benchmark.iteration", i)
                    spans.append(span)
                
                span_creation_times.append((time.time() - span_start) * 1000)
            
            # Calculate performance metrics
            avg_creation_time = sum(span_creation_times) / len(span_creation_times)
            max_creation_time = max(span_creation_times)
            min_creation_time = min(span_creation_times)
            p95_creation_time = sorted(span_creation_times)[int(len(span_creation_times) * 0.95)]
            
            duration_ms = (time.time() - start_time) * 1000
            
            # Determine test status based on performance thresholds
            performance_ok = (
                avg_creation_time < 1.0 and  # 1ms average
                p95_creation_time < 5.0 and  # 5ms P95
                duration_ms < self.config.performance_threshold_ms * 10  # 10x threshold for 100 spans
            )
            
            status = ValidationStatus.PASSED if performance_ok else ValidationStatus.WARNING
            
            return TraceTestResult(
                test_name=test_name,
                scenario=TestScenario.PERFORMANCE_BENCHMARK,
                status=status,
                duration_ms=duration_ms,
                metrics={
                    "spans_created": len(spans),
                    "avg_creation_time_ms": avg_creation_time,
                    "max_creation_time_ms": max_creation_time,
                    "min_creation_time_ms": min_creation_time,
                    "p95_creation_time_ms": p95_creation_time,
                    "performance_threshold_ms": self.config.performance_threshold_ms
                },
                spans_count=len(spans)
            )
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return TraceTestResult(
                test_name=test_name,
                scenario=TestScenario.PERFORMANCE_BENCHMARK,
                status=ValidationStatus.ERROR,
                duration_ms=duration_ms,
                error_message=str(e)
            )
    
    async def _test_sampling_validation(self) -> TraceTestResult:
        """Test trace sampling functionality."""
        start_time = time.time()
        test_name = "sampling_validation"
        
        try:
            if not self.config.sampling_validation_enabled:
                return TraceTestResult(
                    test_name=test_name,
                    scenario=TestScenario.SAMPLING_VALIDATION,
                    status=ValidationStatus.WARNING,
                    duration_ms=0,
                    metrics={"skipped": True, "reason": "Sampling validation disabled"}
                )
            
            tracer = get_tracer()
            sampling_stats = self.sampling_manager.get_sampling_stats()
            
            # Create test spans to validate sampling
            total_spans = 100
            sampled_spans = 0
            
            for i in range(total_spans):
                with tracer.start_as_current_span(f"sampling_test_span_{i}") as span:
                    # Check if span was sampled
                    if span.context.trace_flags.sampled:
                        sampled_spans += 1
            
            # Calculate sampling rate
            actual_sampling_rate = sampled_spans / total_spans
            expected_sampling_rate = sampling_stats.get("sampling_rate", 1.0)
            
            # Validate sampling rate (allow 10% tolerance)
            sampling_rate_ok = abs(actual_sampling_rate - expected_sampling_rate) < 0.1
            
            duration_ms = (time.time() - start_time) * 1000
            
            # Determine test status
            if sampling_rate_ok:
                status = ValidationStatus.PASSED
            else:
                status = ValidationStatus.WARNING
            
            return TraceTestResult(
                test_name=test_name,
                scenario=TestScenario.SAMPLING_VALIDATION,
                status=status,
                duration_ms=duration_ms,
                metrics={
                    "total_spans": total_spans,
                    "sampled_spans": sampled_spans,
                    "actual_sampling_rate": actual_sampling_rate,
                    "expected_sampling_rate": expected_sampling_rate,
                    "sampling_rate_ok": sampling_rate_ok
                }
            )
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return TraceTestResult(
                test_name=test_name,
                scenario=TestScenario.SAMPLING_VALIDATION,
                status=ValidationStatus.ERROR,
                duration_ms=duration_ms,
                error_message=str(e)
            )
    
    async def _test_exporter_reliability(self) -> TraceTestResult:
        """Test trace exporter reliability and performance."""
        start_time = time.time()
        test_name = "exporter_reliability"
        
        try:
            if not self.config.exporter_validation_enabled:
                return TraceTestResult(
                    test_name=test_name,
                    scenario=TestScenario.EXPORTER_RELIABILITY,
                    status=ValidationStatus.WARNING,
                    duration_ms=0,
                    metrics={"skipped": True, "reason": "Exporter validation disabled"}
                )
            
            # Get exporter status
            exporter_status = self.exporter_manager.get_all_exporter_status()
            
            # Create test spans and verify export
            tracer = get_tracer()
            test_trace_id = None
            
            with tracer.start_as_current_span("exporter_test_span") as span:
                test_trace_id = span.context.trace_id
                span.set_attribute("exporter.test", True)
            
            # Check exporter health
            healthy_exporters = sum(
                1 for status in exporter_status.values() 
                if status.get("status") == "healthy"
            )
            total_exporters = len(exporter_status)
            
            # Simulate export verification (in real implementation, this would query the backend)
            export_success = healthy_exporters > 0
            
            duration_ms = (time.time() - start_time) * 1000
            
            # Determine test status
            if export_success and healthy_exporters == total_exporters:
                status = ValidationStatus.PASSED
            elif export_success:
                status = ValidationStatus.WARNING
            else:
                status = ValidationStatus.FAILED
            
            return TraceTestResult(
                test_name=test_name,
                scenario=TestScenario.EXPORTER_RELIABILITY,
                status=status,
                duration_ms=duration_ms,
                metrics={
                    "total_exporters": total_exporters,
                    "healthy_exporters": healthy_exporters,
                    "export_success": export_success,
                    "test_trace_id": f"{test_trace_id:032x}" if test_trace_id else None
                }
            )
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return TraceTestResult(
                test_name=test_name,
                scenario=TestScenario.EXPORTER_RELIABILITY,
                status=ValidationStatus.ERROR,
                duration_ms=duration_ms,
                error_message=str(e)
            )
    
    async def _test_recovery_testing(self) -> TraceTestResult:
        """Test tracing system recovery from failures."""
        start_time = time.time()
        test_name = "recovery_testing"
        
        try:
            if not self.config.error_injection_enabled:
                return TraceTestResult(
                    test_name=test_name,
                    scenario=TestScenario.RECOVERY_TESTING,
                    status=ValidationStatus.WARNING,
                    duration_ms=0,
                    metrics={"skipped": True, "reason": "Error injection disabled"}
                )
            
            tracer = get_tracer()
            recovery_tests = []
            
            # Test 1: Tracer recovery after configuration reset
            try:
                # Simulate configuration reset
                original_config = self.tracing_config.config
                self.tracing_config.config = self.tracing_config._get_default_config()
                
                # Test tracer still works
                with tracer.start_as_current_span("recovery_test_1") as span:
                    span.set_attribute("recovery.test", "config_reset")
                
                # Restore configuration
                self.tracing_config.config = original_config
                
                recovery_tests.append({"test": "config_reset", "success": True})
            except Exception as e:
                recovery_tests.append({"test": "config_reset", "success": False, "error": str(e)})
            
            # Test 2: Recovery after exporter failure
            try:
                # Simulate exporter failure
                exporter_status_before = self.exporter_manager.get_all_exporter_status()
                
                # Test tracing still works
                with tracer.start_as_current_span("recovery_test_2") as span:
                    span.set_attribute("recovery.test", "exporter_failure")
                
                exporter_status_after = self.exporter_manager.get_all_exporter_status()
                
                recovery_tests.append({
                    "test": "exporter_failure", 
                    "success": True,
                    "exporter_status_before": exporter_status_before,
                    "exporter_status_after": exporter_status_after
                })
            except Exception as e:
                recovery_tests.append({"test": "exporter_failure", "success": False, "error": str(e)})
            
            # Calculate recovery success rate
            successful_recoveries = sum(1 for test in recovery_tests if test["success"])
            total_recovery_tests = len(recovery_tests)
            recovery_success_rate = successful_recoveries / total_recovery_tests if total_recovery_tests > 0 else 0
            
            duration_ms = (time.time() - start_time) * 1000
            
            # Determine test status
            if recovery_success_rate >= 0.8:  # 80% success rate threshold
                status = ValidationStatus.PASSED
            elif recovery_success_rate >= 0.5:  # 50% success rate threshold
                status = ValidationStatus.WARNING
            else:
                status = ValidationStatus.FAILED
            
            return TraceTestResult(
                test_name=test_name,
                scenario=TestScenario.RECOVERY_TESTING,
                status=status,
                duration_ms=duration_ms,
                metrics={
                    "recovery_tests": total_recovery_tests,
                    "successful_recoveries": successful_recoveries,
                    "recovery_success_rate": recovery_success_rate,
                    "recovery_test_details": recovery_tests
                }
            )
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return TraceTestResult(
                test_name=test_name,
                scenario=TestScenario.RECOVERY_TESTING,
                status=ValidationStatus.ERROR,
                duration_ms=duration_ms,
                error_message=str(e)
            )
    
    def _generate_performance_summary(self) -> Dict[str, Any]:
        """Generate performance summary from test results."""
        if not self.test_results:
            return {}
        
        performance_data = {
            "total_tests": len(self.test_results),
            "avg_duration_ms": sum(r.duration_ms for r in self.test_results) / len(self.test_results),
            "max_duration_ms": max(r.duration_ms for r in self.test_results),
            "min_duration_ms": min(r.duration_ms for r in self.test_results),
            "total_spans_created": sum(r.spans_count for r in self.test_results),
            "tests_by_status": {}
        }
        
        # Group tests by status
        for status in ValidationStatus:
            performance_data["tests_by_status"][status.value] = [
                r for r in self.test_results if r.status == status
            ]
        
        return performance_data
    
    def _generate_validation_summary(self) -> Dict[str, Any]:
        """Generate validation summary from test results."""
        validation_summary = {
            "total_validation_errors": 0,
            "validation_error_types": {},
            "test_scenarios_status": {}
        }
        
        # Count validation errors
        for result in self.test_results:
            if result.error_message:
                validation_summary["total_validation_errors"] += 1
                error_type = type(result.error_message).__name__
                validation_summary["validation_error_types"][error_type] = \
                    validation_summary["validation_error_types"].get(error_type, 0) + 1
        
        # Group by scenario
        for scenario in TestScenario:
            scenario_results = [r for r in self.test_results if r.scenario == scenario]
            if scenario_results:
                validation_summary["test_scenarios_status"][scenario.value] = {
                    "total": len(scenario_results),
                    "passed": sum(1 for r in scenario_results if r.status == ValidationStatus.PASSED),
                    "failed": sum(1 for r in scenario_results if r.status == ValidationStatus.FAILED),
                    "warning": sum(1 for r in scenario_results if r.status == ValidationStatus.WARNING),
                    "error": sum(1 for r in scenario_results if r.status == ValidationStatus.ERROR)
                }
        
        return validation_summary
    
    def _generate_recommendations(self, results: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on test results."""
        recommendations = []
        
        # Performance recommendations
        if results["summary"]["failed"] > 0:
            recommendations.append("Investigate failed tests and fix underlying issues")
        
        if results["summary"]["warning"] > 0:
            recommendations.append("Review warnings and consider optimizations")
        
        # Check for specific patterns
        for test_name, test_result in results["tests"].items():
            if isinstance(test_result, TraceTestResult):
                if test_result.status == ValidationStatus.FAILED:
                    if "performance" in test_name:
                        recommendations.append(f"Optimize performance for {test_name}")
                    elif "exporter" in test_name:
                        recommendations.append(f"Check exporter configuration and connectivity for {test_name}")
                    elif "sampling" in test_name:
                        recommendations.append(f"Review sampling configuration for {test_name}")
        
        # General recommendations
        if results["summary"]["error"] > 0:
            recommendations.append("Address errors in testing framework configuration")
        
        if not recommendations:
            recommendations.append("All tests passed - consider increasing test coverage or performance thresholds")
        
        return recommendations
    
    def get_test_results(self) -> List[TraceTestResult]:
        """Get all test results."""
        return self.test_results
    
    def get_test_results_by_scenario(self, scenario: TestScenario) -> List[TraceTestResult]:
        """Get test results for a specific scenario."""
        return [r for r in self.test_results if r.scenario == scenario]
    
    def clear_test_results(self) -> None:
        """Clear all test results."""
        self.test_results.clear()
    
    def export_test_results(self, format: str = "json") -> str:
        """Export test results in specified format."""
        if format.lower() == "json":
            return json.dumps([
                {
                    "test_name": r.test_name,
                    "scenario": r.scenario.value,
                    "status": r.status.value,
                    "duration_ms": r.duration_ms,
                    "metrics": r.metrics,
                    "error_message": r.error_message,
                    "timestamp": r.timestamp
                }
                for r in self.test_results
            ], indent=2)
        else:
            raise ValueError(f"Unsupported export format: {format}")


# Global instance
_trace_testing_manager = None


def get_trace_testing_manager(config: TraceTestConfig = None) -> TraceTestingManager:
    """Get the global trace testing manager instance."""
    global _trace_testing_manager
    if _trace_testing_manager is None:
        _trace_testing_manager = TraceTestingManager(config)
    return _trace_testing_manager


async def run_trace_tests() -> Dict[str, Any]:
    """Run all trace tests using the global manager."""
    manager = get_trace_testing_manager()
    return await manager.run_all_tests()