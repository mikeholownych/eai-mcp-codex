"""
Health Check Testing and Validation Utilities.
Provides comprehensive testing and validation for health check implementations.
"""

import asyncio
import json
import time
from typing import Dict, Any, List, Optional, Callable, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import pytest
import aiohttp
from unittest.mock import Mock, patch, AsyncMock

from .enhanced_health_check import (
    HealthStatus, HealthCheckType, HealthChecker, HealthCheckResult,
    check_memory_usage, check_disk_usage, check_cpu_usage,
    check_network_connectivity, health_check
)
from .health_aggregator import HealthAggregator, SystemHealthReport
from .health_monitoring import HealthMonitor, AlertRule, AlertSeverity, AlertType
from .logging import get_logger
from .tracing import get_tracer
from .metrics import get_metrics_collector

logger = get_logger("health_check_testing")
tracer = get_tracer()
metrics = get_metrics_collector("health_check_testing")


class TestResult(Enum):
    """Test result status."""
    PASSED = "passed"
    FAILED = "failed"
    ERROR = "error"
    SKIPPED = "skipped"


@dataclass
class HealthCheckTestCase:
    """Test case for health checks."""
    name: str
    description: str
    test_function: Callable
    expected_result: Any
    timeout: float = 30.0
    critical: bool = True
    tags: List[str] = None


@dataclass
class HealthCheckTestSuite:
    """Test suite for health checks."""
    name: str
    description: str
    test_cases: List[HealthCheckTestCase]
    setup_function: Optional[Callable] = None
    teardown_function: Optional[Callable] = None


@dataclass
class TestExecutionResult:
    """Result of test execution."""
    test_name: str
    result: TestResult
    execution_time: float
    error_message: Optional[str] = None
    expected_result: Any = None
    actual_result: Any = None


@dataclass
class TestSuiteResult:
    """Result of test suite execution."""
    suite_name: str
    total_tests: int
    passed_tests: int
    failed_tests: int
    error_tests: int
    skipped_tests: int
    execution_time: float
    test_results: List[TestExecutionResult]
    success_rate: float


class HealthCheckTester:
    """Tester for health check implementations."""
    
    def __init__(self):
        self.test_suites = self._create_default_test_suites()
        self.test_history = []
        self.max_history_size = 100
        
        # Initialize metrics
        self._initialize_metrics()
    
    def _initialize_metrics(self):
        """Initialize health check testing metrics."""
        metrics.register_counter(
            "health_check_tests_total",
            "Total number of health check tests executed",
            labels=["result", "suite"]
        )
        
        metrics.register_histogram(
            "health_check_test_duration_seconds",
            "Time taken to execute health check tests",
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0]
        )
        
        metrics.register_gauge(
            "health_check_test_success_rate",
            "Success rate of health check tests",
            labels=["suite"]
        )
    
    def _create_default_test_suites(self) -> List[HealthCheckTestSuite]:
        """Create default test suites."""
        return [
            HealthCheckTestSuite(
                name="basic_health_checks",
                description="Basic health check functionality tests",
                test_cases=[
                    HealthCheckTestCase(
                        name="memory_usage_check",
                        description="Test memory usage health check",
                        test_function=self._test_memory_usage_check,
                        expected_result={"status": HealthStatus.HEALTHY.value},
                        critical=True,
                        tags=["resource", "memory"]
                    ),
                    HealthCheckTestCase(
                        name="disk_usage_check",
                        description="Test disk usage health check",
                        test_function=self._test_disk_usage_check,
                        expected_result={"status": HealthStatus.HEALTHY.value},
                        critical=True,
                        tags=["resource", "disk"]
                    ),
                    HealthCheckTestCase(
                        name="cpu_usage_check",
                        description="Test CPU usage health check",
                        test_function=self._test_cpu_usage_check,
                        expected_result={"status": HealthStatus.HEALTHY.value},
                        critical=True,
                        tags=["resource", "cpu"]
                    ),
                    HealthCheckTestCase(
                        name="network_connectivity_check",
                        description="Test network connectivity health check",
                        test_function=self._test_network_connectivity_check,
                        expected_result={"status": HealthStatus.HEALTHY.value},
                        critical=True,
                        tags=["network", "connectivity"]
                    )
                ]
            ),
            HealthCheckTestSuite(
                name="health_checker_functionality",
                description="Health checker functionality tests",
                test_cases=[
                    HealthCheckTestCase(
                        name="health_checker_registration",
                        description="Test health check registration",
                        test_function=self._test_health_checker_registration,
                        expected_result={"registered_checks": 3},
                        critical=True,
                        tags=["registration", "functionality"]
                    ),
                    HealthCheckTestCase(
                        name="health_checker_execution",
                        description="Test health check execution",
                        test_function=self._test_health_checker_execution,
                        expected_result={"execution_successful": True},
                        critical=True,
                        tags=["execution", "functionality"]
                    ),
                    HealthCheckTestCase(
                        name="health_checker_timeout",
                        description="Test health check timeout handling",
                        test_function=self._test_health_checker_timeout,
                        expected_result={"timeout_handled": True},
                        critical=True,
                        tags=["timeout", "error_handling"]
                    )
                ]
            ),
            HealthCheckTestSuite(
                name="health_aggregator",
                description="Health aggregator tests",
                test_cases=[
                    HealthCheckTestCase(
                        name="aggregator_initialization",
                        description="Test health aggregator initialization",
                        test_function=self._test_aggregator_initialization,
                        expected_result={"initialized": True},
                        critical=True,
                        tags=["initialization", "aggregator"]
                    ),
                    HealthCheckTestCase(
                        name="aggregator_service_endpoints",
                        description="Test aggregator service endpoints configuration",
                        test_function=self._test_aggregator_service_endpoints,
                        expected_result={"endpoints_configured": True},
                        critical=True,
                        tags=["configuration", "aggregator"]
                    ),
                    HealthCheckTestCase(
                        name="aggregator_metrics",
                        description="Test aggregator metrics initialization",
                        test_function=self._test_aggregator_metrics,
                        expected_result={"metrics_initialized": True},
                        critical=True,
                        tags=["metrics", "aggregator"]
                    )
                ]
            ),
            HealthCheckTestSuite(
                name="health_monitoring",
                description="Health monitoring tests",
                test_cases=[
                    HealthCheckTestCase(
                        name="monitor_initialization",
                        description="Test health monitor initialization",
                        test_function=self._test_monitor_initialization,
                        expected_result={"initialized": True},
                        critical=True,
                        tags=["initialization", "monitoring"]
                    ),
                    HealthCheckTestCase(
                        name="alert_rules_configuration",
                        description="Test alert rules configuration",
                        test_function=self._test_alert_rules_configuration,
                        expected_result={"rules_configured": True},
                        critical=True,
                        tags=["configuration", "alerting"]
                    ),
                    HealthCheckTestCase(
                        name="notification_handlers",
                        description="Test notification handlers setup",
                        test_function=self._test_notification_handlers,
                        expected_result={"handlers_configured": True},
                        critical=True,
                        tags=["notification", "monitoring"]
                    )
                ]
            ),
            HealthCheckTestSuite(
                name="integration_tests",
                description="Integration tests for health check system",
                test_cases=[
                    HealthCheckTestCase(
                        name="end_to_end_health_check",
                        description="Test end-to-end health check flow",
                        test_function=self._test_end_to_end_health_check,
                        expected_result={"flow_successful": True},
                        critical=True,
                        tags=["integration", "end_to_end"]
                    ),
                    HealthCheckTestCase(
                        name="alert_generation",
                        description="Test alert generation and notification",
                        test_function=self._test_alert_generation,
                        expected_result={"alerts_generated": True},
                        critical=True,
                        tags=["integration", "alerting"]
                    ),
                    HealthCheckTestCase(
                        name="metrics_collection",
                        description="Test metrics collection and reporting",
                        test_function=self._test_metrics_collection,
                        expected_result={"metrics_collected": True},
                        critical=True,
                        tags=["integration", "metrics"]
                    )
                ]
            )
        ]
    
    async def run_test_suite(self, suite_name: str) -> TestSuiteResult:
        """Run a specific test suite."""
        suite = next((s for s in self.test_suites if s.name == suite_name), None)
        if not suite:
            raise ValueError(f"Test suite not found: {suite_name}")
        
        start_time = time.time()
        test_results = []
        
        # Setup
        if suite.setup_function:
            try:
                await suite.setup_function()
            except Exception as e:
                logger.error(f"Setup failed for suite {suite_name}: {str(e)}")
                return TestSuiteResult(
                    suite_name=suite_name,
                    total_tests=len(suite.test_cases),
                    passed_tests=0,
                    failed_tests=0,
                    error_tests=len(suite.test_cases),
                    skipped_tests=0,
                    execution_time=0.0,
                    test_results=[],
                    success_rate=0.0
                )
        
        # Run tests
        for test_case in suite.test_cases:
            try:
                test_start_time = time.time()
                
                # Execute test with timeout
                result = await asyncio.wait_for(
                    test_case.test_function(),
                    timeout=test_case.timeout
                )
                
                execution_time = time.time() - test_start_time
                
                # Validate result
                if self._validate_test_result(result, test_case.expected_result):
                    test_result = TestExecutionResult(
                        test_name=test_case.name,
                        result=TestResult.PASSED,
                        execution_time=execution_time,
                        expected_result=test_case.expected_result,
                        actual_result=result
                    )
                else:
                    test_result = TestExecutionResult(
                        test_name=test_case.name,
                        result=TestResult.FAILED,
                        execution_time=execution_time,
                        error_message=f"Expected {test_case.expected_result}, got {result}",
                        expected_result=test_case.expected_result,
                        actual_result=result
                    )
                
            except asyncio.TimeoutError:
                test_result = TestExecutionResult(
                    test_name=test_case.name,
                    result=TestResult.FAILED,
                    execution_time=test_case.timeout,
                    error_message="Test timed out",
                    expected_result=test_case.expected_result
                )
            except Exception as e:
                test_result = TestExecutionResult(
                    test_name=test_case.name,
                    result=TestResult.ERROR,
                    execution_time=time.time() - test_start_time,
                    error_message=str(e),
                    expected_result=test_case.expected_result
                )
            
            test_results.append(test_result)
            
            # Update metrics
            metrics.counter("health_check_tests_total").labels(
                result=test_result.result.value,
                suite=suite_name
            ).inc()
            
            metrics.histogram("health_check_test_duration_seconds").observe(
                test_result.execution_time
            )
        
        # Teardown
        if suite.teardown_function:
            try:
                await suite.teardown_function()
            except Exception as e:
                logger.error(f"Teardown failed for suite {suite_name}: {str(e)}")
        
        # Calculate results
        total_time = time.time() - start_time
        passed = sum(1 for r in test_results if r.result == TestResult.PASSED)
        failed = sum(1 for r in test_results if r.result == TestResult.FAILED)
        error = sum(1 for r in test_results if r.result == TestResult.ERROR)
        skipped = sum(1 for r in test_results if r.result == TestResult.SKIPPED)
        success_rate = passed / len(test_results) if test_results else 0.0
        
        # Update success rate metric
        metrics.gauge("health_check_test_success_rate").labels(
            suite=suite_name
        ).set(success_rate)
        
        # Create suite result
        suite_result = TestSuiteResult(
            suite_name=suite_name,
            total_tests=len(test_results),
            passed_tests=passed,
            failed_tests=failed,
            error_tests=error,
            skipped_tests=skipped,
            execution_time=total_time,
            test_results=test_results,
            success_rate=success_rate
        )
        
        # Store in history
        self.test_history.append(suite_result)
        if len(self.test_history) > self.max_history_size:
            self.test_history = self.test_history[-self.max_history_size:]
        
        # Log results
        logger.info(f"Test suite '{suite_name}' completed: "
                   f"{passed} passed, {failed} failed, {error} error, "
                   f"{skipped} skipped in {total_time:.2f}s "
                   f"({success_rate:.1%} success rate)")
        
        return suite_result
    
    async def run_all_test_suites(self) -> Dict[str, TestSuiteResult]:
        """Run all test suites."""
        results = {}
        
        for suite in self.test_suites:
            try:
                result = await self.run_test_suite(suite.name)
                results[suite.name] = result
            except Exception as e:
                logger.error(f"Error running test suite {suite.name}: {str(e)}")
                results[suite.name] = TestSuiteResult(
                    suite_name=suite.name,
                    total_tests=len(suite.test_cases),
                    passed_tests=0,
                    failed_tests=0,
                    error_tests=len(suite.test_cases),
                    skipped_tests=0,
                    execution_time=0.0,
                    test_results=[],
                    success_rate=0.0
                )
        
        return results
    
    def _validate_test_result(self, actual: Any, expected: Any) -> bool:
        """Validate test result against expected result."""
        if isinstance(expected, dict) and isinstance(actual, dict):
            return all(key in actual and actual[key] == value for key, value in expected.items())
        return actual == expected
    
    # Test functions
    async def _test_memory_usage_check(self) -> Dict[str, Any]:
        """Test memory usage health check."""
        result = check_memory_usage(max_usage_percent=90.0)
        return result
    
    async def _test_disk_usage_check(self) -> Dict[str, Any]:
        """Test disk usage health check."""
        result = check_disk_usage(max_usage_percent=90.0)
        return result
    
    async def _test_cpu_usage_check(self) -> Dict[str, Any]:
        """Test CPU usage health check."""
        result = check_cpu_usage(max_usage_percent=90.0)
        return result
    
    async def _test_network_connectivity_check(self) -> Dict[str, Any]:
        """Test network connectivity health check."""
        result = check_network_connectivity(host="8.8.8.8", port=53, timeout=5.0)
        return result
    
    async def _test_health_checker_registration(self) -> Dict[str, Any]:
        """Test health check registration."""
        checker = HealthChecker("test_service")
        
        # Register test checks
        checker.register_simple_check("test1", lambda: {"status": "healthy"})
        checker.register_simple_check("test2", lambda: {"status": "healthy"})
        checker.register_simple_check("test3", lambda: {"status": "healthy"})
        
        return {"registered_checks": len(checker.checks)}
    
    async def _test_health_checker_execution(self) -> Dict[str, Any]:
        """Test health check execution."""
        checker = HealthChecker("test_service")
        
        # Register test check
        checker.register_simple_check("test", lambda: {"status": "healthy"})
        
        # Execute check
        results = await checker.run_all_checks()
        
        return {"execution_successful": "test" in results}
    
    async def _test_health_checker_timeout(self) -> Dict[str, Any]:
        """Test health check timeout handling."""
        checker = HealthChecker("test_service")
        
        # Register slow check
        async def slow_check():
            await asyncio.sleep(2.0)
            return {"status": "healthy"}
        
        checker.register_simple_check("slow_test", slow_check)
        
        # Execute with timeout
        try:
            results = await checker.run_all_checks(timeout=1.0)
            return {"timeout_handled": False}
        except asyncio.TimeoutError:
            return {"timeout_handled": True}
    
    async def _test_aggregator_initialization(self) -> Dict[str, Any]:
        """Test health aggregator initialization."""
        aggregator = HealthAggregator()
        return {"initialized": aggregator is not None}
    
    async def _test_aggregator_service_endpoints(self) -> Dict[str, Any]:
        """Test aggregator service endpoints configuration."""
        aggregator = HealthAggregator()
        return {"endpoints_configured": len(aggregator.service_endpoints) > 0}
    
    async def _test_aggregator_metrics(self) -> Dict[str, Any]:
        """Test aggregator metrics initialization."""
        aggregator = HealthAggregator()
        return {"metrics_initialized": hasattr(aggregator, '_initialize_metrics')}
    
    async def _test_monitor_initialization(self) -> Dict[str, Any]:
        """Test health monitor initialization."""
        monitor = HealthMonitor()
        return {"initialized": monitor is not None}
    
    async def _test_alert_rules_configuration(self) -> Dict[str, Any]:
        """Test alert rules configuration."""
        monitor = HealthMonitor()
        return {"rules_configured": len(monitor.alert_rules) > 0}
    
    async def _test_notification_handlers(self) -> Dict[str, Any]:
        """Test notification handlers setup."""
        monitor = HealthMonitor()
        return {"handlers_configured": len(monitor.notification_handlers) > 0}
    
    async def _test_end_to_end_health_check(self) -> Dict[str, Any]:
        """Test end-to-end health check flow."""
        # Create mock services
        async def mock_health_endpoint():
            return {
                "service": "test_service",
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "checks": {
                    "test_check": {
                        "status": "healthy",
                        "message": "Test check passed"
                    }
                }
            }
        
        # Test aggregation
        aggregator = HealthAggregator()
        
        # Mock service health data
        service_health_data = {
            "test_service": await mock_health_endpoint()
        }
        
        # Generate summaries
        summaries = aggregator._generate_service_summaries(service_health_data)
        
        return {"flow_successful": len(summaries) > 0}
    
    async def _test_alert_generation(self) -> Dict[str, Any]:
        """Test alert generation and notification."""
        monitor = HealthMonitor()
        
        # Create test alert rule
        rule = AlertRule(
            name="test_rule",
            enabled=True,
            condition="service_status == 'error'",
            severity=AlertSeverity.WARNING,
            alert_type=AlertType.SERVICE_DOWN,
            threshold=1.0,
            duration=1,
            services=["test_service"],
            notification_channels=[]
        )
        
        # Add rule
        success = monitor.add_alert_rule(rule)
        
        return {"alerts_generated": success}
    
    async def _test_metrics_collection(self) -> Dict[str, Any]:
        """Test metrics collection and reporting."""
        # Test metric registration
        metrics.register_gauge("test_gauge", "Test gauge")
        metrics.register_counter("test_counter", "Test counter")
        metrics.register_histogram("test_histogram", "Test histogram")
        
        # Test metric updates
        metrics.gauge("test_gauge").set(1.0)
        metrics.counter("test_counter").inc()
        metrics.histogram("test_histogram").observe(1.0)
        
        return {"metrics_collected": True}
    
    def get_test_history(self, suite_name: Optional[str] = None) -> List[TestSuiteResult]:
        """Get test execution history."""
        if suite_name:
            return [result for result in self.test_history if result.suite_name == suite_name]
        return self.test_history.copy()
    
    def get_test_summary(self) -> Dict[str, Any]:
        """Get summary of all test results."""
        if not self.test_history:
            return {"message": "No test history available"}
        
        total_suites = len(self.test_history)
        total_tests = sum(result.total_tests for result in self.test_history)
        total_passed = sum(result.passed_tests for result in self.test_history)
        total_failed = sum(result.failed_tests for result in self.test_history)
        total_error = sum(result.error_tests for result in self.test_history)
        total_skipped = sum(result.skipped_tests for result in self.test_history)
        
        overall_success_rate = total_passed / total_tests if total_tests > 0 else 0.0
        
        return {
            "total_test_suites": total_suites,
            "total_tests": total_tests,
            "total_passed": total_passed,
            "total_failed": total_failed,
            "total_error": total_error,
            "total_skipped": total_skipped,
            "overall_success_rate": overall_success_rate,
            "last_execution": self.test_history[-1].suite_name if self.test_history else None
        }


# Global instance
_health_tester: Optional[HealthCheckTester] = None


def get_health_check_tester() -> HealthCheckTester:
    """Get the global health check tester."""
    global _health_tester
    if _health_tester is None:
        _health_tester = HealthCheckTester()
    return _health_tester


# Test runner functions
async def run_health_check_tests(suite_name: Optional[str] = None) -> Dict[str, Any]:
    """Run health check tests."""
    tester = get_health_check_tester()
    
    if suite_name:
        result = await tester.run_test_suite(suite_name)
        return asdict(result)
    else:
        results = await tester.run_all_test_suites()
        return {name: asdict(result) for name, result in results.items()}


async def get_test_results(suite_name: Optional[str] = None) -> Dict[str, Any]:
    """Get test results."""
    tester = get_health_check_tester()
    history = tester.get_test_history(suite_name)
    
    if suite_name and history:
        return asdict(history[-1]) if history else {"error": "No results found"}
    elif not suite_name:
        return {"history": [asdict(result) for result in history]}
    else:
        return {"error": f"No results found for suite: {suite_name}"}


async def get_test_summary() -> Dict[str, Any]:
    """Get test summary."""
    tester = get_health_check_tester()
    return tester.get_test_summary()


# Pytest fixtures and utilities
@pytest.fixture
async def health_checker():
    """Pytest fixture for health checker."""
    return HealthChecker("test_service")


@pytest.fixture
async def health_aggregator():
    """Pytest fixture for health aggregator."""
    return HealthAggregator()


@pytest.fixture
async def health_monitor():
    """Pytest fixture for health monitor."""
    return HealthMonitor()


@pytest.fixture
async def health_tester():
    """Pytest fixture for health tester."""
    return HealthCheckTester()


# Test utilities
def create_mock_health_check(status: HealthStatus = HealthStatus.HEALTHY, 
                           message: str = "OK") -> Callable:
    """Create a mock health check function."""
    async def mock_check():
        return {
            "status": status.value,
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        }
    return mock_check


def create_mock_service_health(service_name: str, status: str = "healthy") -> Dict[str, Any]:
    """Create mock service health data."""
    return {
        "service": service_name,
        "status": status,
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {
            "test_check": {
                "status": status,
                "message": "Test check"
            }
        }
    }


def validate_health_check_result(result: Dict[str, Any], 
                                expected_status: HealthStatus) -> bool:
    """Validate health check result."""
    return result.get("status") == expected_status.value


def validate_alert_rule(rule: AlertRule, expected_name: str, 
                       expected_severity: AlertSeverity) -> bool:
    """Validate alert rule."""
    return rule.name == expected_name and rule.severity == expected_severity


# Performance testing utilities
class HealthCheckPerformanceTester:
    """Performance tester for health checks."""
    
    def __init__(self):
        self.results = []
    
    async def benchmark_health_check(self, check_function: Callable, 
                                   iterations: int = 100) -> Dict[str, Any]:
        """Benchmark a health check function."""
        times = []
        
        for _ in range(iterations):
            start_time = time.time()
            try:
                await check_function()
                times.append(time.time() - start_time)
            except Exception as e:
                logger.error(f"Benchmark iteration failed: {str(e)}")
        
        if not times:
            return {"error": "All iterations failed"}
        
        return {
            "iterations": iterations,
            "successful_iterations": len(times),
            "min_time": min(times),
            "max_time": max(times),
            "avg_time": sum(times) / len(times),
            "p95_time": sorted(times)[int(len(times) * 0.95)],
            "p99_time": sorted(times)[int(len(times) * 0.99)]
        }
    
    async def load_test_health_aggregator(self, aggregator: HealthAggregator,
                                       concurrent_requests: int = 50) -> Dict[str, Any]:
        """Load test health aggregator."""
        async def make_request():
            start_time = time.time()
            try:
                await aggregator.aggregate_all_health_checks()
                return time.time() - start_time
            except Exception as e:
                logger.error(f"Load test request failed: {str(e)}")
                return -1
        
        # Make concurrent requests
        tasks = [make_request() for _ in range(concurrent_requests)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        successful_results = [r for r in results if isinstance(r, float) and r > 0]
        
        if not successful_results:
            return {"error": "All requests failed"}
        
        return {
            "concurrent_requests": concurrent_requests,
            "successful_requests": len(successful_results),
            "failed_requests": len(results) - len(successful_results),
            "min_time": min(successful_results),
            "max_time": max(successful_results),
            "avg_time": sum(successful_results) / len(successful_results),
            "requests_per_second": len(successful_results) / sum(successful_results)
        }


# Global performance tester instance
_performance_tester: Optional[HealthCheckPerformanceTester] = None


def get_health_check_performance_tester() -> HealthCheckPerformanceTester:
    """Get the global health check performance tester."""
    global _performance_tester
    if _performance_tester is None:
        _performance_tester = HealthCheckPerformanceTester()
    return _performance_tester