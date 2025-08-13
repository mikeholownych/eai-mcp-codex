"""
Verification Feedback Application Performance Monitoring (APM) implementation.
Provides comprehensive performance monitoring for code analysis, security scanning, and quality assessment.
"""

import logging
import time
from typing import Dict, Any, Optional, List
from contextlib import asynccontextmanager
from dataclasses import dataclass
from enum import Enum
from collections import defaultdict
import statistics

from opentelemetry.trace import Status, StatusCode

from src.common.apm import (
    APMOperationType, 
    APMConfig, 
    get_apm
)
from src.common.tracing import get_tracing_config

logger = logging.getLogger(__name__)


class VerificationFeedbackOperationType(Enum):
    """Verification Feedback specific operation types."""
    CODE_ANALYSIS = "code_analysis"
    SECURITY_SCANNING = "security_scanning"
    QUALITY_ASSESSMENT = "quality_assessment"
    VERIFICATION_EXECUTION = "verification_execution"
    FEEDBACK_SUBMISSION = "feedback_submission"
    FEEDBACK_PROCESSING = "feedback_processing"
    RULE_APPLICATION = "rule_application"
    VULNERABILITY_DETECTION = "vulnerability_detection"
    COMPLIANCE_CHECKING = "compliance_checking"
    PERFORMANCE_ANALYSIS = "performance_analysis"
    STATIC_ANALYSIS = "static_analysis"
    DYNAMIC_ANALYSIS = "dynamic_analysis"


@dataclass
class VerificationMetrics:
    """Verification-specific performance metrics."""
    verification_id: str
    execution_duration: float = 0.0
    total_rules: int = 0
    passed_rules: int = 0
    failed_rules: int = 0
    total_issues: int = 0
    critical_issues: int = 0
    high_issues: int = 0
    medium_issues: int = 0
    low_issues: int = 0
    files_analyzed: int = 0
    lines_analyzed: int = 0
    complexity_score: float = 0.0
    quality_score: float = 0.0
    security_score: float = 0.0
    success: bool = True
    error_message: Optional[str] = None
    last_updated: float = 0.0
    
    @property
    def rule_pass_rate(self) -> float:
        """Calculate rule pass rate."""
        if self.total_rules == 0:
            return 0.0
        return self.passed_rules / self.total_rules
    
    @property
    def issue_density(self) -> float:
        """Calculate issue density per line of code."""
        if self.lines_analyzed == 0:
            return 0.0
        return self.total_issues / self.lines_analyzed


@dataclass
class AnalysisMetrics:
    """Analysis-specific performance metrics."""
    analysis_id: str
    verification_id: str
    analysis_type: str
    execution_duration: float = 0.0
    files_processed: int = 0
    lines_processed: int = 0
    issues_found: int = 0
    complexity_score: float = 0.0
    maintainability_score: float = 0.0
    reliability_score: float = 0.0
    security_score: float = 0.0
    performance_score: float = 0.0
    success: bool = True
    error_message: Optional[str] = None


@dataclass
class SecurityScanMetrics:
    """Security scan-specific performance metrics."""
    scan_id: str
    verification_id: str
    scan_type: str
    duration: float
    success: bool
    vulnerabilities_found: int
    critical_vulnerabilities: int
    high_vulnerabilities: int
    medium_vulnerabilities: int
    low_vulnerabilities: int
    false_positives: int
    scan_coverage: float = 0.0
    strategy_used: str = "static"
    error_message: Optional[str] = None


@dataclass
class QualityAssessmentMetrics:
    """Quality assessment-specific performance metrics."""
    assessment_id: str
    verification_id: str
    assessment_type: str
    duration: float
    success: bool
    quality_score: float
    metrics_count: int
    passed_checks: int
    failed_checks: int
    code_smells: int
    technical_debt: float = 0.0
    duplications: int = 0
    coverage: float = 0.0
    error_message: Optional[str] = None


@dataclass
class FeedbackMetrics:
    """Feedback-specific performance metrics."""
    feedback_id: str
    verification_id: str
    feedback_type: str
    severity: str
    submission_duration: float = 0.0
    processing_duration: float = 0.0
    auto_processed: bool = False
    resolution_duration: float = 0.0
    resolved: bool = False
    error_message: Optional[str] = None


class VerificationFeedbackAPM:
    """APM implementation for Verification Feedback service."""
    
    def __init__(self, config: APMConfig = None):
        """Initialize Verification Feedback APM."""
        self.config = config or APMConfig()
        self.apm = get_apm()
        self.tracer = get_tracing_config().get_tracer()
        self.meter = get_tracing_config().get_meter()
        
        # Performance tracking
        self.verification_metrics = defaultdict(lambda: VerificationMetrics(verification_id=""))
        self.analysis_metrics = defaultdict(lambda: AnalysisMetrics(analysis_id="", verification_id="", analysis_type=""))
        self.security_scan_metrics = []
        self.quality_assessment_metrics = []
        self.feedback_metrics = []
        
        # Initialize metrics
        self._initialize_metrics()
        
        # Performance thresholds
        self.slow_verification_threshold = 120.0  # seconds
        self.slow_analysis_threshold = 60.0  # seconds
        self.slow_security_scan_threshold = 90.0  # seconds
        self.low_quality_threshold = 0.7  # 70%
        self.high_vulnerability_threshold = 5  # vulnerabilities
        
        # History limits
        self.max_security_scan_history = 1000
        self.max_quality_assessment_history = 1000
        self.max_feedback_history = 5000
    
    def _initialize_metrics(self):
        """Initialize OpenTelemetry metrics for Verification Feedback."""
        # Counters
        self.verification_execution_counter = self.meter.create_counter(
            "verification_feedback_verifications_total",
            description="Total number of verification executions"
        )
        
        self.analysis_operations_counter = self.meter.create_counter(
            "verification_feedback_analyses_total",
            description="Total number of analysis operations"
        )
        
        self.security_scan_counter = self.meter.create_counter(
            "verification_feedback_security_scans_total",
            description="Total number of security scans"
        )
        
        self.vulnerability_counter = self.meter.create_counter(
            "verification_feedback_vulnerabilities_total",
            description="Total number of vulnerabilities found"
        )
        
        self.quality_assessment_counter = self.meter.create_counter(
            "verification_feedback_quality_assessments_total",
            description="Total number of quality assessments"
        )
        
        self.feedback_submission_counter = self.meter.create_counter(
            "verification_feedback_feedback_submissions_total",
            description="Total number of feedback submissions"
        )
        
        # Histograms
        self.verification_duration = self.meter.create_histogram(
            "verification_feedback_verification_duration_seconds",
            description="Duration of verification executions"
        )
        
        self.analysis_duration = self.meter.create_histogram(
            "verification_feedback_analysis_duration_seconds",
            description="Duration of analysis operations"
        )
        
        self.security_scan_duration = self.meter.create_histogram(
            "verification_feedback_security_scan_duration_seconds",
            description="Duration of security scans"
        )
        
        self.quality_assessment_duration = self.meter.create_histogram(
            "verification_feedback_quality_assessment_duration_seconds",
            description="Duration of quality assessments"
        )
        
        self.feedback_processing_duration = self.meter.create_histogram(
            "verification_feedback_feedback_processing_duration_seconds",
            description="Duration of feedback processing"
        )
        
        # Gauges
        self.quality_score_gauge = self.meter.create_up_down_counter(
            "verification_feedback_quality_score",
            description="Quality assessment scores"
        )
        
        self.security_score_gauge = self.meter.create_up_down_counter(
            "verification_feedback_security_score",
            description="Security assessment scores"
        )
        
        self.vulnerability_count_gauge = self.meter.create_up_down_counter(
            "verification_feedback_vulnerability_count",
            description="Number of vulnerabilities"
        )
    
    @asynccontextmanager
    async def trace_verification_execution(self, verification_id: str, target_type: str,
                                       target_id: str, rule_count: int = 0):
        """Trace verification execution process."""
        operation_name = "execute_verification"
        attributes = {
            "verification_feedback.verification_id": verification_id,
            "verification_feedback.target_type": target_type,
            "verification_feedback.target_id": target_id,
            "verification_feedback.rule_count": rule_count
        }
        
        start_time = time.time()
        success = True
        error_message = None
        
        async with self.apm.trace_async_operation(
            operation_name, APMOperationType.CPU_INTENSIVE, attributes
        ) as span:
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
                
                # Record verification metrics
                verification_metrics = self.verification_metrics[verification_id]
                verification_metrics.verification_id = verification_id
                verification_metrics.execution_duration = duration
                verification_metrics.total_rules = rule_count
                verification_metrics.success = success
                if error_message:
                    verification_metrics.error_message = error_message
                verification_metrics.last_updated = end_time
                
                # Update metrics
                self.verification_execution_counter.add(1, {
                    "target_type": target_type,
                    "success": success
                })
                
                self.verification_duration.record(duration, {
                    "target_type": target_type
                })
    
    @asynccontextmanager
    async def trace_code_analysis(self, verification_id: str, analysis_type: str,
                                file_count: int = 0, line_count: int = 0):
        """Trace code analysis process."""
        operation_name = "analyze_code"
        attributes = {
            "verification_feedback.verification_id": verification_id,
            "verification_feedback.analysis_type": analysis_type,
            "verification_feedback.file_count": file_count,
            "verification_feedback.line_count": line_count
        }
        
        start_time = time.time()
        success = True
        error_message = None
        issues_found = 0
        analysis_id = f"{verification_id}#{analysis_type}#{int(time.time())}"
        
        async with self.apm.trace_async_operation(
            operation_name, APMOperationType.CPU_INTENSIVE, attributes
        ) as span:
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
                
                # Record analysis metrics
                analysis_metrics = AnalysisMetrics(
                    analysis_id=analysis_id,
                    verification_id=verification_id,
                    analysis_type=analysis_type,
                    execution_duration=duration,
                    files_processed=file_count,
                    lines_processed=line_count,
                    issues_found=issues_found,
                    success=success,
                    error_message=error_message
                )
                self.analysis_metrics[analysis_id] = analysis_metrics
                
                # Update verification metrics
                if verification_id in self.verification_metrics:
                    verification_metrics = self.verification_metrics[verification_id]
                    verification_metrics.files_analyzed += file_count
                    verification_metrics.lines_analyzed += line_count
                    verification_metrics.total_issues += issues_found
                    verification_metrics.last_updated = end_time
                
                # Update metrics
                self.analysis_operations_counter.add(1, {
                    "analysis_type": analysis_type,
                    "success": success
                })
                
                self.analysis_duration.record(duration, {
                    "analysis_type": analysis_type
                })
    
    @asynccontextmanager
    async def trace_security_scanning(self, verification_id: str, scan_type: str,
                                    severity_levels: List[str] = None):
        """Trace security scanning process."""
        operation_name = "scan_security"
        attributes = {
            "verification_feedback.verification_id": verification_id,
            "verification_feedback.scan_type": scan_type
        }
        
        if severity_levels:
            attributes["verification_feedback.severity_levels"] = ",".join(severity_levels)
        
        start_time = time.time()
        success = True
        error_message = None
        vulnerabilities_found = 0
        critical_vulnerabilities = 0
        high_vulnerabilities = 0
        medium_vulnerabilities = 0
        low_vulnerabilities = 0
        false_positives = 0
        scan_id = f"{verification_id}#{scan_type}#{int(time.time())}"
        
        async with self.apm.trace_async_operation(
            operation_name, APMOperationType.CPU_INTENSIVE, attributes
        ) as span:
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
                
                # Record security scan metrics
                scan_metrics = SecurityScanMetrics(
                    scan_id=scan_id,
                    verification_id=verification_id,
                    scan_type=scan_type,
                    duration=duration,
                    success=success,
                    vulnerabilities_found=vulnerabilities_found,
                    critical_vulnerabilities=critical_vulnerabilities,
                    high_vulnerabilities=high_vulnerabilities,
                    medium_vulnerabilities=medium_vulnerabilities,
                    low_vulnerabilities=low_vulnerabilities,
                    false_positives=false_positives,
                    strategy_used=scan_type,
                    error_message=error_message
                )
                self.security_scan_metrics.append(scan_metrics)
                
                # Keep only recent security scan data
                if len(self.security_scan_metrics) > self.max_security_scan_history:
                    self.security_scan_metrics.pop(0)
                
                # Update verification metrics
                if verification_id in self.verification_metrics:
                    verification_metrics = self.verification_metrics[verification_id]
                    verification_metrics.total_issues += vulnerabilities_found
                    verification_metrics.critical_issues += critical_vulnerabilities
                    verification_metrics.high_issues += high_vulnerabilities
                    verification_metrics.medium_issues += medium_vulnerabilities
                    verification_metrics.low_issues += low_vulnerabilities
                    verification_metrics.last_updated = end_time
                
                # Update metrics
                self.security_scan_counter.add(1, {
                    "scan_type": scan_type,
                    "success": success
                })
                
                self.vulnerability_counter.add(vulnerabilities_found, {
                    "scan_type": scan_type,
                    "success": success
                })
                
                self.security_scan_duration.record(duration, {
                    "scan_type": scan_type
                })
                
                self.vulnerability_count_gauge.add(vulnerabilities_found, {
                    "scan_type": scan_type
                })
    
    @asynccontextmanager
    async def trace_quality_assessment(self, verification_id: str, assessment_type: str,
                                     metrics_count: int = 0):
        """Trace quality assessment process."""
        operation_name = "assess_quality"
        attributes = {
            "verification_feedback.verification_id": verification_id,
            "verification_feedback.assessment_type": assessment_type,
            "verification_feedback.metrics_count": metrics_count
        }
        
        start_time = time.time()
        success = True
        error_message = None
        quality_score = 0.0
        passed_checks = 0
        failed_checks = 0
        assessment_id = f"{verification_id}#{assessment_type}#{int(time.time())}"
        
        async with self.apm.trace_async_operation(
            operation_name, APMOperationType.CPU_INTENSIVE, attributes
        ) as span:
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
                
                # Record quality assessment metrics
                assessment_metrics = QualityAssessmentMetrics(
                    assessment_id=assessment_id,
                    verification_id=verification_id,
                    assessment_type=assessment_type,
                    duration=duration,
                    success=success,
                    quality_score=quality_score,
                    metrics_count=metrics_count,
                    passed_checks=passed_checks,
                    failed_checks=failed_checks,
                    error_message=error_message
                )
                self.quality_assessment_metrics.append(assessment_metrics)
                
                # Keep only recent quality assessment data
                if len(self.quality_assessment_metrics) > self.max_quality_assessment_history:
                    self.quality_assessment_metrics.pop(0)
                
                # Update verification metrics
                if verification_id in self.verification_metrics:
                    verification_metrics = self.verification_metrics[verification_id]
                    verification_metrics.quality_score = quality_score
                    verification_metrics.last_updated = end_time
                
                # Update metrics
                self.quality_assessment_counter.add(1, {
                    "assessment_type": assessment_type,
                    "success": success
                })
                
                self.quality_assessment_duration.record(duration, {
                    "assessment_type": assessment_type
                })
                
                self.quality_score_gauge.add(quality_score, {
                    "assessment_type": assessment_type
                })
    
    @asynccontextmanager
    async def trace_feedback_submission(self, feedback_id: str, feedback_type: str,
                                      severity: str, target_id: str):
        """Trace feedback submission process."""
        operation_name = "submit_feedback"
        attributes = {
            "verification_feedback.feedback_id": feedback_id,
            "verification_feedback.feedback_type": feedback_type,
            "verification_feedback.severity": severity,
            "verification_feedback.target_id": target_id
        }
        
        start_time = time.time()
        success = True
        error_message = None
        
        async with self.apm.trace_async_operation(
            operation_name, APMOperationType.IO_INTENSIVE, attributes
        ) as span:
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
                
                # Record feedback metrics
                feedback_metrics = FeedbackMetrics(
                    feedback_id=feedback_id,
                    verification_id="",
                    feedback_type=feedback_type,
                    severity=severity,
                    submission_duration=duration,
                    error_message=error_message
                )
                self.feedback_metrics.append(feedback_metrics)
                
                # Keep only recent feedback data
                if len(self.feedback_metrics) > self.max_feedback_history:
                    self.feedback_metrics.pop(0)
                
                # Update metrics
                self.feedback_submission_counter.add(1, {
                    "feedback_type": feedback_type,
                    "severity": severity,
                    "success": success
                })
    
    @asynccontextmanager
    async def trace_feedback_processing(self, feedback_id: str, processing_type: str,
                                      auto_processed: bool = False):
        """Trace feedback processing process."""
        operation_name = "process_feedback"
        attributes = {
            "verification_feedback.feedback_id": feedback_id,
            "verification_feedback.processing_type": processing_type,
            "verification_feedback.auto_processed": auto_processed
        }
        
        start_time = time.time()
        success = True
        error_message = None
        
        async with self.apm.trace_async_operation(
            operation_name, APMOperationType.CPU_INTENSIVE, attributes
        ) as span:
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
                
                # Update feedback metrics
                for feedback in self.feedback_metrics:
                    if feedback.feedback_id == feedback_id:
                        feedback.processing_duration = duration
                        feedback.auto_processed = auto_processed
                        break
                
                # Update metrics
                self.feedback_processing_duration.record(duration, {
                    "processing_type": processing_type,
                    "auto_processed": auto_processed
                })
    
    def get_verification_performance_summary(self, verification_id: str = None) -> Dict[str, Any]:
        """Get performance summary for verifications."""
        if verification_id:
            metrics = self.verification_metrics.get(verification_id)
            if not metrics or metrics.verification_id == "":
                return {"verification_id": verification_id, "message": "No data available"}
            
            return {
                "verification_id": verification_id,
                "execution_duration": metrics.execution_duration,
                "total_rules": metrics.total_rules,
                "passed_rules": metrics.passed_rules,
                "failed_rules": metrics.failed_rules,
                "rule_pass_rate": metrics.rule_pass_rate,
                "total_issues": metrics.total_issues,
                "critical_issues": metrics.critical_issues,
                "high_issues": metrics.high_issues,
                "medium_issues": metrics.medium_issues,
                "low_issues": metrics.low_issues,
                "files_analyzed": metrics.files_analyzed,
                "lines_analyzed": metrics.lines_analyzed,
                "issue_density": metrics.issue_density,
                "complexity_score": metrics.complexity_score,
                "quality_score": metrics.quality_score,
                "security_score": metrics.security_score,
                "success": metrics.success,
                "error_message": metrics.error_message,
                "last_updated": metrics.last_updated
            }
        else:
            # Return summary for all verifications
            summary = {}
            for v_id, metrics in self.verification_metrics.items():
                if metrics.verification_id:
                    summary[v_id] = self.get_verification_performance_summary(v_id)
            return summary
    
    def get_analysis_performance_summary(self, analysis_id: str = None) -> Dict[str, Any]:
        """Get performance summary for analyses."""
        if analysis_id:
            metrics = self.analysis_metrics.get(analysis_id)
            if not metrics or metrics.analysis_id == "":
                return {"analysis_id": analysis_id, "message": "No data available"}
            
            return {
                "analysis_id": analysis_id,
                "verification_id": metrics.verification_id,
                "analysis_type": metrics.analysis_type,
                "execution_duration": metrics.execution_duration,
                "files_processed": metrics.files_processed,
                "lines_processed": metrics.lines_processed,
                "issues_found": metrics.issues_found,
                "complexity_score": metrics.complexity_score,
                "maintainability_score": metrics.maintainability_score,
                "reliability_score": metrics.reliability_score,
                "security_score": metrics.security_score,
                "performance_score": metrics.performance_score,
                "success": metrics.success,
                "error_message": metrics.error_message
            }
        else:
            # Return summary for all analyses
            summary = {}
            for a_id, metrics in self.analysis_metrics.items():
                if metrics.analysis_id:
                    summary[a_id] = self.get_analysis_performance_summary(a_id)
            return summary
    
    def get_security_scan_summary(self) -> Dict[str, Any]:
        """Get security scan summary."""
        if not self.security_scan_metrics:
            return {"message": "No security scans recorded"}
        
        scan_data = self.security_scan_metrics
        total_scans = len(scan_data)
        successful_scans = sum(1 for s in scan_data if s.success)
        
        # Calculate average duration
        avg_duration = statistics.mean(s.duration for s in scan_data)
        
        # Calculate total vulnerabilities
        total_vulnerabilities = sum(s.vulnerabilities_found for s in scan_data)
        critical_vulnerabilities = sum(s.critical_vulnerabilities for s in scan_data)
        high_vulnerabilities = sum(s.high_vulnerabilities for s in scan_data)
        medium_vulnerabilities = sum(s.medium_vulnerabilities for s in scan_data)
        low_vulnerabilities = sum(s.low_vulnerabilities for s in scan_data)
        
        # Get scan type distribution
        type_distribution = defaultdict(int)
        for s in scan_data:
            type_distribution[s.scan_type] += 1
        
        # Get vulnerability severity distribution
        severity_distribution = {
            "critical": critical_vulnerabilities,
            "high": high_vulnerabilities,
            "medium": medium_vulnerabilities,
            "low": low_vulnerabilities
        }
        
        return {
            "total_security_scans": total_scans,
            "success_rate": successful_scans / total_scans if total_scans > 0 else 0,
            "average_duration": avg_duration,
            "total_vulnerabilities": total_vulnerabilities,
            "vulnerability_severity_distribution": severity_distribution,
            "scan_type_distribution": dict(type_distribution)
        }
    
    def get_quality_assessment_summary(self) -> Dict[str, Any]:
        """Get quality assessment summary."""
        if not self.quality_assessment_metrics:
            return {"message": "No quality assessments recorded"}
        
        assessment_data = self.quality_assessment_metrics
        total_assessments = len(assessment_data)
        successful_assessments = sum(1 for a in assessment_data if a.success)
        
        # Calculate average duration
        avg_duration = statistics.mean(a.duration for a in assessment_data)
        
        # Calculate average quality score
        avg_quality_score = statistics.mean(a.quality_score for a in assessment_data)
        
        # Calculate total checks
        total_checks = sum(a.metrics_count for a in assessment_data)
        passed_checks = sum(a.passed_checks for a in assessment_data)
        failed_checks = sum(a.failed_checks for a in assessment_data)
        
        # Get assessment type distribution
        type_distribution = defaultdict(int)
        for a in assessment_data:
            type_distribution[a.assessment_type] += 1
        
        return {
            "total_quality_assessments": total_assessments,
            "success_rate": successful_assessments / total_assessments if total_assessments > 0 else 0,
            "average_duration": avg_duration,
            "average_quality_score": avg_quality_score,
            "total_checks": total_checks,
            "passed_checks": passed_checks,
            "failed_checks": failed_checks,
            "check_pass_rate": passed_checks / total_checks if total_checks > 0 else 0,
            "assessment_type_distribution": dict(type_distribution)
        }
    
    def get_feedback_summary(self) -> Dict[str, Any]:
        """Get feedback summary."""
        if not self.feedback_metrics:
            return {"message": "No feedback recorded"}
        
        feedback_data = self.feedback_metrics
        total_feedback = len(feedback_data)
        
        # Calculate average submission duration
        submission_durations = [f.submission_duration for f in feedback_data if f.submission_duration > 0]
        avg_submission_duration = statistics.mean(submission_durations) if submission_durations else 0
        
        # Calculate average processing duration
        processing_durations = [f.processing_duration for f in feedback_data if f.processing_duration > 0]
        avg_processing_duration = statistics.mean(processing_durations) if processing_durations else 0
        
        # Calculate auto-processing rate
        auto_processed_count = sum(1 for f in feedback_data if f.auto_processed)
        auto_processing_rate = auto_processed_count / total_feedback if total_feedback > 0 else 0
        
        # Get feedback type distribution
        type_distribution = defaultdict(int)
        for f in feedback_data:
            type_distribution[f.feedback_type] += 1
        
        # Get severity distribution
        severity_distribution = defaultdict(int)
        for f in feedback_data:
            severity_distribution[f.severity] += 1
        
        return {
            "total_feedback": total_feedback,
            "average_submission_duration": avg_submission_duration,
            "average_processing_duration": avg_processing_duration,
            "auto_processing_rate": auto_processing_rate,
            "feedback_type_distribution": dict(type_distribution),
            "severity_distribution": dict(severity_distribution)
        }
    
    def get_performance_insights(self) -> List[Dict[str, Any]]:
        """Get performance insights and recommendations."""
        insights = []
        
        # Analyze verification performance
        for verification_id, metrics in self.verification_metrics.items():
            if not metrics.verification_id:
                continue
            
            # Check for slow verifications
            if metrics.execution_duration > self.slow_verification_threshold:
                insights.append({
                    "type": "slow_verification",
                    "verification_id": verification_id,
                    "severity": "warning",
                    "message": f"Verification {verification_id} took too long to execute ({metrics.execution_duration:.2f}s)",
                    "recommendation": "Optimize verification rules or reduce scope"
                })
            
            # Check for low quality scores
            if metrics.quality_score < self.low_quality_threshold:
                insights.append({
                    "type": "low_quality_score",
                    "verification_id": verification_id,
                    "severity": "warning",
                    "message": f"Verification {verification_id} has low quality score ({metrics.quality_score:.2f})",
                    "recommendation": "Review code quality and address issues"
                })
            
            # Check for high issue density
            if metrics.issue_density > 0.1 and metrics.lines_analyzed > 1000:
                insights.append({
                    "type": "high_issue_density",
                    "verification_id": verification_id,
                    "severity": "warning",
                    "message": f"Verification {verification_id} has high issue density ({metrics.issue_density:.4f} issues per line)",
                    "recommendation": "Focus on code quality improvements"
                })
        
        # Analyze security scan performance
        if self.security_scan_metrics:
            recent_scans = self.security_scan_metrics[-100:]  # Last 100 security scans
            
            # Check for slow scans
            slow_scans = [s for s in recent_scans if s.duration > self.slow_security_scan_threshold]
            if len(slow_scans) > 5:
                insights.append({
                    "type": "slow_security_scans",
                    "severity": "warning",
                    "message": f"High number of slow security scans ({len(slow_scans)} in last 100)",
                    "recommendation": "Optimize security scanning process or reduce scan scope"
                })
            
            # Check for high vulnerability counts
            high_vuln_scans = [s for s in recent_scans if s.vulnerabilities_found > self.high_vulnerability_threshold]
            if len(high_vuln_scans) > 10:
                insights.append({
                    "type": "high_vulnerability_count",
                    "severity": "error",
                    "message": f"High number of security scans with many vulnerabilities ({len(high_vuln_scans)} in last 100)",
                    "recommendation": "Prioritize security improvements and code review"
                })
        
        # Analyze quality assessment performance
        if self.quality_assessment_metrics:
            recent_assessments = self.quality_assessment_metrics[-100:]  # Last 100 quality assessments
            
            # Check for low quality scores
            low_quality_assessments = [a for a in recent_assessments if a.quality_score < self.low_quality_threshold]
            if len(low_quality_assessments) > 20:
                insights.append({
                    "type": "low_quality_assessments",
                    "severity": "warning",
                    "message": f"High number of low quality assessments ({len(low_quality_assessments)} in last 100)",
                    "recommendation": "Improve code quality standards and practices"
                })
        
        return insights
    
    def record_verification_results(self, verification_id: str, passed_rules: int, failed_rules: int,
                                  critical_issues: int, high_issues: int, medium_issues: int, low_issues: int,
                                  complexity_score: float, quality_score: float, security_score: float):
        """Record verification results."""
        if verification_id in self.verification_metrics:
            metrics = self.verification_metrics[verification_id]
            metrics.passed_rules = passed_rules
            metrics.failed_rules = failed_rules
            metrics.critical_issues = critical_issues
            metrics.high_issues = high_issues
            metrics.medium_issues = medium_issues
            metrics.low_issues = low_issues
            metrics.complexity_score = complexity_score
            metrics.quality_score = quality_score
            metrics.security_score = security_score
    
    def record_analysis_results(self, analysis_id: str, issues_found: int, complexity_score: float,
                              maintainability_score: float, reliability_score: float,
                              security_score: float, performance_score: float):
        """Record analysis results."""
        if analysis_id in self.analysis_metrics:
            metrics = self.analysis_metrics[analysis_id]
            metrics.issues_found = issues_found
            metrics.complexity_score = complexity_score
            metrics.maintainability_score = maintainability_score
            metrics.reliability_score = reliability_score
            metrics.security_score = security_score
            metrics.performance_score = performance_score
    
    def record_security_scan_results(self, scan_id: str, vulnerabilities_found: int, critical_vulnerabilities: int,
                                   high_vulnerabilities: int, medium_vulnerabilities: int, low_vulnerabilities: int,
                                   false_positives: int, scan_coverage: float):
        """Record security scan results."""
        for scan in self.security_scan_metrics:
            if scan.scan_id == scan_id:
                scan.vulnerabilities_found = vulnerabilities_found
                scan.critical_vulnerabilities = critical_vulnerabilities
                scan.high_vulnerabilities = high_vulnerabilities
                scan.medium_vulnerabilities = medium_vulnerabilities
                scan.low_vulnerabilities = low_vulnerabilities
                scan.false_positives = false_positives
                scan.scan_coverage = scan_coverage
                break
    
    def record_quality_assessment_results(self, assessment_id: str, quality_score: float, passed_checks: int,
                                        failed_checks: int, code_smells: int, technical_debt: float,
                                        duplications: int, coverage: float):
        """Record quality assessment results."""
        for assessment in self.quality_assessment_metrics:
            if assessment.assessment_id == assessment_id:
                assessment.quality_score = quality_score
                assessment.passed_checks = passed_checks
                assessment.failed_checks = failed_checks
                assessment.code_smells = code_smells
                assessment.technical_debt = technical_debt
                assessment.duplications = duplications
                assessment.coverage = coverage
                break
    
    def record_feedback_results(self, feedback_id: str, resolution_duration: float, resolved: bool):
        """Record feedback results."""
        for feedback in self.feedback_metrics:
            if feedback.feedback_id == feedback_id:
                feedback.resolution_duration = resolution_duration
                feedback.resolved = resolved
                break


# Global instance
verification_feedback_apm = None


def get_verification_feedback_apm() -> VerificationFeedbackAPM:
    """Get the global Verification Feedback APM instance."""
    global verification_feedback_apm
    if verification_feedback_apm is None:
        verification_feedback_apm = VerificationFeedbackAPM()
    return verification_feedback_apm


def initialize_verification_feedback_apm(config: APMConfig = None):
    """Initialize the global Verification Feedback APM instance."""
    global verification_feedback_apm
    verification_feedback_apm = VerificationFeedbackAPM(config)
    return verification_feedback_apm


# Decorators for Verification Feedback operations
def trace_verification_execution(operation_name: str = None):
    """Decorator to trace verification execution operations."""
    def decorator(func):
        name = operation_name or f"verification_execution.{func.__name__}"
        
        async def async_wrapper(*args, **kwargs):
            apm = get_verification_feedback_apm()
            
            # Extract parameters
            verification_id = kwargs.get('verification_id', '')
            target_type = kwargs.get('target_type', '')
            target_id = kwargs.get('target_id', '')
            rule_count = kwargs.get('rule_count', 0)
            
            async with apm.trace_verification_execution(verification_id, target_type, target_id, rule_count) as span:
                return await func(*args, **kwargs)
        
        return async_wrapper
    
    return decorator


def trace_code_analysis(operation_name: str = None):
    """Decorator to trace code analysis operations."""
    def decorator(func):
        name = operation_name or f"code_analysis.{func.__name__}"
        
        async def async_wrapper(*args, **kwargs):
            apm = get_verification_feedback_apm()
            
            # Extract parameters
            verification_id = kwargs.get('verification_id', '')
            analysis_type = kwargs.get('analysis_type', '')
            file_count = kwargs.get('file_count', 0)
            line_count = kwargs.get('line_count', 0)
            
            async with apm.trace_code_analysis(verification_id, analysis_type, file_count, line_count) as span:
                return await func(*args, **kwargs)
        
        return async_wrapper
    
    return decorator


def trace_security_scanning(operation_name: str = None):
    """Decorator to trace security scanning operations."""
    def decorator(func):
        name = operation_name or f"security_scanning.{func.__name__}"
        
        async def async_wrapper(*args, **kwargs):
            apm = get_verification_feedback_apm()
            
            # Extract parameters
            verification_id = kwargs.get('verification_id', '')
            scan_type = kwargs.get('scan_type', '')
            severity_levels = kwargs.get('severity_levels', [])
            
            async with apm.trace_security_scanning(verification_id, scan_type, severity_levels) as span:
                return await func(*args, **kwargs)
        
        return async_wrapper
    
    return decorator


def trace_quality_assessment(operation_name: str = None):
    """Decorator to trace quality assessment operations."""
    def decorator(func):
        name = operation_name or f"quality_assessment.{func.__name__}"
        
        async def async_wrapper(*args, **kwargs):
            apm = get_verification_feedback_apm()
            
            # Extract parameters
            verification_id = kwargs.get('verification_id', '')
            assessment_type = kwargs.get('assessment_type', '')
            metrics_count = kwargs.get('metrics_count', 0)
            
            async with apm.trace_quality_assessment(verification_id, assessment_type, metrics_count) as span:
                return await func(*args, **kwargs)
        
        return async_wrapper
    
    return decorator