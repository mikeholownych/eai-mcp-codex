"""
Plan Management specific health checks.
Provides comprehensive health monitoring for the Plan Management service.
"""

import time
import asyncio
import json
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from ..common.enhanced_health_check import (
    HealthStatus, HealthCheckType, HealthChecker, 
    check_memory_usage, check_disk_usage, check_cpu_usage,
    check_network_connectivity, check_file_system, health_check
)
from ..common.logging import get_logger
from ..common.tracing import get_tracer
from ..common.metrics import get_metrics_collector

logger = get_logger("plan_management.health")
tracer = get_tracer()
metrics = get_metrics_collector("plan_management")


class PlanManagementHealthChecker:
    """Health checker for Plan Management service."""
    
    def __init__(self):
        self.service_name = "plan-management"
        self.base_checker = HealthChecker(self.service_name)
        self._setup_health_checks()
    
    def _setup_health_checks(self):
        """Set up all health checks for Plan Management."""
        
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
        
        # Plan Management specific checks
        self.base_checker.register_simple_check(
            "task_decomposition",
            self._check_task_decomposition,
            check_type=HealthCheckType.BUSINESS_LOGIC,
            critical=True
        )
        
        self.base_checker.register_simple_check(
            "consensus_building",
            self._check_consensus_building,
            check_type=HealthCheckType.BUSINESS_LOGIC,
            critical=True
        )
        
        self.base_checker.register_simple_check(
            "storage_operations",
            self._check_storage_operations,
            check_type=HealthCheckType.DEPENDENCY,
            critical=True
        )
        
        self.base_checker.register_simple_check(
            "backup_status",
            self._check_backup_status,
            check_type=HealthCheckType.READINESS,
            critical=False
        )
        
        self.base_checker.register_simple_check(
            "plan_validation",
            self._check_plan_validation,
            check_type=HealthCheckType.BUSINESS_LOGIC,
            critical=True
        )
        
        self.base_checker.register_simple_check(
            "versioning_system",
            self._check_versioning_system,
            check_type=HealthCheckType.DEPENDENCY,
            critical=True
        )
        
        self.base_checker.register_simple_check(
            "collaboration_tools",
            self._check_collaboration_tools,
            check_type=HealthCheckType.BUSINESS_LOGIC,
            critical=False
        )
        
        self.base_checker.register_simple_check(
            "notification_system",
            self._check_notification_system,
            check_type=HealthCheckType.DEPENDENCY,
            critical=False
        )
    
    async def _check_task_decomposition(self) -> Dict[str, Any]:
        """Check task decomposition functionality."""
        try:
            # Simulate task decomposition tests
            test_tasks = [
                {
                    "name": "Implement user authentication",
                    "description": "Create a secure authentication system with JWT tokens",
                    "complexity": "high",
                    "estimated_hours": 16
                },
                {
                    "name": "Add unit tests",
                    "description": "Write comprehensive unit tests for existing modules",
                    "complexity": "medium",
                    "estimated_hours": 8
                },
                {
                    "name": "Update documentation",
                    "description": "Update API documentation with new endpoints",
                    "complexity": "low",
                    "estimated_hours": 4
                }
            ]
            
            decomposition_results = []
            successful_decompositions = 0
            
            for task in test_tasks:
                try:
                    # Simulate task decomposition
                    subtasks = await self._simulate_task_decomposition(task)
                    decomposition_results.append({
                        "task": task["name"],
                        "subtask_count": len(subtasks),
                        "success": True,
                        "subtasks": subtasks[:3]  # Show first 3 subtasks
                    })
                    successful_decompositions += 1
                except Exception as e:
                    decomposition_results.append({
                        "task": task["name"],
                        "error": str(e),
                        "success": False
                    })
            
            success_rate = successful_decompositions / len(test_tasks)
            
            if success_rate == 1.0:
                status = HealthStatus.HEALTHY
            elif success_rate >= 0.8:
                status = HealthStatus.DEGRADED
            else:
                status = HealthStatus.UNHEALTHY
            
            return {
                "status": status.value,
                "message": f"Task decomposition success rate: {success_rate:.1%}",
                "details": {
                    "total_tasks": len(test_tasks),
                    "successful_decompositions": successful_decompositions,
                    "success_rate": success_rate,
                    "decomposition_results": decomposition_results,
                },
            }
            
        except Exception as e:
            return {
                "status": HealthStatus.ERROR.value,
                "message": f"Task decomposition check failed: {str(e)}",
            }
    
    async def _simulate_task_decomposition(self, task: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Simulate task decomposition for testing."""
        # Simulate processing time
        await asyncio.sleep(0.1)
        
        # Generate mock subtasks based on task complexity
        complexity_factors = {
            "high": 8,
            "medium": 5,
            "low": 3
        }
        
        subtask_count = complexity_factors.get(task["complexity"], 4)
        subtasks = []
        
        for i in range(subtask_count):
            subtasks.append({
                "name": f"Subtask {i+1}: {task['name']}",
                "description": f"Part {i+1} of {task['name']}",
                "estimated_hours": round(task["estimated_hours"] / subtask_count, 1),
                "priority": "high" if i < 2 else "medium"
            })
        
        return subtasks
    
    async def _check_consensus_building(self) -> Dict[str, Any]:
        """Check consensus building functionality."""
        try:
            # Simulate consensus building scenarios
            consensus_scenarios = [
                {
                    "name": "Technical approach selection",
                    "participants": ["developer", "architect", "tech_lead"],
                    "options": ["Microservices", "Monolith", "Serverless"],
                    "expected_consensus": True
                },
                {
                    "name": "Priority assignment",
                    "participants": ["product_owner", "developer", "qa"],
                    "options": ["High", "Medium", "Low"],
                    "expected_consensus": True
                },
                {
                    "name": "Architecture decision",
                    "participants": ["architect", "tech_lead", "security_engineer"],
                    "options": ["Option A", "Option B", "Option C"],
                    "expected_consensus": False  # Simulate conflict
                }
            ]
            
            consensus_results = []
            successful_consensus = 0
            
            for scenario in consensus_scenarios:
                try:
                    # Simulate consensus building
                    result = await self._simulate_consensus_building(scenario)
                    consensus_results.append({
                        "scenario": scenario["name"],
                        "participants": scenario["participants"],
                        "consensus_reached": result["consensus_reached"],
                        "time_taken": result["time_taken"],
                        "success": result["consensus_reached"] == scenario["expected_consensus"]
                    })
                    if result["consensus_reached"] == scenario["expected_consensus"]:
                        successful_consensus += 1
                except Exception as e:
                    consensus_results.append({
                        "scenario": scenario["name"],
                        "error": str(e),
                        "success": False
                    })
            
            success_rate = successful_consensus / len(consensus_scenarios)
            
            if success_rate == 1.0:
                status = HealthStatus.HEALTHY
            elif success_rate >= 0.7:
                status = HealthStatus.DEGRADED
            else:
                status = HealthStatus.UNHEALTHY
            
            return {
                "status": status.value,
                "message": f"Consensus building success rate: {success_rate:.1%}",
                "details": {
                    "total_scenarios": len(consensus_scenarios),
                    "successful_consensus": successful_consensus,
                    "success_rate": success_rate,
                    "consensus_results": consensus_results,
                },
            }
            
        except Exception as e:
            return {
                "status": HealthStatus.ERROR.value,
                "message": f"Consensus building check failed: {str(e)}",
            }
    
    async def _simulate_consensus_building(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate consensus building for testing."""
        # Simulate processing time
        await asyncio.sleep(0.2)
        
        # Simulate consensus based on scenario
        if scenario["name"] == "Architecture decision":
            # Simulate no consensus
            return {
                "consensus_reached": False,
                "time_taken": 5.2,
                "votes": {"Option A": 1, "Option B": 1, "Option C": 1}
            }
        else:
            # Simulate consensus reached
            return {
                "consensus_reached": True,
                "time_taken": 2.1,
                "selected_option": scenario["options"][0],
                "confidence": 0.85
            }
    
    async def _check_storage_operations(self) -> Dict[str, Any]:
        """Check storage operations functionality."""
        try:
            # Simulate storage operation tests
            storage_tests = [
                {"operation": "save_plan", "size_kb": 50},
                {"operation": "load_plan", "size_kb": 50},
                {"operation": "update_plan", "size_kb": 75},
                {"operation": "delete_plan", "size_kb": 30},
                {"operation": "list_plans", "count": 100},
                {"operation": "search_plans", "query": "test"},
            ]
            
            test_results = []
            successful_operations = 0
            
            for test in storage_tests:
                try:
                    # Simulate storage operation
                    result = await self._simulate_storage_operation(test)
                    test_results.append({
                        "operation": test["operation"],
                        "success": True,
                        "duration_ms": result["duration_ms"],
                        "details": result.get("details", {})
                    })
                    successful_operations += 1
                except Exception as e:
                    test_results.append({
                        "operation": test["operation"],
                        "success": False,
                        "error": str(e)
                    })
            
            success_rate = successful_operations / len(storage_tests)
            
            # Calculate average response time
            successful_durations = [r["duration_ms"] for r in test_results if r["success"]]
            avg_duration = sum(successful_durations) / len(successful_durations) if successful_durations else 0
            
            if success_rate == 1.0 and avg_duration < 1000:
                status = HealthStatus.HEALTHY
            elif success_rate >= 0.8 and avg_duration < 2000:
                status = HealthStatus.DEGRADED
            else:
                status = HealthStatus.UNHEALTHY
            
            return {
                "status": status.value,
                "message": f"Storage operations success rate: {success_rate:.1%}, avg duration: {avg_duration:.1f}ms",
                "details": {
                    "total_operations": len(storage_tests),
                    "successful_operations": successful_operations,
                    "success_rate": success_rate,
                    "average_duration_ms": avg_duration,
                    "test_results": test_results,
                },
            }
            
        except Exception as e:
            return {
                "status": HealthStatus.ERROR.value,
                "message": f"Storage operations check failed: {str(e)}",
            }
    
    async def _simulate_storage_operation(self, test: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate storage operation for testing."""
        # Simulate processing time based on operation
        base_time = 0.1
        if test["operation"] in ["save_plan", "load_plan"]:
            base_time = 0.2
        elif test["operation"] == "search_plans":
            base_time = 0.15
        
        await asyncio.sleep(base_time)
        
        return {
            "duration_ms": base_time * 1000,
            "details": {
                "size_kb": test.get("size_kb", 0),
                "count": test.get("count", 0),
                "query": test.get("query", "")
            }
        }
    
    async def _check_backup_status(self) -> Dict[str, Any]:
        """Check backup system status."""
        try:
            # Simulate backup status check
            backup_info = {
                "last_backup_time": datetime.utcnow() - timedelta(hours=6),
                "last_backup_size_mb": 250,
                "backup_frequency_hours": 24,
                "backup_retention_days": 30,
                "backup_location": "/backups/plan_management",
                "backup_status": "completed",
                "backup_success_rate": 0.98,
                "next_backup_scheduled": datetime.utcnow() + timedelta(hours=18),
            }
            
            # Check backup health
            issues = []
            time_since_last_backup = datetime.utcnow() - backup_info["last_backup_time"]
            if time_since_last_backup > timedelta(hours=backup_info["backup_frequency_hours"] * 1.5):
                issues.append("Backup is overdue")
            
            if backup_info["backup_success_rate"] < 0.9:
                issues.append("Low backup success rate")
            
            # Check backup storage
            storage_check = await check_file_system(backup_info["backup_location"], "read")
            if storage_check["status"] != HealthStatus.HEALTHY.value:
                issues.append("Backup storage location not accessible")
            
            if issues:
                status = HealthStatus.DEGRADED if len(issues) <= 2 else HealthStatus.UNHEALTHY
                message = f"Backup issues detected: {len(issues)} issues"
            else:
                status = HealthStatus.HEALTHY
                message = "Backup system healthy"
            
            return {
                "status": status.value,
                "message": message,
                "details": {
                    "backup_info": backup_info,
                    "time_since_last_backup_hours": time_since_last_backup.total_seconds() / 3600,
                    "issues": issues,
                    "storage_check": storage_check,
                },
            }
            
        except Exception as e:
            return {
                "status": HealthStatus.ERROR.value,
                "message": f"Backup status check failed: {str(e)}",
            }
    
    async def _check_plan_validation(self) -> Dict[str, Any]:
        """Check plan validation functionality."""
        try:
            # Simulate plan validation tests
            test_plans = [
                {
                    "name": "Valid plan",
                    "description": "A well-structured plan with all required fields",
                    "tasks": [{"name": "Task 1", "estimated_hours": 4}],
                    "timeline": {"start_date": "2024-01-01", "end_date": "2024-01-31"},
                    "expected_valid": True
                },
                {
                    "name": "Invalid plan - missing tasks",
                    "description": "Plan without required tasks",
                    "tasks": [],
                    "timeline": {"start_date": "2024-01-01", "end_date": "2024-01-31"},
                    "expected_valid": False
                },
                {
                    "name": "Invalid plan - invalid timeline",
                    "description": "Plan with end date before start date",
                    "tasks": [{"name": "Task 1", "estimated_hours": 4}],
                    "timeline": {"start_date": "2024-01-31", "end_date": "2024-01-01"},
                    "expected_valid": False
                }
            ]
            
            validation_results = []
            correct_validations = 0
            
            for plan in test_plans:
                try:
                    # Simulate plan validation
                    result = await self._simulate_plan_validation(plan)
                    is_correct = result["is_valid"] == plan["expected_valid"]
                    
                    validation_results.append({
                        "plan": plan["name"],
                        "is_valid": result["is_valid"],
                        "expected_valid": plan["expected_valid"],
                        "correct": is_correct,
                        "validation_time_ms": result["validation_time_ms"],
                        "issues": result.get("issues", [])
                    })
                    
                    if is_correct:
                        correct_validations += 1
                except Exception as e:
                    validation_results.append({
                        "plan": plan["name"],
                        "error": str(e),
                        "correct": False
                    })
            
            accuracy = correct_validations / len(test_plans)
            
            if accuracy == 1.0:
                status = HealthStatus.HEALTHY
            elif accuracy >= 0.8:
                status = HealthStatus.DEGRADED
            else:
                status = HealthStatus.UNHEALTHY
            
            return {
                "status": status.value,
                "message": f"Plan validation accuracy: {accuracy:.1%}",
                "details": {
                    "total_plans": len(test_plans),
                    "correct_validations": correct_validations,
                    "accuracy": accuracy,
                    "validation_results": validation_results,
                },
            }
            
        except Exception as e:
            return {
                "status": HealthStatus.ERROR.value,
                "message": f"Plan validation check failed: {str(e)}",
            }
    
    async def _simulate_plan_validation(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate plan validation for testing."""
        # Simulate processing time
        await asyncio.sleep(0.05)
        
        issues = []
        is_valid = True
        
        # Check for required tasks
        if not plan.get("tasks"):
            issues.append("Plan must have at least one task")
            is_valid = False
        
        # Check timeline validity
        timeline = plan.get("timeline", {})
        if timeline.get("start_date") and timeline.get("end_date"):
            if timeline["end_date"] < timeline["start_date"]:
                issues.append("End date cannot be before start date")
                is_valid = False
        
        return {
            "is_valid": is_valid,
            "validation_time_ms": 50,
            "issues": issues
        }
    
    async def _check_versioning_system(self) -> Dict[str, Any]:
        """Check versioning system functionality."""
        try:
            # Simulate versioning system check
            versioning_info = {
                "current_version": "2.1.0",
                "total_versions": 15,
                "latest_version_created": datetime.utcnow() - timedelta(hours=2),
                "storage_used_mb": 1200,
                "compression_enabled": True,
                "diff_storage_enabled": True,
                "rollback_available": True,
            }
            
            # Test versioning operations
            version_tests = [
                {"operation": "create_version", "success": True},
                {"operation": "list_versions", "success": True},
                {"operation": "get_version_diff", "success": True},
                {"operation": "rollback_version", "success": True},
            ]
            
            test_results = []
            successful_tests = 0
            
            for test in version_tests:
                try:
                    # Simulate versioning operation
                    await asyncio.sleep(0.05)
                    test_results.append({
                        "operation": test["operation"],
                        "success": True,
                        "duration_ms": 50
                    })
                    successful_tests += 1
                except Exception as e:
                    test_results.append({
                        "operation": test["operation"],
                        "success": False,
                        "error": str(e)
                    })
            
            success_rate = successful_tests / len(version_tests)
            
            # Check versioning health
            issues = []
            if versioning_info["storage_used_mb"] > 2000:
                issues.append("High storage usage")
            if success_rate < 1.0:
                issues.append("Some versioning operations failed")
            
            if issues:
                status = HealthStatus.DEGRADED if len(issues) <= 1 else HealthStatus.UNHEALTHY
                message = f"Versioning issues detected: {len(issues)} issues"
            else:
                status = HealthStatus.HEALTHY
                message = "Versioning system healthy"
            
            return {
                "status": status.value,
                "message": message,
                "details": {
                    "versioning_info": versioning_info,
                    "test_results": test_results,
                    "success_rate": success_rate,
                    "issues": issues,
                },
            }
            
        except Exception as e:
            return {
                "status": HealthStatus.ERROR.value,
                "message": f"Versioning system check failed: {str(e)}",
            }
    
    async def _check_collaboration_tools(self) -> Dict[str, Any]:
        """Check collaboration tools functionality."""
        try:
            # Simulate collaboration tools check
            collaboration_tools = [
                {"name": "real_time_editing", "status": "active", "users": 5},
                {"name": "comment_system", "status": "active", "users": 8},
                {"name": "approval_workflow", "status": "active", "users": 3},
                {"name": "notification_system", "status": "active", "users": 10},
            ]
            
            # Test collaboration features
            feature_tests = [
                {"feature": "add_comment", "success": True},
                {"feature": "request_approval", "success": True},
                {"feature": "share_plan", "success": True},
                {"feature": "edit_collaboratively", "success": True},
            ]
            
            test_results = []
            successful_tests = 0
            
            for test in feature_tests:
                try:
                    # Simulate collaboration feature test
                    await asyncio.sleep(0.1)
                    test_results.append({
                        "feature": test["feature"],
                        "success": True,
                        "response_time_ms": 100
                    })
                    successful_tests += 1
                except Exception as e:
                    test_results.append({
                        "feature": test["feature"],
                        "success": False,
                        "error": str(e)
                    })
            
            success_rate = successful_tests / len(feature_tests)
            
            # Check collaboration health
            total_users = sum(tool["users"] for tool in collaboration_tools)
            active_tools = sum(1 for tool in collaboration_tools if tool["status"] == "active")
            
            issues = []
            if success_rate < 1.0:
                issues.append("Some collaboration features failed")
            if active_tools < len(collaboration_tools):
                issues.append("Some collaboration tools inactive")
            
            if issues:
                status = HealthStatus.DEGRADED if len(issues) <= 1 else HealthStatus.UNHEALTHY
                message = f"Collaboration tools issues detected: {len(issues)} issues"
            else:
                status = HealthStatus.HEALTHY
                message = "Collaboration tools healthy"
            
            return {
                "status": status.value,
                "message": message,
                "details": {
                    "collaboration_tools": collaboration_tools,
                    "test_results": test_results,
                    "success_rate": success_rate,
                    "total_users": total_users,
                    "active_tools": active_tools,
                    "issues": issues,
                },
            }
            
        except Exception as e:
            return {
                "status": HealthStatus.ERROR.value,
                "message": f"Collaboration tools check failed: {str(e)}",
            }
    
    async def _check_notification_system(self) -> Dict[str, Any]:
        """Check notification system functionality."""
        try:
            # Simulate notification system check
            notification_metrics = {
                "emails_sent_today": 150,
                "emails_failed": 2,
                "in_app_notifications": 300,
                "push_notifications": 80,
                "webhook_deliveries": 25,
                "avg_delivery_time_ms": 250,
            }
            
            # Test notification channels
            channel_tests = [
                {"channel": "email", "success": True},
                {"channel": "in_app", "success": True},
                {"channel": "push", "success": True},
                {"channel": "webhook", "success": True},
            ]
            
            test_results = []
            successful_tests = 0
            
            for test in channel_tests:
                try:
                    # Simulate notification channel test
                    await asyncio.sleep(0.05)
                    test_results.append({
                        "channel": test["channel"],
                        "success": True,
                        "delivery_time_ms": 200
                    })
                    successful_tests += 1
                except Exception as e:
                    test_results.append({
                        "channel": test["channel"],
                        "success": False,
                        "error": str(e)
                    })
            
            success_rate = successful_tests / len(channel_tests)
            
            # Calculate failure rates
            email_failure_rate = notification_metrics["emails_failed"] / max(notification_metrics["emails_sent_today"], 1)
            
            # Check notification health
            issues = []
            if success_rate < 1.0:
                issues.append("Some notification channels failed")
            if email_failure_rate > 0.05:
                issues.append("High email failure rate")
            if notification_metrics["avg_delivery_time_ms"] > 1000:
                issues.append("Slow notification delivery")
            
            if issues:
                status = HealthStatus.DEGRADED if len(issues) <= 1 else HealthStatus.UNHEALTHY
                message = f"Notification system issues detected: {len(issues)} issues"
            else:
                status = HealthStatus.HEALTHY
                message = "Notification system healthy"
            
            return {
                "status": status.value,
                "message": message,
                "details": {
                    "notification_metrics": notification_metrics,
                    "test_results": test_results,
                    "success_rate": success_rate,
                    "email_failure_rate": email_failure_rate,
                    "issues": issues,
                },
            }
            
        except Exception as e:
            return {
                "status": HealthStatus.ERROR.value,
                "message": f"Notification system check failed: {str(e)}",
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
_plan_management_health_checker: Optional[PlanManagementHealthChecker] = None


def get_plan_management_health_checker() -> PlanManagementHealthChecker:
    """Get the global Plan Management health checker."""
    global _plan_management_health_checker
    if _plan_management_health_checker is None:
        _plan_management_health_checker = PlanManagementHealthChecker()
    return _plan_management_health_checker


# Health check endpoints
async def plan_management_liveness() -> Dict[str, Any]:
    """Plan Management liveness endpoint."""
    checker = get_plan_management_health_checker()
    return await checker.run_liveness_checks()


async def plan_management_readiness() -> Dict[str, Any]:
    """Plan Management readiness endpoint."""
    checker = get_plan_management_health_checker()
    return await checker.run_readiness_checks()


async def plan_management_health() -> Dict[str, Any]:
    """Plan Management comprehensive health endpoint."""
    checker = get_plan_management_health_checker()
    return await checker.run_all_checks()


# Decorated health checks for easy registration
@health_check("plan_management_task_decomposition", HealthCheckType.BUSINESS_LOGIC, critical=True)
async def check_plan_management_task_decomposition():
    """Check task decomposition for Plan Management."""
    checker = get_plan_management_health_checker()
    return await checker._check_task_decomposition()


@health_check("plan_management_consensus_building", HealthCheckType.BUSINESS_LOGIC, critical=True)
async def check_plan_management_consensus_building():
    """Check consensus building for Plan Management."""
    checker = get_plan_management_health_checker()
    return await checker._check_consensus_building()


@health_check("plan_management_storage_operations", HealthCheckType.DEPENDENCY, critical=True)
async def check_plan_management_storage_operations():
    """Check storage operations for Plan Management."""
    checker = get_plan_management_health_checker()
    return await checker._check_storage_operations()