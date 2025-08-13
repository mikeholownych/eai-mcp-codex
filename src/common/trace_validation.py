"""
Trace validation utilities for MCP services.
Provides validation, health checks, and integration testing for distributed tracing.
"""

import logging
from typing import Dict, Any, List
import time
import re
from dataclasses import dataclass
from enum import Enum
from collections import defaultdict

from opentelemetry.trace import (
    Span, 
    Status, 
    StatusCode
)
from opentelemetry.trace.span import Span

from .tracing import get_tracing_config
from .trace_sampling import get_trace_sampling_manager
import os
from .trace_exporters import get_trace_exporter_manager

logger = logging.getLogger(__name__)


class ValidationLevel(Enum):
    """Validation level enumeration."""
    BASIC = "basic"
    STRICT = "strict"
    COMPREHENSIVE = "comprehensive"


class ValidationStatus(Enum):
    """Validation status enumeration."""
    PASSED = "passed"
    WARNING = "warning"
    FAILED = "failed"
    ERROR = "error"


@dataclass
class ValidationResult:
    """Result of a validation check."""
    name: str
    status: ValidationStatus
    message: str
    details: Dict[str, Any] = None
    timestamp: float = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()
        if self.details is None:
            self.details = {}


@dataclass
class TraceValidationReport:
    """Report containing all validation results."""
    trace_id: str
    validation_level: ValidationLevel
    results: List[ValidationResult]
    overall_status: ValidationStatus
    timestamp: float = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()
        
        # Calculate overall status
        if self.results:
            if any(r.status == ValidationStatus.ERROR for r in self.results):
                self.overall_status = ValidationStatus.ERROR
            elif any(r.status == ValidationStatus.FAILED for r in self.results):
                self.overall_status = ValidationStatus.FAILED
            elif any(r.status == ValidationStatus.WARNING for r in self.results):
                self.overall_status = ValidationStatus.WARNING
            else:
                self.overall_status = ValidationStatus.PASSED
        else:
            self.overall_status = ValidationStatus.ERROR


class TraceValidator:
    """Validator for trace data and spans."""
    
    def __init__(self):
        """Initialize trace validator."""
        self.tracing_config = get_tracing_config()
        self.sampling_manager = get_trace_sampling_manager()
        if os.getenv("TESTING_MODE", "").lower() == "true":
            self.exporter_manager = None
        else:
            self.exporter_manager = get_trace_exporter_manager()
        
        # Validation rules
        self.required_attributes = {
            "service.name": str,
            "service.version": str,
            "deployment.environment": str,
        }
        
        self.recommended_attributes = {
            "service.instance.id": str,
            "host.name": str,
            "host.arch": str,
            "os.type": str,
            "os.version": str,
            "process.pid": int,
            "process.command": str,
        }
        
        self.sensitive_patterns = [
            r'\bpassword\s*[:=]\s*[^\s]+',
            r'\btoken\s*[:=]\s*[^\s]+',
            r'\bapi[_-]?key\s*[:=]\s*[^\s]+',
            r'\bsecret\s*[:=]\s*[^\s]+',
            r'\bauthorization\s*[:=]\s*[^\s]+',
            r'\bemail\s*[:=]\s*[^\s]+@[^\s]+',
        ]
        
        self.span_name_patterns = {
            r'llm\..*': "LLM operations should follow naming convention",
            r'database\..*': "Database operations should follow naming convention",
            r'http\..*': "HTTP operations should follow naming convention",
            r'message_queue\..*': "Message queue operations should follow naming convention",
            r'service_communication\..*': "Service communication should follow naming convention",
        }
    
    def validate_trace(self, spans: List[Span], level: ValidationLevel = ValidationLevel.BASIC) -> TraceValidationReport:
        """
        Validate a complete trace.
        
        Args:
            spans: List of spans in the trace
            level: Validation level
            
        Returns:
            TraceValidationReport with validation results
        """
        if not spans:
            return TraceValidationReport(
                trace_id="unknown",
                validation_level=level,
                results=[ValidationResult(
                    name="trace_spans",
                    status=ValidationStatus.ERROR,
                    message="No spans found in trace"
                )],
                overall_status=ValidationStatus.ERROR
            )
        
        trace_id = spans[0].context.trace_id
        results = []
        
        # Basic validation
        if level in [ValidationLevel.BASIC, ValidationLevel.STRICT, ValidationLevel.COMPREHENSIVE]:
            results.extend(self._validate_basic_trace_structure(spans))
        
        # Strict validation
        if level in [ValidationLevel.STRICT, ValidationLevel.COMPREHENSIVE]:
            results.extend(self._validate_strict_trace_structure(spans))
        
        # Comprehensive validation
        if level == ValidationLevel.COMPREHENSIVE:
            results.extend(self._validate_comprehensive_trace_structure(spans))
        
        return TraceValidationReport(
            trace_id=trace_id,
            validation_level=level,
            results=results,
            overall_status=ValidationStatus.PASSED  # Will be calculated in __post_init__
        )
    
    def _validate_basic_trace_structure(self, spans: List[Span]) -> List[ValidationResult]:
        """Validate basic trace structure."""
        results = []
        
        # Check if trace has at least one span
        if not spans:
            results.append(ValidationResult(
                name="trace_spans",
                status=ValidationStatus.ERROR,
                message="No spans found in trace"
            ))
            return results
        
        # Check if all spans have the same trace ID
        trace_ids = {span.context.trace_id for span in spans}
        if len(trace_ids) > 1:
            results.append(ValidationResult(
                name="trace_id_consistency",
                status=ValidationStatus.ERROR,
                message="Spans have inconsistent trace IDs",
                details={"trace_ids": len(trace_ids)}
            ))
        
        # Check if spans have valid context
        for span in spans:
            if not span.context or not span.context.trace_id:
                results.append(ValidationResult(
                    name="span_context",
                    status=ValidationStatus.ERROR,
                    message=f"Span {span.name} has invalid context",
                    details={"span_name": span.name}
                ))
        
        # Check for required attributes
        service_names = set()
        for span in spans:
            service_name = span.attributes.get("service.name")
            if service_name:
                service_names.add(service_name)
            else:
                results.append(ValidationResult(
                    name="required_attributes",
                    status=ValidationStatus.WARNING,
                    message=f"Span {span.name} missing required attribute: service.name",
                    details={"span_name": span.name}
                ))
        
        # Check if trace spans are from the same service
        if len(service_names) > 1:
            results.append(ValidationResult(
                name="service_consistency",
                status=ValidationStatus.WARNING,
                message="Trace contains spans from multiple services",
                details={"service_count": len(service_names), "services": list(service_names)}
            ))
        
        return results
    
    def _validate_strict_trace_structure(self, spans: List[Span]) -> List[ValidationResult]:
        """Validate strict trace structure."""
        results = []
        
        # Check span hierarchy
        root_spans = [span for span in spans if span.parent is None]
        if len(root_spans) != 1:
            results.append(ValidationResult(
                name="span_hierarchy",
                status=ValidationStatus.WARNING,
                message=f"Expected exactly 1 root span, found {len(root_spans)}",
                details={"root_spans": len(root_spans)}
            ))
        
        # Check span timing
        for span in spans:
            if span.start_time and span.end_time:
                duration = span.end_time - span.start_time
                if duration < 0:
                    results.append(ValidationResult(
                        name="span_timing",
                        status=ValidationStatus.ERROR,
                        message=f"Span {span.name} has negative duration",
                        details={"span_name": span.name, "duration": duration}
                    ))
                elif duration > 3600 * 1000000000:  # 1 hour in nanoseconds
                    results.append(ValidationResult(
                        name="span_timing",
                        status=ValidationStatus.WARNING,
                        message=f"Span {span.name} has very long duration",
                        details={"span_name": span.name, "duration": duration}
                    ))
        
        # Check span names
        for span in spans:
            name_valid = False
            for pattern, description in self.span_name_patterns.items():
                if re.match(pattern, span.name):
                    name_valid = True
                    break
            
            if not name_valid:
                results.append(ValidationResult(
                    name="span_naming",
                    status=ValidationStatus.WARNING,
                    message=f"Span {span.name} does not follow naming convention",
                    details={"span_name": span.name}
                ))
        
        # Check for sensitive data
        for span in spans:
            sensitive_data_found = self._check_sensitive_data(span.attributes)
            if sensitive_data_found:
                results.append(ValidationResult(
                    name="sensitive_data",
                    status=ValidationStatus.WARNING,
                    message=f"Span {span.name} may contain sensitive data",
                    details={"span_name": span.name, "sensitive_fields": sensitive_data_found}
                ))
        
        return results
    
    def _validate_comprehensive_trace_structure(self, spans: List[Span]) -> List[ValidationResult]:
        """Validate comprehensive trace structure."""
        results = []
        
        # Check span relationships
        span_relationships = defaultdict(list)
        for span in spans:
            if span.parent:
                span_relationships[span.parent.span_id].append(span.context.span_id)
        
        # Check for orphan spans
        all_span_ids = {span.context.span_id for span in spans}
        for span in spans:
            if span.parent and span.parent.span_id not in all_span_ids:
                results.append(ValidationResult(
                    name="span_relationships",
                    status=ValidationStatus.WARNING,
                    message=f"Span {span.name} references non-existent parent",
                    details={"span_name": span.name, "parent_span_id": span.parent.span_id}
                ))
        
        # Check for circular references
        if self._has_circular_references(spans):
            results.append(ValidationResult(
                name="span_relationships",
                status=ValidationStatus.ERROR,
                message="Trace contains circular references in span hierarchy"
            ))
        
        # Check span status codes
        for span in spans:
            if span.status and span.status.status_code == StatusCode.ERROR:
                results.append(ValidationResult(
                    name="span_status",
                    status=ValidationStatus.WARNING,
                    message=f"Span {span.name} has error status",
                    details={"span_name": span.name, "status": span.status.description}
                ))
        
        # Check for recommended attributes
        for span in spans:
            missing_recommended = []
            for attr, attr_type in self.recommended_attributes.items():
                if attr not in span.attributes:
                    missing_recommended.append(attr)
                elif not isinstance(span.attributes[attr], attr_type):
                    missing_recommended.append(f"{attr} (type mismatch)")
            
            if missing_recommended:
                results.append(ValidationResult(
                    name="recommended_attributes",
                    status=ValidationStatus.WARNING,
                    message=f"Span {span.name} missing recommended attributes",
                    details={"span_name": span.name, "missing_attributes": missing_recommended}
                ))
        
        # Check span events
        for span in spans:
            if hasattr(span, 'events') and span.events:
                for event in span.events:
                    if not event.name:
                        results.append(ValidationResult(
                            name="span_events",
                            status=ValidationStatus.WARNING,
                            message=f"Span {span.name} has event without name",
                            details={"span_name": span.name}
                        ))
        
        return results
    
    def _check_sensitive_data(self, attributes: Dict[str, Any]) -> List[str]:
        """Check for sensitive data in attributes."""
        sensitive_fields = []
        
        for key, value in attributes.items():
            if isinstance(value, str):
                for pattern in self.sensitive_patterns:
                    if re.search(pattern, value, re.IGNORECASE):
                        sensitive_fields.append(key)
                        break
        
        return sensitive_fields
    
    def _has_circular_references(self, spans: List[Span]) -> bool:
        """Check if spans have circular references."""
        span_map = {span.context.span_id: span for span in spans}
        visited = set()
        
        def has_cycle(span_id: int, path: set) -> bool:
            if span_id in path:
                return True
            if span_id in visited:
                return False
            
            visited.add(span_id)
            path.add(span_id)
            
            span = span_map.get(span_id)
            if span and span.parent:
                if has_cycle(span.parent.span_id, path.copy()):
                    return True
            
            return False
        
        for span in spans:
            if has_cycle(span.context.span_id, set()):
                return True
        
        return False


class TraceHealthChecker:
    """Health checker for tracing system."""
    
    def __init__(self):
        """Initialize trace health checker."""
        self.tracing_config = get_tracing_config()
        self.exporter_manager = get_trace_exporter_manager()
        self.sampling_manager = get_trace_sampling_manager()
        
        # Health check thresholds
        self.max_export_queue_size = 1000
        self.max_export_duration = 30.0  # seconds
        self.min_sampling_rate = 0.01
        self.max_sampling_rate = 1.0
    
    def check_tracing_health(self) -> Dict[str, Any]:
        """
        Check the health of the entire tracing system.
        
        Returns:
            Health check results
        """
        health_results = {
            "overall_status": "healthy",
            "components": {},
            "timestamp": time.time()
        }
        
        # Check tracer provider
        tracer_health = self._check_tracer_health()
        health_results["components"]["tracer"] = tracer_health
        
        # Check exporters
        exporter_health = self._check_exporter_health()
        health_results["components"]["exporters"] = exporter_health
        
        # Check sampling
        sampling_health = self._check_sampling_health()
        health_results["components"]["sampling"] = sampling_health
        
        # Check metrics
        metrics_health = self._check_metrics_health()
        health_results["components"]["metrics"] = metrics_health
        
        # Determine overall status
        component_statuses = [
            component.get("status", "unknown")
            for component in health_results["components"].values()
        ]
        
        if "unhealthy" in component_statuses:
            health_results["overall_status"] = "unhealthy"
        elif "degraded" in component_statuses:
            health_results["overall_status"] = "degraded"
        
        return health_results
    
    def _check_tracer_health(self) -> Dict[str, Any]:
        """Check tracer health."""
        try:
            tracer = self.tracing_config.get_tracer()
            
            # Create a test span
            with tracer.start_as_current_span("health_check") as span:
                span.set_attribute("health_check", True)
                span.set_status(Status(StatusCode.OK))
            
            return {
                "status": "healthy",
                "message": "Tracer is functioning normally",
                "timestamp": time.time()
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "message": f"Tracer health check failed: {str(e)}",
                "timestamp": time.time()
            }
    
    def _check_exporter_health(self) -> Dict[str, Any]:
        """Check exporter health."""
        exporter_status = self.exporter_manager.get_all_exporter_status()
        
        healthy_count = 0
        total_count = len(exporter_status)
        
        for exporter_name, status in exporter_status.items():
            if status.get("status") == "healthy":
                healthy_count += 1
        
        if total_count == 0:
            return {
                "status": "unhealthy",
                "message": "No exporters configured",
                "timestamp": time.time()
            }
        elif healthy_count == total_count:
            return {
                "status": "healthy",
                "message": f"All {total_count} exporters are healthy",
                "timestamp": time.time()
            }
        elif healthy_count > 0:
            return {
                "status": "degraded",
                "message": f"{healthy_count}/{total_count} exporters are healthy",
                "timestamp": time.time()
            }
        else:
            return {
                "status": "unhealthy",
                "message": f"No healthy exporters out of {total_count}",
                "timestamp": time.time()
            }
    
    def _check_sampling_health(self) -> Dict[str, Any]:
        """Check sampling health."""
        try:
            sampler = self.sampling_manager.get_adaptive_sampler()
            stats = self.sampling_manager.get_sampling_stats()
            
            # Check sampling rate
            current_tps = stats.get("current_tps", 0)
            target_tps = stats.get("target_tps", 10)
            max_tps = stats.get("max_tps", 100)
            
            if current_tps > max_tps:
                return {
                    "status": "degraded",
                    "message": f"Current TPS ({current_tps}) exceeds maximum TPS ({max_tps})",
                    "timestamp": time.time()
                }
            elif current_tps > target_tps:
                return {
                    "status": "degraded",
                    "message": f"Current TPS ({current_tps}) exceeds target TPS ({target_tps})",
                    "timestamp": time.time()
                }
            else:
                return {
                    "status": "healthy",
                    "message": f"Sampling is within normal parameters (TPS: {current_tps})",
                    "timestamp": time.time()
                }
        except Exception as e:
            return {
                "status": "unhealthy",
                "message": f"Sampling health check failed: {str(e)}",
                "timestamp": time.time()
            }
    
    def _check_metrics_health(self) -> Dict[str, Any]:
        """Check metrics health."""
        try:
            meter = self.tracing_config.get_meter()
            
            # Create a test metric
            counter = meter.create_counter("health_check_test")
            counter.add(1, {"test": True})
            
            return {
                "status": "healthy",
                "message": "Metrics collection is functioning normally",
                "timestamp": time.time()
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "message": f"Metrics health check failed: {str(e)}",
                "timestamp": time.time()
            }


class TraceIntegrationTester:
    """Integration tester for tracing system."""
    
    def __init__(self):
        """Initialize trace integration tester."""
        self.tracing_config = get_tracing_config()
        self.validator = TraceValidator()
        self.health_checker = TraceHealthChecker()
    
    async def run_integration_tests(self) -> Dict[str, Any]:
        """
        Run comprehensive integration tests for the tracing system.
        
        Returns:
            Test results
        """
        test_results = {
            "overall_status": "passed",
            "tests": {},
            "timestamp": time.time()
        }
        
        # Test basic span creation
        basic_test = await self._test_basic_span_creation()
        test_results["tests"]["basic_span_creation"] = basic_test
        
        # Test span hierarchy
        hierarchy_test = await self._test_span_hierarchy()
        test_results["tests"]["span_hierarchy"] = hierarchy_test
        
        # Test trace context propagation
        propagation_test = await self._test_trace_context_propagation()
        test_results["tests"]["trace_context_propagation"] = propagation_test
        
        # Test exporter functionality
        exporter_test = await self._test_exporter_functionality()
        test_results["tests"]["exporter_functionality"] = exporter_test
        
        # Test sampling functionality
        sampling_test = await self._test_sampling_functionality()
        test_results["tests"]["sampling_functionality"] = sampling_test
        
        # Test metrics collection
        metrics_test = await self._test_metrics_collection()
        test_results["tests"]["metrics_collection"] = metrics_test
        
        # Determine overall status
        test_statuses = [
            test.get("status", "unknown")
            for test in test_results["tests"].values()
        ]
        
        if "failed" in test_statuses:
            test_results["overall_status"] = "failed"
        elif "warning" in test_statuses:
            test_results["overall_status"] = "warning"
        
        return test_results
    
    async def _test_basic_span_creation(self) -> Dict[str, Any]:
        """Test basic span creation."""
        try:
            tracer = self.tracing_config.get_tracer()
            
            with tracer.start_as_current_span("test_span") as span:
                span.set_attribute("test.attribute", "test_value")
                span.set_status(Status(StatusCode.OK))
            
            return {
                "status": "passed",
                "message": "Basic span creation test passed",
                "timestamp": time.time()
            }
        except Exception as e:
            return {
                "status": "failed",
                "message": f"Basic span creation test failed: {str(e)}",
                "timestamp": time.time()
            }
    
    async def _test_span_hierarchy(self) -> Dict[str, Any]:
        """Test span hierarchy."""
        try:
            tracer = self.tracing_config.get_tracer()
            spans = []
            
            with tracer.start_as_current_span("parent_span") as parent_span:
                spans.append(parent_span)
                
                with tracer.start_as_current_span("child_span") as child_span:
                    spans.append(child_span)
                    
                    with tracer.start_as_current_span("grandchild_span") as grandchild_span:
                        spans.append(grandchild_span)
            
            # Validate hierarchy
            if len(spans) != 3:
                return {
                    "status": "failed",
                    "message": f"Expected 3 spans, got {len(spans)}",
                    "timestamp": time.time()
                }
            
            # Check parent-child relationships
            if spans[1].parent != spans[0].context:
                return {
                    "status": "failed",
                    "message": "Child span parent reference incorrect",
                    "timestamp": time.time()
                }
            
            if spans[2].parent != spans[1].context:
                return {
                    "status": "failed",
                    "message": "Grandchild span parent reference incorrect",
                    "timestamp": time.time()
                }
            
            return {
                "status": "passed",
                "message": "Span hierarchy test passed",
                "timestamp": time.time()
            }
        except Exception as e:
            return {
                "status": "failed",
                "message": f"Span hierarchy test failed: {str(e)}",
                "timestamp": time.time()
            }
    
    async def _test_trace_context_propagation(self) -> Dict[str, Any]:
        """Test trace context propagation."""
        try:
            tracer = self.tracing_config.get_tracer()
            
            # Create parent span
            with tracer.start_as_current_span("parent_span") as parent_span:
                parent_trace_id = parent_span.context.trace_id
                
                # Create child span in different context
                with tracer.start_as_current_span("child_span") as child_span:
                    child_trace_id = child_span.context.trace_id
                
                # Create another child span
                with tracer.start_as_current_span("child_span_2") as child_span_2:
                    child_trace_id_2 = child_span_2.context.trace_id
            
            # Check trace ID consistency
            if parent_trace_id != child_trace_id or parent_trace_id != child_trace_id_2:
                return {
                    "status": "failed",
                    "message": "Trace context propagation failed - trace IDs don't match",
                    "timestamp": time.time()
                }
            
            return {
                "status": "passed",
                "message": "Trace context propagation test passed",
                "timestamp": time.time()
            }
        except Exception as e:
            return {
                "status": "failed",
                "message": f"Trace context propagation test failed: {str(e)}",
                "timestamp": time.time()
            }
    
    async def _test_exporter_functionality(self) -> Dict[str, Any]:
        """Test exporter functionality."""
        try:
            # Check exporter health
            exporter_health = self.health_checker._check_exporter_health()
            
            if exporter_health["status"] == "unhealthy":
                return {
                    "status": "failed",
                    "message": "Exporter functionality test failed - exporters unhealthy",
                    "timestamp": time.time()
                }
            
            return {
                "status": "passed",
                "message": "Exporter functionality test passed",
                "timestamp": time.time()
            }
        except Exception as e:
            return {
                "status": "failed",
                "message": f"Exporter functionality test failed: {str(e)}",
                "timestamp": time.time()
            }
    
    async def _test_sampling_functionality(self) -> Dict[str, Any]:
        """Test sampling functionality."""
        try:
            # Check sampling health
            sampling_health = self.health_checker._check_sampling_health()
            
            if sampling_health["status"] == "unhealthy":
                return {
                    "status": "failed",
                    "message": "Sampling functionality test failed - sampling unhealthy",
                    "timestamp": time.time()
                }
            
            return {
                "status": "passed",
                "message": "Sampling functionality test passed",
                "timestamp": time.time()
            }
        except Exception as e:
            return {
                "status": "failed",
                "message": f"Sampling functionality test failed: {str(e)}",
                "timestamp": time.time()
            }
    
    async def _test_metrics_collection(self) -> Dict[str, Any]:
        """Test metrics collection."""
        try:
            # Check metrics health
            metrics_health = self.health_checker._check_metrics_health()
            
            if metrics_health["status"] == "unhealthy":
                return {
                    "status": "failed",
                    "message": "Metrics collection test failed - metrics unhealthy",
                    "timestamp": time.time()
                }
            
            return {
                "status": "passed",
                "message": "Metrics collection test passed",
                "timestamp": time.time()
            }
        except Exception as e:
            return {
                "status": "failed",
                "message": f"Metrics collection test failed: {str(e)}",
                "timestamp": time.time()
            }


# Global instances
trace_validator = TraceValidator()
trace_health_checker = TraceHealthChecker()
trace_integration_tester = TraceIntegrationTester()


def get_trace_validator() -> TraceValidator:
    """Get the global trace validator."""
    return trace_validator


def get_trace_health_checker() -> TraceHealthChecker:
    """Get the global trace health checker."""
    return trace_health_checker


def get_trace_integration_tester() -> TraceIntegrationTester:
    """Get the global trace integration tester."""
    return trace_integration_tester


def validate_trace(spans: List[Span], level: ValidationLevel = ValidationLevel.BASIC) -> TraceValidationReport:
    """Validate a trace."""
    return trace_validator.validate_trace(spans, level)


def check_tracing_health() -> Dict[str, Any]:
    """Check tracing system health."""
    return trace_health_checker.check_tracing_health()


async def run_trace_integration_tests() -> Dict[str, Any]:
    """Run trace integration tests."""
    return await trace_integration_tester.run_integration_tests()