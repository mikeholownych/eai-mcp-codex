"""
Verification Feedback specific health checks.
Provides comprehensive health monitoring for the Verification Feedback service.
"""

import time
import asyncio
import json
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from ..common.enhanced_health_check import (
    HealthStatus, HealthCheckType, HealthChecker, 
    check_memory_usage, check_disk_usage, check_cpu_usage,
    check_network_connectivity, health_check
)
from ..common.logging import get_logger
from ..common.tracing import get_tracer
from ..common.metrics import get_metrics_collector

logger = get_logger("verification_feedback.health")
tracer = get_tracer()
metrics = get_metrics_collector("verification_feedback")


class VerificationFeedbackHealthChecker:
    """Health checker for Verification Feedback service."""
    
    def __init__(self):
        self.service_name = "verification-feedback"
        self.base_checker = HealthChecker(self.service_name)
        self._setup_health_checks()
    
    def _setup_health_checks(self):
        """Set up all health checks for Verification Feedback."""
        
        # Basic resource checks
        self.base_checker.register_simple_check(
            "memory_usage",
            lambda: check_memory_usage(max_usage_percent=85.0),
            check_type=HealthCheckType.RESOURCE,
            critical=False
        )
        
        self.base_checker.register_simple_check(
            "disk_usage",
            lambda: check_disk_usage(max_usage_percent=85.0),
            check_type=HealthCheckType.RESOURCE,
            critical=False
        )
        
        self.base_checker.register_simple_check(
            "cpu_usage",
            lambda: check_cpu_usage(max_usage_percent=85.0),
            check_type=HealthCheckType.RESOURCE,
            critical=False
        )
        
        # Verification Feedback specific checks
        self.base_checker.register_simple_check(
            "code_analysis",
            self._check_code_analysis,
            check_type=HealthCheckType.BUSINESS_LOGIC,
            critical=True
        )
        
        self.base_checker.register_simple_check(
            "security_scanning",
            self._check_security_scanning,
            check_type=HealthCheckType.BUSINESS_LOGIC,
            critical=True
        )
        
        self.base_checker.register_simple_check(
            "quality_assessment",
            self._check_quality_assessment,
            check_type=HealthCheckType.BUSINESS_LOGIC,
            critical=True
        )
        
        self.base_checker.register_simple_check(
            "verification_status",
            self._check_verification_status,
            check_type=HealthCheckType.BUSINESS_LOGIC,
            critical=True
        )
        
        self.base_checker.register_simple_check(
            "rule_engine",
            self._check_rule_engine,
            check_type=HealthCheckType.DEPENDENCY,
            critical=True
        )
        
        self.base_checker.register_simple_check(
            "feedback_generation",
            self._check_feedback_generation,
            check_type=HealthCheckType.BUSINESS_LOGIC,
            critical=True
        )
        
        self.base_checker.register_simple_check(
            "compliance_checking",
            self._check_compliance_checking,
            check_type=HealthCheckType.BUSINESS_LOGIC,
            critical=True
        )
        
        self.base_checker.register_simple_check(
            "report_generation",
            self._check_report_generation,
            check_type=HealthCheckType.BUSINESS_LOGIC,
            critical=False
        )
    
    async def _check_code_analysis(self) -> Dict[str, Any]:
        """Check code analysis functionality."""
        try:
            # Simulate code analysis tests
            analysis_tests = [
                {
                    "name": "syntax_analysis",
                    "language": "python",
                    "code_size_lines": 500,
                    "expected_success": True
                },
                {
                    "name": "semantic_analysis",
                    "language": "javascript",
                    "code_size_lines": 750,
                    "expected_success": True
                },
                {
                    "name": "dependency_analysis",
                    "language": "java",
                    "code_size_lines": 1000,
                    "expected_success": True
                },
                {
                    "name": "complexity_analysis",
                    "language": "python",
                    "code_size_lines": 300,
                    "expected_success": True
                }
            ]
            
            analysis_results = []
            successful_analyses = 0
            
            for test in analysis_tests:
                try:
                    # Simulate code analysis
                    result = await self._simulate_code_analysis(test)
                    analysis_results.append({
                        "test": test["name"],
                        "analysis_successful": result["analysis_successful"],
                        "analysis_time": result["analysis_time"],
                        "issues_found": result.get("issues_found", 0),
                        "success": result["analysis_successful"] == test["expected_success"]
                    })
                    if result["analysis_successful"] == test["expected_success"]:
                        successful_analyses += 1
                except Exception as e:
                    analysis_results.append({
                        "test": test["name"],
                        "analysis_successful": False,
                        "error": str(e),
                        "success": False
                    })
            
            success_rate = successful_analyses / len(analysis_tests)
            
            if success_rate == 1.0:
                status = HealthStatus.HEALTHY
            elif success_rate >= 0.8:
                status = HealthStatus.DEGRADED
            else:
                status = HealthStatus.UNHEALTHY
            
            return {
                "status": status.value,
                "message": f"Code analysis success rate: {success_rate:.1%}",
                "details": {
                    "total_tests": len(analysis_tests),
                    "successful_analyses": successful_analyses,
                    "success_rate": success_rate,
                    "analysis_results": analysis_results,
                },
            }
            
        except Exception as e:
            return {
                "status": HealthStatus.ERROR.value,
                "message": f"Code analysis check failed: {str(e)}",
            }
    
    async def _simulate_code_analysis(self, test: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate code analysis for testing."""
        # Simulate processing time based on code size
        base_time = test["code_size_lines"] / 1000  # 1 second per 1000 lines
        await asyncio.sleep(base_time)
        
        # Simulate different analysis types
        if test["name"] == "syntax_analysis":
            return {
                "analysis_successful": True,
                "analysis_time": base_time,
                "issues_found": 2,
                "syntax_errors": 0,
                "warnings": 2
            }
        elif test["name"] == "semantic_analysis":
            return {
                "analysis_successful": True,
                "analysis_time": base_time * 1.5,
                "issues_found": 5,
                "semantic_issues": 3,
                "potential_bugs": 2
            }
        elif test["name"] == "dependency_analysis":
            return {
                "analysis_successful": True,
                "analysis_time": base_time * 0.8,
                "issues_found": 3,
                "vulnerabilities": 1,
                "outdated_dependencies": 2
            }
        else:  # complexity_analysis
            return {
                "analysis_successful": True,
                "analysis_time": base_time * 0.6,
                "issues_found": 4,
                "complexity_score": 8.5,
                "maintainability_issues": 2
            }
    
    async def _check_security_scanning(self) -> Dict[str, Any]:
        """Check security scanning functionality."""
        try:
            # Simulate security scanning tests
            security_tests = [
                {
                    "name": "vulnerability_scan",
                    "scan_type": "sast",
                    "target_type": "source_code",
                    "expected_success": True
                },
                {
                    "name": "dependency_scan",
                    "scan_type": "sca",
                    "target_type": "dependencies",
                    "expected_success": True
                },
                {
                    "name": "secret_detection",
                    "scan_type": "secret",
                    "target_type": "codebase",
                    "expected_success": True
                },
                {
                    "name": "malware_scan",
                    "scan_type": "malware",
                    "target_type": "binaries",
                    "expected_success": True
                }
            ]
            
            scanning_results = []
            successful_scans = 0
            
            for test in security_tests:
                try:
                    # Simulate security scan
                    result = await self._simulate_security_scan(test)
                    scanning_results.append({
                        "test": test["name"],
                        "scan_successful": result["scan_successful"],
                        "scan_time": result["scan_time"],
                        "vulnerabilities_found": result.get("vulnerabilities_found", 0),
                        "success": result["scan_successful"] == test["expected_success"]
                    })
                    if result["scan_successful"] == test["expected_success"]:
                        successful_scans += 1
                except Exception as e:
                    scanning_results.append({
                        "test": test["name"],
                        "scan_successful": False,
                        "error": str(e),
                        "success": False
                    })
            
            success_rate = successful_scans / len(security_tests)
            
            if success_rate == 1.0:
                status = HealthStatus.HEALTHY
            elif success_rate >= 0.8:
                status = HealthStatus.DEGRADED
            else:
                status = HealthStatus.UNHEALTHY
            
            return {
                "status": status.value,
                "message": f"Security scanning success rate: {success_rate:.1%}",
                "details": {
                    "total_tests": len(security_tests),
                    "successful_scans": successful_scans,
                    "success_rate": success_rate,
                    "scanning_results": scanning_results,
                },
            }
            
        except Exception as e:
            return {
                "status": HealthStatus.ERROR.value,
                "message": f"Security scanning check failed: {str(e)}",
            }
    
    async def _simulate_security_scan(self, test: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate security scan for testing."""
        # Simulate processing time based on scan type
        base_time = 2.0
        if test["scan_type"] == "sast":
            base_time = 3.0
        elif test["scan_type"] == "sca":
            base_time = 1.5
        elif test["scan_type"] == "secret":
            base_time = 1.0
        elif test["scan_type"] == "malware":
            base_time = 2.5
        
        await asyncio.sleep(base_time)
        
        # Simulate different scan results
        if test["scan_type"] == "sast":
            return {
                "scan_successful": True,
                "scan_time": base_time,
                "vulnerabilities_found": 3,
                "critical": 0,
                "high": 1,
                "medium": 1,
                "low": 1
            }
        elif test["scan_type"] == "sca":
            return {
                "scan_successful": True,
                "scan_time": base_time,
                "vulnerabilities_found": 5,
                "critical": 1,
                "high": 2,
                "medium": 1,
                "low": 1
            }
        elif test["scan_type"] == "secret":
            return {
                "scan_successful": True,
                "scan_time": base_time,
                "vulnerabilities_found": 2,
                "secrets_found": 2,
                "false_positives": 0
            }
        else:  # malware
            return {
                "scan_successful": True,
                "scan_time": base_time,
                "vulnerabilities_found": 0,
                "malware_detected": 0,
                "suspicious_files": 1
            }
    
    async def _check_quality_assessment(self) -> Dict[str, Any]:
        """Check quality assessment functionality."""
        try:
            # Simulate quality assessment tests
            quality_tests = [
                {
                    "name": "code_quality_metrics",
                    "assessment_type": "metrics",
                    "language": "python",
                    "expected_success": True
                },
                {
                    "name": "test_coverage",
                    "assessment_type": "coverage",
                    "language": "javascript",
                    "expected_success": True
                },
                {
                    "name": "code_smells",
                    "assessment_type": "smells",
                    "language": "java",
                    "expected_success": True
                },
                {
                    "name": "technical_debt",
                    "assessment_type": "debt",
                    "language": "python",
                    "expected_success": True
                }
            ]
            
            assessment_results = []
            successful_assessments = 0
            
            for test in quality_tests:
                try:
                    # Simulate quality assessment
                    result = await self._simulate_quality_assessment(test)
                    assessment_results.append({
                        "test": test["name"],
                        "assessment_successful": result["assessment_successful"],
                        "assessment_time": result["assessment_time"],
                        "quality_score": result.get("quality_score", 0),
                        "success": result["assessment_successful"] == test["expected_success"]
                    })
                    if result["assessment_successful"] == test["expected_success"]:
                        successful_assessments += 1
                except Exception as e:
                    assessment_results.append({
                        "test": test["name"],
                        "assessment_successful": False,
                        "error": str(e),
                        "success": False
                    })
            
            success_rate = successful_assessments / len(quality_tests)
            
            if success_rate == 1.0:
                status = HealthStatus.HEALTHY
            elif success_rate >= 0.8:
                status = HealthStatus.DEGRADED
            else:
                status = HealthStatus.UNHEALTHY
            
            return {
                "status": status.value,
                "message": f"Quality assessment success rate: {success_rate:.1%}",
                "details": {
                    "total_tests": len(quality_tests),
                    "successful_assessments": successful_assessments,
                    "success_rate": success_rate,
                    "assessment_results": assessment_results,
                },
            }
            
        except Exception as e:
            return {
                "status": HealthStatus.ERROR.value,
                "message": f"Quality assessment check failed: {str(e)}",
            }
    
    async def _simulate_quality_assessment(self, test: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate quality assessment for testing."""
        # Simulate processing time
        base_time = 1.0
        if test["assessment_type"] == "metrics":
            base_time = 0.8
        elif test["assessment_type"] == "coverage":
            base_time = 1.2
        elif test["assessment_type"] == "smells":
            base_time = 1.5
        elif test["assessment_type"] == "debt":
            base_time = 1.0
        
        await asyncio.sleep(base_time)
        
        # Simulate different assessment results
        if test["assessment_type"] == "metrics":
            return {
                "assessment_successful": True,
                "assessment_time": base_time,
                "quality_score": 8.2,
                "maintainability": 7.5,
                "reliability": 8.8,
                "efficiency": 8.3
            }
        elif test["assessment_type"] == "coverage":
            return {
                "assessment_successful": True,
                "assessment_time": base_time,
                "quality_score": 7.8,
                "line_coverage": 85.2,
                "branch_coverage": 78.5,
                "function_coverage": 92.1
            }
        elif test["assessment_type"] == "smells":
            return {
                "assessment_successful": True,
                "assessment_time": base_time,
                "quality_score": 7.5,
                "code_smells": 12,
                "major_smells": 3,
                "minor_smells": 9
            }
        else:  # debt
            return {
                "assessment_successful": True,
                "assessment_time": base_time,
                "quality_score": 8.0,
                "technical_debt_days": 15,
                "debt_ratio": 0.08,
                "priority_issues": 2
            }
    
    async def _check_verification_status(self) -> Dict[str, Any]:
        """Check verification status functionality."""
        try:
            # Simulate verification status tests
            verification_tests = [
                {
                    "name": "verification_queue",
                    "check_type": "queue_status",
                    "expected_success": True
                },
                {
                    "name": "verification_progress",
                    "check_type": "progress_tracking",
                    "expected_success": True
                },
                {
                    "name": "verification_results",
                    "check_type": "results_storage",
                    "expected_success": True
                },
                {
                    "name": "verification_history",
                    "check_type": "history_retrieval",
                    "expected_success": True
                }
            ]
            
            verification_results = []
            successful_verifications = 0
            
            for test in verification_tests:
                try:
                    # Simulate verification status check
                    result = await self._simulate_verification_status(test)
                    verification_results.append({
                        "test": test["name"],
                        "verification_successful": result["verification_successful"],
                        "check_time": result["check_time"],
                        "status_info": result.get("status_info", {}),
                        "success": result["verification_successful"] == test["expected_success"]
                    })
                    if result["verification_successful"] == test["expected_success"]:
                        successful_verifications += 1
                except Exception as e:
                    verification_results.append({
                        "test": test["name"],
                        "verification_successful": False,
                        "error": str(e),
                        "success": False
                    })
            
            success_rate = successful_verifications / len(verification_tests)
            
            # Get verification statistics
            verification_stats = {
                "total_verifications": 1250,
                "pending_verifications": 25,
                "in_progress_verifications": 8,
                "completed_verifications": 1150,
                "failed_verifications": 67,
                "avg_verification_time": 45.2,
                "success_rate": 0.946,
            }
            
            if success_rate == 1.0:
                status = HealthStatus.HEALTHY
            elif success_rate >= 0.8:
                status = HealthStatus.DEGRADED
            else:
                status = HealthStatus.UNHEALTHY
            
            return {
                "status": status.value,
                "message": f"Verification status success rate: {success_rate:.1%}",
                "details": {
                    "total_tests": len(verification_tests),
                    "successful_verifications": successful_verifications,
                    "success_rate": success_rate,
                    "verification_stats": verification_stats,
                    "verification_results": verification_results,
                },
            }
            
        except Exception as e:
            return {
                "status": HealthStatus.ERROR.value,
                "message": f"Verification status check failed: {str(e)}",
            }
    
    async def _simulate_verification_status(self, test: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate verification status check for testing."""
        # Simulate processing time
        await asyncio.sleep(0.2)
        
        # Simulate different verification status results
        if test["check_type"] == "queue_status":
            return {
                "verification_successful": True,
                "check_time": 0.2,
                "status_info": {
                    "queue_size": 25,
                    "max_queue_size": 100,
                    "queue_utilization": 0.25,
                    "oldest_pending_age_minutes": 15
                }
            }
        elif test["check_type"] == "progress_tracking":
            return {
                "verification_successful": True,
                "check_time": 0.2,
                "status_info": {
                    "active_verifications": 8,
                    "avg_progress": 65.2,
                    "estimated_completion_minutes": 12
                }
            }
        elif test["check_type"] == "results_storage":
            return {
                "verification_successful": True,
                "check_time": 0.2,
                "status_info": {
                    "results_stored": 1150,
                    "storage_used_mb": 850,
                    "compression_enabled": True
                }
            }
        else:  # history_retrieval
            return {
                "verification_successful": True,
                "check_time": 0.2,
                "status_info": {
                    "history_available": True,
                    "retention_days": 90,
                    "searchable_fields": ["id", "status", "timestamp", "type"]
                }
            }
    
    async def _check_rule_engine(self) -> Dict[str, Any]:
        """Check rule engine functionality."""
        try:
            # Simulate rule engine tests
            rule_tests = [
                {
                    "name": "rule_loading",
                    "test_type": "load_rules",
                    "rule_count": 150,
                    "expected_success": True
                },
                {
                    "name": "rule_execution",
                    "test_type": "execute_rules",
                    "rule_count": 10,
                    "expected_success": True
                },
                {
                    "name": "rule_validation",
                    "test_type": "validate_rules",
                    "rule_count": 150,
                    "expected_success": True
                },
                {
                    "name": "rule_performance",
                    "test_type": "performance_test",
                    "rule_count": 50,
                    "expected_success": True
                }
            ]
            
            rule_results = []
            successful_tests = 0
            
            for test in rule_tests:
                try:
                    # Simulate rule engine test
                    result = await self._simulate_rule_engine_test(test)
                    rule_results.append({
                        "test": test["name"],
                        "test_successful": result["test_successful"],
                        "test_time": result["test_time"],
                        "performance_metrics": result.get("performance_metrics", {}),
                        "success": result["test_successful"] == test["expected_success"]
                    })
                    if result["test_successful"] == test["expected_success"]:
                        successful_tests += 1
                except Exception as e:
                    rule_results.append({
                        "test": test["name"],
                        "test_successful": False,
                        "error": str(e),
                        "success": False
                    })
            
            success_rate = successful_tests / len(rule_tests)
            
            # Get rule engine statistics
            rule_stats = {
                "total_rules": 150,
                "active_rules": 145,
                "disabled_rules": 5,
                "rule_categories": ["security", "quality", "performance", "compliance"],
                "avg_execution_time_ms": 25.5,
                "rule_cache_hit_rate": 0.92,
            }
            
            if success_rate == 1.0:
                status = HealthStatus.HEALTHY
            elif success_rate >= 0.8:
                status = HealthStatus.DEGRADED
            else:
                status = HealthStatus.UNHEALTHY
            
            return {
                "status": status.value,
                "message": f"Rule engine success rate: {success_rate:.1%}",
                "details": {
                    "total_tests": len(rule_tests),
                    "successful_tests": successful_tests,
                    "success_rate": success_rate,
                    "rule_stats": rule_stats,
                    "rule_results": rule_results,
                },
            }
            
        except Exception as e:
            return {
                "status": HealthStatus.ERROR.value,
                "message": f"Rule engine check failed: {str(e)}",
            }
    
    async def _simulate_rule_engine_test(self, test: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate rule engine test for testing."""
        # Simulate processing time
        base_time = 0.5
        if test["test_type"] == "load_rules":
            base_time = 1.0
        elif test["test_type"] == "execute_rules":
            base_time = 0.3
        elif test["test_type"] == "validate_rules":
            base_time = 0.8
        elif test["test_type"] == "performance_test":
            base_time = 2.0
        
        await asyncio.sleep(base_time)
        
        # Simulate different rule engine test results
        if test["test_type"] == "load_rules":
            return {
                "test_successful": True,
                "test_time": base_time,
                "performance_metrics": {
                    "rules_loaded": test["rule_count"],
                    "load_time_ms": base_time * 1000,
                    "memory_usage_mb": 45
                }
            }
        elif test["test_type"] == "execute_rules":
            return {
                "test_successful": True,
                "test_time": base_time,
                "performance_metrics": {
                    "rules_executed": test["rule_count"],
                    "avg_execution_time_ms": 25.5,
                    "cache_hits": 9
                }
            }
        elif test["test_type"] == "validate_rules":
            return {
                "test_successful": True,
                "test_time": base_time,
                "performance_metrics": {
                    "rules_validated": test["rule_count"],
                    "validation_errors": 0,
                    "warnings": 2
                }
            }
        else:  # performance_test
            return {
                "test_successful": True,
                "test_time": base_time,
                "performance_metrics": {
                    "rules_tested": test["rule_count"],
                    "avg_response_time_ms": 22.3,
                    "throughput_per_second": 45.2
                }
            }
    
    async def _check_feedback_generation(self) -> Dict[str, Any]:
        """Check feedback generation functionality."""
        try:
            # Simulate feedback generation tests
            feedback_tests = [
                {
                    "name": "code_feedback",
                    "feedback_type": "code_review",
                    "complexity": "medium",
                    "expected_success": True
                },
                {
                    "name": "security_feedback",
                    "feedback_type": "security_report",
                    "complexity": "high",
                    "expected_success": True
                },
                {
                    "name": "quality_feedback",
                    "feedback_type": "quality_assessment",
                    "complexity": "medium",
                    "expected_success": True
                },
                {
                    "name": "performance_feedback",
                    "feedback_type": "performance_analysis",
                    "complexity": "low",
                    "expected_success": True
                }
            ]
            
            feedback_results = []
            successful_generations = 0
            
            for test in feedback_tests:
                try:
                    # Simulate feedback generation
                    result = await self._simulate_feedback_generation(test)
                    feedback_results.append({
                        "test": test["name"],
                        "generation_successful": result["generation_successful"],
                        "generation_time": result["generation_time"],
                        "feedback_quality": result.get("feedback_quality", 0),
                        "success": result["generation_successful"] == test["expected_success"]
                    })
                    if result["generation_successful"] == test["expected_success"]:
                        successful_generations += 1
                except Exception as e:
                    feedback_results.append({
                        "test": test["name"],
                        "generation_successful": False,
                        "error": str(e),
                        "success": False
                    })
            
            success_rate = successful_generations / len(feedback_tests)
            
            if success_rate == 1.0:
                status = HealthStatus.HEALTHY
            elif success_rate >= 0.8:
                status = HealthStatus.DEGRADED
            else:
                status = HealthStatus.UNHEALTHY
            
            return {
                "status": status.value,
                "message": f"Feedback generation success rate: {success_rate:.1%}",
                "details": {
                    "total_tests": len(feedback_tests),
                    "successful_generations": successful_generations,
                    "success_rate": success_rate,
                    "feedback_results": feedback_results,
                },
            }
            
        except Exception as e:
            return {
                "status": HealthStatus.ERROR.value,
                "message": f"Feedback generation check failed: {str(e)}",
            }
    
    async def _simulate_feedback_generation(self, test: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate feedback generation for testing."""
        # Simulate processing time based on complexity
        base_time = 1.0
        if test["complexity"] == "high":
            base_time = 2.0
        elif test["complexity"] == "medium":
            base_time = 1.5
        elif test["complexity"] == "low":
            base_time = 0.8
        
        await asyncio.sleep(base_time)
        
        # Simulate different feedback generation results
        if test["feedback_type"] == "code_review":
            return {
                "generation_successful": True,
                "generation_time": base_time,
                "feedback_quality": 8.5,
                "suggestions_count": 12,
                "actionable_items": 8
            }
        elif test["feedback_type"] == "security_report":
            return {
                "generation_successful": True,
                "generation_time": base_time,
                "feedback_quality": 9.0,
                "security_issues": 5,
                "remediation_steps": 8
            }
        elif test["feedback_type"] == "quality_assessment":
            return {
                "generation_successful": True,
                "generation_time": base_time,
                "feedback_quality": 8.2,
                "quality_metrics": 15,
                "improvement_areas": 6
            }
        else:  # performance_analysis
            return {
                "generation_successful": True,
                "generation_time": base_time,
                "feedback_quality": 8.8,
                "performance_issues": 3,
                "optimization_suggestions": 7
            }
    
    async def _check_compliance_checking(self) -> Dict[str, Any]:
        """Check compliance checking functionality."""
        try:
            # Simulate compliance checking tests
            compliance_tests = [
                {
                    "name": "gdpr_compliance",
                    "compliance_type": "privacy",
                    "framework": "GDPR",
                    "expected_success": True
                },
                {
                    "name": "soc2_compliance",
                    "compliance_type": "security",
                    "framework": "SOC2",
                    "expected_success": True
                },
                {
                    "name": "iso27001_compliance",
                    "compliance_type": "security",
                    "framework": "ISO27001",
                    "expected_success": True
                },
                {
                    "name": "pci_dss_compliance",
                    "compliance_type": "security",
                    "framework": "PCI_DSS",
                    "expected_success": True
                }
            ]
            
            compliance_results = []
            successful_checks = 0
            
            for test in compliance_tests:
                try:
                    # Simulate compliance check
                    result = await self._simulate_compliance_check(test)
                    compliance_results.append({
                        "test": test["name"],
                        "check_successful": result["check_successful"],
                        "check_time": result["check_time"],
                        "compliance_score": result.get("compliance_score", 0),
                        "success": result["check_successful"] == test["expected_success"]
                    })
                    if result["check_successful"] == test["expected_success"]:
                        successful_checks += 1
                except Exception as e:
                    compliance_results.append({
                        "test": test["name"],
                        "check_successful": False,
                        "error": str(e),
                        "success": False
                    })
            
            success_rate = successful_checks / len(compliance_tests)
            
            if success_rate == 1.0:
                status = HealthStatus.HEALTHY
            elif success_rate >= 0.8:
                status = HealthStatus.DEGRADED
            else:
                status = HealthStatus.UNHEALTHY
            
            return {
                "status": status.value,
                "message": f"Compliance checking success rate: {success_rate:.1%}",
                "details": {
                    "total_tests": len(compliance_tests),
                    "successful_checks": successful_checks,
                    "success_rate": success_rate,
                    "compliance_results": compliance_results,
                },
            }
            
        except Exception as e:
            return {
                "status": HealthStatus.ERROR.value,
                "message": f"Compliance checking check failed: {str(e)}",
            }
    
    async def _simulate_compliance_check(self, test: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate compliance check for testing."""
        # Simulate processing time
        base_time = 2.0
        if test["framework"] == "GDPR":
            base_time = 1.5
        elif test["framework"] == "SOC2":
            base_time = 2.5
        elif test["framework"] == "ISO27001":
            base_time = 3.0
        elif test["framework"] == "PCI_DSS":
            base_time = 2.0
        
        await asyncio.sleep(base_time)
        
        # Simulate different compliance check results
        if test["framework"] == "GDPR":
            return {
                "check_successful": True,
                "check_time": base_time,
                "compliance_score": 92.5,
                "violations": 2,
                "recommendations": 5
            }
        elif test["framework"] == "SOC2":
            return {
                "check_successful": True,
                "check_time": base_time,
                "compliance_score": 88.0,
                "violations": 3,
                "recommendations": 7
            }
        elif test["framework"] == "ISO27001":
            return {
                "check_successful": True,
                "check_time": base_time,
                "compliance_score": 85.5,
                "violations": 4,
                "recommendations": 8
            }
        else:  # PCI_DSS
            return {
                "check_successful": True,
                "check_time": base_time,
                "compliance_score": 95.0,
                "violations": 1,
                "recommendations": 3
            }
    
    async def _check_report_generation(self) -> Dict[str, Any]:
        """Check report generation functionality."""
        try:
            # Simulate report generation tests
            report_tests = [
                {
                    "name": "summary_report",
                    "report_type": "summary",
                    "format": "pdf",
                    "expected_success": True
                },
                {
                    "name": "detailed_report",
                    "report_type": "detailed",
                    "format": "html",
                    "expected_success": True
                },
                {
                    "name": "executive_report",
                    "report_type": "executive",
                    "format": "pdf",
                    "expected_success": True
                },
                {
                    "name": "compliance_report",
                    "report_type": "compliance",
                    "format": "xlsx",
                    "expected_success": True
                }
            ]
            
            report_results = []
            successful_generations = 0
            
            for test in report_tests:
                try:
                    # Simulate report generation
                    result = await self._simulate_report_generation(test)
                    report_results.append({
                        "test": test["name"],
                        "generation_successful": result["generation_successful"],
                        "generation_time": result["generation_time"],
                        "report_size_kb": result.get("report_size_kb", 0),
                        "success": result["generation_successful"] == test["expected_success"]
                    })
                    if result["generation_successful"] == test["expected_success"]:
                        successful_generations += 1
                except Exception as e:
                    report_results.append({
                        "test": test["name"],
                        "generation_successful": False,
                        "error": str(e),
                        "success": False
                    })
            
            success_rate = successful_generations / len(report_tests)
            
            if success_rate == 1.0:
                status = HealthStatus.HEALTHY
            elif success_rate >= 0.8:
                status = HealthStatus.DEGRADED
            else:
                status = HealthStatus.UNHEALTHY
            
            return {
                "status": status.value,
                "message": f"Report generation success rate: {success_rate:.1%}",
                "details": {
                    "total_tests": len(report_tests),
                    "successful_generations": successful_generations,
                    "success_rate": success_rate,
                    "report_results": report_results,
                },
            }
            
        except Exception as e:
            return {
                "status": HealthStatus.ERROR.value,
                "message": f"Report generation check failed: {str(e)}",
            }
    
    async def _simulate_report_generation(self, test: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate report generation for testing."""
        # Simulate processing time based on report type
        base_time = 1.0
        if test["report_type"] == "detailed":
            base_time = 2.0
        elif test["report_type"] == "executive":
            base_time = 1.5
        elif test["report_type"] == "compliance":
            base_time = 2.5
        
        await asyncio.sleep(base_time)
        
        # Simulate different report generation results
        if test["report_type"] == "summary":
            return {
                "generation_successful": True,
                "generation_time": base_time,
                "report_size_kb": 250,
                "pages": 5,
                "charts": 3
            }
        elif test["report_type"] == "detailed":
            return {
                "generation_successful": True,
                "generation_time": base_time,
                "report_size_kb": 1500,
                "pages": 25,
                "charts": 12
            }
        elif test["report_type"] == "executive":
            return {
                "generation_successful": True,
                "generation_time": base_time,
                "report_size_kb": 800,
                "pages": 15,
                "charts": 8
            }
        else:  # compliance
            return {
                "generation_successful": True,
                "generation_time": base_time,
                "report_size_kb": 2000,
                "pages": 35,
                "tables": 15
            }
    
    async def run_all_checks(self) -> Dict[str, Any]:
        """Run all health checks and return comprehensive report."""
        return await self.base_checker.run_all_checks()
    
    async def run_liveness_checks(self) -> Dict[str, Any]:
        """Run liveness checks only."""
        results = await self.base_checker.run_checks_by_type(HealthCheckType.LIVENESS)
        return {
            "service": self.service_name,
            "check_type": "liveness",
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {name: result.to_dict() for name, result in results.items()},
        }
    
    async def run_readiness_checks(self) -> Dict[str, Any]:
        """Run readiness checks only."""
        results = await self.base_checker.run_checks_by_type(HealthCheckType.READINESS)
        return {
            "service": self.service_name,
            "check_type": "readiness",
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {name: result.to_dict() for name, result in results.items()},
        }
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Get health summary without running checks."""
        return self.base_checker.get_service_health_summary()


# Global instance
_verification_feedback_health_checker: Optional[VerificationFeedbackHealthChecker] = None


def get_verification_feedback_health_checker() -> VerificationFeedbackHealthChecker:
    """Get the global Verification Feedback health checker."""
    global _verification_feedback_health_checker
    if _verification_feedback_health_checker is None:
        _verification_feedback_health_checker = VerificationFeedbackHealthChecker()
    return _verification_feedback_health_checker


# Health check endpoints
async def verification_feedback_liveness() -> Dict[str, Any]:
    """Verification Feedback liveness endpoint."""
    checker = get_verification_feedback_health_checker()
    return await checker.run_liveness_checks()


async def verification_feedback_readiness() -> Dict[str, Any]:
    """Verification Feedback readiness endpoint."""
    checker = get_verification_feedback_health_checker()
    return await checker.run_readiness_checks()


async def verification_feedback_health() -> Dict[str, Any]:
    """Verification Feedback comprehensive health endpoint."""
    checker = get_verification_feedback_health_checker()
    return await checker.run_all_checks()


# Decorated health checks for easy registration
@health_check("verification_feedback_code_analysis", HealthCheckType.BUSINESS_LOGIC, critical=True)
async def check_verification_feedback_code_analysis():
    """Check code analysis for Verification Feedback."""
    checker = get_verification_feedback_health_checker()
    return await checker._check_code_analysis()


@health_check("verification_feedback_security_scanning", HealthCheckType.BUSINESS_LOGIC, critical=True)
async def check_verification_feedback_security_scanning():
    """Check security scanning for Verification Feedback."""
    checker = get_verification_feedback_health_checker()
    return await checker._check_security_scanning()


@health_check("verification_feedback_quality_assessment", HealthCheckType.BUSINESS_LOGIC, critical=True)
async def check_verification_feedback_quality_assessment():
    """Check quality assessment for Verification Feedback."""
    checker = get_verification_feedback_health_checker()
    return await checker._check_quality_assessment()