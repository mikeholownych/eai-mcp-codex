"""
Verification Feedback service-specific tracing instrumentation.
Provides custom spans and metrics for code analysis, security scanning, and quality assessment.
"""

import logging
from typing import Dict, List
from contextlib import asynccontextmanager
import time

from opentelemetry.trace import Status, StatusCode, SpanKind
from src.common.tracing import (
    get_tracing_config,
    get_instrumentation_manager
)

logger = logging.getLogger(__name__)


class VerificationFeedbackTracing:
    """Tracing instrumentation specific to Verification Feedback operations."""
    
    def __init__(self):
        self.tracer = None
        self.meter = None
        self._initialize_metrics()
    
    def _initialize_metrics(self):
        """Initialize metrics for verification feedback operations."""
        config = get_tracing_config()
        self.tracer = config.get_tracer()
        self.meter = config.get_meter()
        
        # Create metrics
        self.verification_execution_counter = self.meter.create_counter(
            "verification_feedback_executions_total",
            description="Total number of verification executions"
        )
        
        self.verification_duration = self.meter.create_histogram(
            "verification_feedback_duration_seconds",
            description="Duration of verification operations"
        )
        
        self.feedback_submission_counter = self.meter.create_counter(
            "verification_feedback_submissions_total",
            description="Total number of feedback submissions"
        )
        
        self.feedback_processing_duration = self.meter.create_histogram(
            "verification_feedback_processing_duration_seconds",
            description="Duration of feedback processing operations"
        )
        
        self.security_scan_counter = self.meter.create_counter(
            "verification_feedback_security_scans_total",
            description="Total number of security scans"
        )
        
        self.security_issues_found = self.meter.create_counter(
            "verification_feedback_security_issues_total",
            description="Total number of security issues found"
        )
        
        self.quality_assessment_counter = self.meter.create_counter(
            "verification_feedback_quality_assessments_total",
            description="Total number of quality assessments"
        )
        
        self.quality_score_histogram = self.meter.create_histogram(
            "verification_feedback_quality_score",
            description="Quality assessment scores"
        )
        
        self.code_analysis_counter = self.meter.create_counter(
            "verification_feedback_code_analyses_total",
            description="Total number of code analyses"
        )
        
        self.verification_rules_counter = self.meter.create_counter(
            "verification_feedback_rules_applied_total",
            description="Total number of verification rules applied"
        )
        
        self.verification_error_counter = self.meter.create_counter(
            "verification_feedback_errors_total",
            description="Total number of verification errors"
        )
        
        self.feedback_auto_processing_counter = self.meter.create_counter(
            "verification_feedback_auto_processing_total",
            description="Total number of auto-processed feedback items"
        )
    
    @asynccontextmanager
    async def trace_verification_execution(self, verification_id: str, target_type: str, 
                                        target_id: str, rule_count: int = 0):
        """Trace verification execution process."""
        span_name = "verification_feedback.execute_verification"
        attributes = {
            "verification_feedback.verification_id": verification_id,
            "verification_feedback.target_type": target_type,
            "verification_feedback.target_id": target_id,
            "verification_feedback.rule_count": rule_count
        }
        
        with self.tracer.start_as_current_span(span_name, attributes=attributes) as span:
            start_time = time.time()
            try:
                yield span
                duration = time.time() - start_time
                self.verification_duration.record(duration, {"target_type": target_type})
                self.verification_execution_counter.add(1, {"target_type": target_type})
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                self.verification_error_counter.add(1, {
                    "operation": "verification_execution",
                    "error_type": type(e).__name__
                })
                raise
    
    @asynccontextmanager
    async def trace_code_analysis(self, verification_id: str, analysis_type: str, 
                                file_count: int = 0, line_count: int = 0):
        """Trace code analysis process."""
        span_name = "verification_feedback.code_analysis"
        attributes = {
            "verification_feedback.verification_id": verification_id,
            "verification_feedback.analysis_type": analysis_type,
            "verification_feedback.file_count": file_count,
            "verification_feedback.line_count": line_count
        }
        
        with self.tracer.start_as_current_span(span_name, attributes=attributes) as span:
            start_time = time.time()
            try:
                yield span
                duration = time.time() - start_time
                self.verification_duration.record(duration, {"operation": "code_analysis"})
                self.code_analysis_counter.add(1, {"analysis_type": analysis_type})
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                self.verification_error_counter.add(1, {
                    "operation": "code_analysis",
                    "error_type": type(e).__name__
                })
                raise
    
    @asynccontextmanager
    async def trace_security_scanning(self, verification_id: str, scan_type: str, 
                                    severity_levels: List[str] = None):
        """Trace security scanning process."""
        span_name = "verification_feedback.security_scanning"
        attributes = {
            "verification_feedback.verification_id": verification_id,
            "verification_feedback.scan_type": scan_type
        }
        
        if severity_levels:
            attributes["verification_feedback.severity_levels"] = ",".join(severity_levels)
        
        with self.tracer.start_as_current_span(span_name, attributes=attributes) as span:
            start_time = time.time()
            issues_found = 0
            try:
                yield span
                duration = time.time() - start_time
                self.verification_duration.record(duration, {"operation": "security_scanning"})
                self.security_scan_counter.add(1, {"scan_type": scan_type})
                self.security_issues_found.add(issues_found, {"scan_type": scan_type})
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                self.verification_error_counter.add(1, {
                    "operation": "security_scanning",
                    "error_type": type(e).__name__
                })
                raise
    
    @asynccontextmanager
    async def trace_quality_assessment(self, verification_id: str, assessment_type: str, 
                                    metrics_count: int = 0):
        """Trace quality assessment process."""
        span_name = "verification_feedback.quality_assessment"
        attributes = {
            "verification_feedback.verification_id": verification_id,
            "verification_feedback.assessment_type": assessment_type,
            "verification_feedback.metrics_count": metrics_count
        }
        
        with self.tracer.start_as_current_span(span_name, attributes=attributes) as span:
            start_time = time.time()
            quality_score = 0.0
            try:
                yield span
                duration = time.time() - start_time
                self.verification_duration.record(duration, {"operation": "quality_assessment"})
                self.quality_assessment_counter.add(1, {"assessment_type": assessment_type})
                self.quality_score_histogram.record(quality_score, {"assessment_type": assessment_type})
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                self.verification_error_counter.add(1, {
                    "operation": "quality_assessment",
                    "error_type": type(e).__name__
                })
                raise
    
    @asynccontextmanager
    async def trace_feedback_submission(self, feedback_id: str, feedback_type: str, 
                                     severity: str, target_id: str):
        """Trace feedback submission process."""
        span_name = "verification_feedback.submit_feedback"
        attributes = {
            "verification_feedback.feedback_id": feedback_id,
            "verification_feedback.feedback_type": feedback_type,
            "verification_feedback.severity": severity,
            "verification_feedback.target_id": target_id
        }
        
        with self.tracer.start_as_current_span(span_name, attributes=attributes) as span:
            start_time = time.time()
            try:
                yield span
                duration = time.time() - start_time
                self.feedback_processing_duration.record(duration, {"operation": "submission"})
                self.feedback_submission_counter.add(1, {"feedback_type": feedback_type})
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                self.verification_error_counter.add(1, {
                    "operation": "feedback_submission",
                    "error_type": type(e).__name__
                })
                raise
    
    @asynccontextmanager
    async def trace_feedback_processing(self, feedback_id: str, processing_type: str):
        """Trace feedback processing process."""
        span_name = "verification_feedback.process_feedback"
        attributes = {
            "verification_feedback.feedback_id": feedback_id,
            "verification_feedback.processing_type": processing_type
        }
        
        with self.tracer.start_as_current_span(span_name, attributes=attributes) as span:
            start_time = time.time()
            try:
                yield span
                duration = time.time() - start_time
                self.feedback_processing_duration.record(duration, {"processing_type": processing_type})
                self.feedback_auto_processing_counter.add(1, {"processing_type": processing_type})
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                self.verification_error_counter.add(1, {
                    "operation": "feedback_processing",
                    "error_type": type(e).__name__
                })
                raise
    
    @asynccontextmanager
    async def trace_rule_application(self, verification_id: str, rule_name: str, 
                                  rule_type: str, target_type: str):
        """Trace rule application process."""
        span_name = "verification_feedback.apply_rule"
        attributes = {
            "verification_feedback.verification_id": verification_id,
            "verification_feedback.rule_name": rule_name,
            "verification_feedback.rule_type": rule_type,
            "verification_feedback.target_type": target_type
        }
        
        with self.tracer.start_as_current_span(span_name, attributes=attributes) as span:
            try:
                yield span
                self.verification_rules_counter.add(1, {
                    "rule_type": rule_type,
                    "target_type": target_type
                })
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                self.verification_error_counter.add(1, {
                    "operation": "rule_application",
                    "error_type": type(e).__name__
                })
                raise
    
    def record_verification_metrics(self, verification_id: str, duration: float, 
                                 rule_count: int, issues_found: int, success: bool):
        """Record verification execution metrics."""
        self.verification_duration.record(duration)
        self.verification_execution_counter.add(1, {"success": success})
        
        if issues_found > 0:
            self.security_issues_found.add(issues_found)
    
    def record_security_scan_metrics(self, scan_type: str, duration: float, 
                                  issues_found: int, severity_breakdown: Dict[str, int]):
        """Record security scan metrics."""
        self.verification_duration.record(duration, {"operation": "security_scan"})
        self.security_scan_counter.add(1, {"scan_type": scan_type})
        self.security_issues_found.add(issues_found, {"scan_type": scan_type})
        
        # Record severity breakdown
        for severity, count in severity_breakdown.items():
            self.security_issues_found.add(count, {
                "scan_type": scan_type,
                "severity": severity
            })
    
    def record_quality_metrics(self, assessment_type: str, duration: float, 
                             quality_score: float, metrics_count: int):
        """Record quality assessment metrics."""
        self.verification_duration.record(duration, {"operation": "quality_assessment"})
        self.quality_assessment_counter.add(1, {"assessment_type": assessment_type})
        self.quality_score_histogram.record(quality_score, {"assessment_type": assessment_type})
    
    def record_feedback_metrics(self, feedback_type: str, severity: str, 
                               processing_time: float, auto_processed: bool):
        """Record feedback metrics."""
        self.feedback_processing_duration.record(processing_time, {"feedback_type": feedback_type})
        self.feedback_submission_counter.add(1, {"feedback_type": feedback_type, "severity": severity})
        
        if auto_processed:
            self.feedback_auto_processing_counter.add(1, {"feedback_type": feedback_type})
    
    def add_verification_attributes(self, span, verification_id: str, target_type: str, 
                                  target_id: str, status: str):
        """Add verification attributes to span."""
        span.set_attribute("verification_feedback.verification_id", verification_id)
        span.set_attribute("verification_feedback.target_type", target_type)
        span.set_attribute("verification_feedback.target_id", target_id)
        span.set_attribute("verification_feedback.status", status)
    
    def add_analysis_attributes(self, span, analysis_type: str, file_count: int, 
                              line_count: int, issues_found: int):
        """Add analysis attributes to span."""
        span.set_attribute("verification_feedback.analysis_type", analysis_type)
        span.set_attribute("verification_feedback.file_count", file_count)
        span.set_attribute("verification_feedback.line_count", line_count)
        span.set_attribute("verification_feedback.issues_found", issues_found)
    
    def add_security_attributes(self, span, scan_type: str, vulnerabilities_found: int, 
                              severity_levels: List[str]):
        """Add security attributes to span."""
        span.set_attribute("verification_feedback.scan_type", scan_type)
        span.set_attribute("verification_feedback.vulnerabilities_found", vulnerabilities_found)
        span.set_attribute("verification_feedback.severity_levels", ",".join(severity_levels))
    
    def add_quality_attributes(self, span, assessment_type: str, quality_score: float, 
                             metrics_count: int, passed_checks: int):
        """Add quality attributes to span."""
        span.set_attribute("verification_feedback.assessment_type", assessment_type)
        span.set_attribute("verification_feedback.quality_score", quality_score)
        span.set_attribute("verification_feedback.metrics_count", metrics_count)
        span.set_attribute("verification_feedback.passed_checks", passed_checks)
    
    def add_feedback_attributes(self, span, feedback_id: str, feedback_type: str, 
                              severity: str, auto_processed: bool):
        """Add feedback attributes to span."""
        span.set_attribute("verification_feedback.feedback_id", feedback_id)
        span.set_attribute("verification_feedback.feedback_type", feedback_type)
        span.set_attribute("verification_feedback.severity", severity)
        span.set_attribute("verification_feedback.auto_processed", auto_processed)
    
    def add_error_attributes(self, span, error_type: str, error_message: str, 
                           operation: str = None, verification_id: str = None):
        """Add error attributes to span."""
        span.set_attribute("error.type", error_type)
        span.set_attribute("error.message", error_message)
        if operation:
            span.set_attribute("verification_feedback.operation", operation)
        if verification_id:
            span.set_attribute("verification_feedback.verification_id", verification_id)


# Decorators for verification feedback operations
def trace_verification_operation(operation_name: str = None):
    """Decorator to trace verification operations."""
    def decorator(func):
        name = operation_name or f"verification_feedback.{func.__name__}"
        
        async def async_wrapper(*args, **kwargs):
            tracer = get_tracing_config().get_tracer()
            with tracer.start_as_current_span(name, kind=SpanKind.SERVER) as span:
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


def trace_analysis_operation(operation_name: str = None):
    """Decorator to trace analysis operations."""
    def decorator(func):
        name = operation_name or f"verification_feedback.analysis.{func.__name__}"
        
        async def async_wrapper(*args, **kwargs):
            tracer = get_tracing_config().get_tracer()
            with tracer.start_as_current_span(name, kind=SpanKind.INTERNAL) as span:
                start_time = time.time()
                try:
                    result = await func(*args, **kwargs)
                    duration = time.time() - start_time
                    
                    # Record metrics
                    verification_tracing = VerificationFeedbackTracing()
                    verification_tracing.verification_duration.record(duration, {"operation": "analysis"})
                    verification_tracing.code_analysis_counter.add(1)
                    
                    span.set_status(Status(StatusCode.OK))
                    span.set_attribute("verification_feedback.duration_ms", duration * 1000)
                    
                    return result
                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    verification_tracing = VerificationFeedbackTracing()
                    verification_tracing.verification_error_counter.add(1, {
                        "operation": "analysis",
                        "error_type": type(e).__name__
                    })
                    raise
        
        if hasattr(func, '__call__') and hasattr(func, '__code__') and func.__code__.co_flags & 0x80:
            return async_wrapper
        return func
    
    return decorator


def trace_feedback_operation(operation_name: str = None):
    """Decorator to trace feedback operations."""
    def decorator(func):
        name = operation_name or f"verification_feedback.feedback.{func.__name__}"
        
        async def async_wrapper(*args, **kwargs):
            tracer = get_tracing_config().get_tracer()
            with tracer.start_as_current_span(name, kind=SpanKind.INTERNAL) as span:
                start_time = time.time()
                try:
                    result = await func(*args, **kwargs)
                    duration = time.time() - start_time
                    
                    # Record metrics
                    verification_tracing = VerificationFeedbackTracing()
                    verification_tracing.feedback_processing_duration.record(duration)
                    verification_tracing.feedback_submission_counter.add(1)
                    
                    span.set_status(Status(StatusCode.OK))
                    span.set_attribute("verification_feedback.duration_ms", duration * 1000)
                    
                    return result
                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    verification_tracing = VerificationFeedbackTracing()
                    verification_tracing.verification_error_counter.add(1, {
                        "operation": "feedback",
                        "error_type": type(e).__name__
                    })
                    raise
        
        if hasattr(func, '__call__') and hasattr(func, '__code__') and func.__code__.co_flags & 0x80:
            return async_wrapper
        return func
    
    return decorator


# Global instance
verification_feedback_tracing = VerificationFeedbackTracing()


def get_verification_feedback_tracing() -> VerificationFeedbackTracing:
    """Get the global verification feedback tracing instance."""
    return verification_feedback_tracing


def initialize_verification_feedback_tracing():
    """Initialize verification feedback tracing."""
    config = get_tracing_config()
    config.initialize("verification-feedback")
    
    # Instrument database clients
    manager = get_instrumentation_manager()
    manager.instrument_database()
    
    logger.info("Verification feedback tracing initialized")