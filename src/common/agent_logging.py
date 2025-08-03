"""
Agent-specific logging utilities for MCP services.
Provides specialized logging patterns for different agent types and operations.
"""

import logging
import time
import json
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from contextlib import contextmanager, asynccontextmanager
import uuid

from .logging_config import get_logger, log_operation
from .logging_filters import (
    get_trace_filter, get_service_filter, get_sensitive_filter,
    get_request_filter, get_performance_filter,
    set_request_context, clear_request_context,
    start_operation_timing, end_operation_timing
)

logger = get_logger(__name__)


class AgentLogger:
    """Base class for agent-specific logging."""
    
    def __init__(self, agent_name: str, agent_type: str = "unknown"):
        self.agent_name = agent_name
        self.agent_type = agent_type
        self.logger = get_logger(agent_name)
        self.operation_stack = []
    
    def _log_with_context(self, level: str, message: str, **context):
        """Log a message with agent-specific context."""
        # Add agent context
        agent_context = {
            'agent_name': self.agent_name,
            'agent_type': self.agent_type,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            **context
        }
        
        # Add current operation context if available
        if self.operation_stack:
            agent_context['current_operation'] = self.operation_stack[-1]
        
        # Log with appropriate level
        if level == 'debug':
            self.logger.debug(message, **agent_context)
        elif level == 'info':
            self.logger.info(message, **agent_context)
        elif level == 'warning':
            self.logger.warning(message, **agent_context)
        elif level == 'error':
            self.logger.error(message, **agent_context)
        elif level == 'critical':
            self.logger.critical(message, **agent_context)
    
    def debug(self, message: str, **context):
        """Log a debug message."""
        self._log_with_context('debug', message, **context)
    
    def info(self, message: str, **context):
        """Log an info message."""
        self._log_with_context('info', message, **context)
    
    def warning(self, message: str, **context):
        """Log a warning message."""
        self._log_with_context('warning', message, **context)
    
    def error(self, message: str, **context):
        """Log an error message."""
        self._log_with_context('error', message, **context)
    
    def critical(self, message: str, **context):
        """Log a critical message."""
        self._log_with_context('critical', message, **context)
    
    def exception(self, message: str, **context):
        """Log an exception with traceback."""
        context['exception'] = True
        self.logger.exception(message, **context)
    
    @contextmanager
    def operation(self, operation_name: str, **context):
        """Context manager for agent operations with timing."""
        self.operation_stack.append(operation_name)
        start_time = time.time()
        
        self.info(f"Starting operation: {operation_name}", operation=operation_name, **context)
        start_operation_timing()
        
        try:
            yield
        except Exception as e:
            duration = time.time() - start_time
            self.error(f"Operation failed: {operation_name}", 
                     operation=operation_name,
                     duration_seconds=duration,
                     error=str(e),
                     **context)
            raise
        else:
            duration = time.time() - start_time
            self.info(f"Operation completed: {operation_name}", 
                     operation=operation_name,
                     duration_seconds=duration,
                     **context)
        finally:
            self.operation_stack.pop()
            end_operation_timing()
    
    @asynccontextmanager
    async def async_operation(self, operation_name: str, **context):
        """Async context manager for agent operations with timing."""
        self.operation_stack.append(operation_name)
        start_time = time.time()
        
        self.info(f"Starting async operation: {operation_name}", operation=operation_name, **context)
        start_operation_timing()
        
        try:
            yield
        except Exception as e:
            duration = time.time() - start_time
            self.error(f"Async operation failed: {operation_name}", 
                     operation=operation_name,
                     duration_seconds=duration,
                     error=str(e),
                     **context)
            raise
        else:
            duration = time.time() - start_time
            self.info(f"Async operation completed: {operation_name}", 
                     operation=operation_name,
                     duration_seconds=duration,
                     **context)
        finally:
            self.operation_stack.pop()
            end_operation_timing()


class ModelRouterLogger(AgentLogger):
    """Logger for Model Router agent."""
    
    def __init__(self):
        super().__init__("model-router", "router")
    
    def log_model_selection(self, request_id: str, selected_model: str, 
                           available_models: List[str], selection_reason: str,
                           confidence_score: float = None):
        """Log model selection event."""
        self.info("Model selected", 
                 request_id=request_id,
                 selected_model=selected_model,
                 available_models=available_models,
                 selection_reason=selection_reason,
                 confidence_score=confidence_score,
                 event_type="model_selection")
    
    def log_request_routing(self, request_id: str, source_service: str, 
                           target_model: str, routing_strategy: str):
        """Log request routing event."""
        self.info("Request routed", 
                 request_id=request_id,
                 source_service=source_service,
                 target_model=target_model,
                 routing_strategy=routing_strategy,
                 event_type="request_routing")
    
    def log_response_aggregation(self, request_id: str, model_responses: int,
                               aggregation_strategy: str, response_time: float):
        """Log response aggregation event."""
        self.info("Response aggregated", 
                 request_id=request_id,
                 model_responses=model_responses,
                 aggregation_strategy=aggregation_strategy,
                 response_time=response_time,
                 event_type="response_aggregation")
    
    def log_model_health_check(self, model_name: str, health_status: str,
                             response_time: float, error_message: str = None):
        """Log model health check event."""
        level = "error" if health_status != "healthy" else "info"
        self._log_with_context(level, "Model health check",
                             model_name=model_name,
                             health_status=health_status,
                             response_time=response_time,
                             error_message=error_message,
                             event_type="model_health_check")


class PlanManagementLogger(AgentLogger):
    """Logger for Plan Management agent."""
    
    def __init__(self):
        super().__init__("plan-management", "planner")
    
    def log_task_decomposition(self, plan_id: str, original_task: str,
                             decomposed_tasks: List[str], decomposition_strategy: str):
        """Log task decomposition event."""
        self.info("Task decomposed", 
                 plan_id=plan_id,
                 original_task=original_task,
                 decomposed_tasks=decomposed_tasks,
                 decomposition_strategy=decomposition_strategy,
                 task_count=len(decomposed_tasks),
                 event_type="task_decomposition")
    
    def log_consensus_building(self, plan_id: str, consensus_type: str,
                              participants: List[str], consensus_reached: bool,
                              consensus_score: float = None):
        """Log consensus building event."""
        level = "warning" if not consensus_reached else "info"
        self._log_with_context(level, "Consensus building",
                             plan_id=plan_id,
                             consensus_type=consensus_type,
                             participants=participants,
                             consensus_reached=consensus_reached,
                             consensus_score=consensus_score,
                             event_type="consensus_building")
    
    def log_plan_validation(self, plan_id: str, validation_result: str,
                           validation_score: float, issues_found: List[str]):
        """Log plan validation event."""
        level = "error" if validation_result == "failed" else "info"
        self._log_with_context(level, "Plan validation",
                             plan_id=plan_id,
                             validation_result=validation_result,
                             validation_score=validation_score,
                             issues_found=issues_found,
                             issues_count=len(issues_found),
                             event_type="plan_validation")
    
    def log_plan_backup(self, plan_id: str, backup_location: str,
                       backup_size: int, backup_duration: float):
        """Log plan backup event."""
        self.info("Plan backed up", 
                 plan_id=plan_id,
                 backup_location=backup_location,
                 backup_size=backup_size,
                 backup_duration=backup_duration,
                 event_type="plan_backup")


class GitWorktreeLogger(AgentLogger):
    """Logger for Git Worktree Manager agent."""
    
    def __init__(self):
        super().__init__("git-worktree-manager", "git")
    
    def log_git_operation(self, operation: str, repository: str, 
                         branch: str, operation_duration: float,
                         success: bool, error_message: str = None):
        """Log git operation event."""
        level = "error" if not success else "info"
        self._log_with_context(level, "Git operation",
                             operation=operation,
                             repository=repository,
                             branch=branch,
                             operation_duration=operation_duration,
                             success=success,
                             error_message=error_message,
                             event_type="git_operation")
    
    def log_worktree_creation(self, repository: str, worktree_path: str,
                            base_branch: str, creation_duration: float):
        """Log worktree creation event."""
        self.info("Worktree created", 
                 repository=repository,
                 worktree_path=worktree_path,
                 base_branch=base_branch,
                 creation_duration=creation_duration,
                 event_type="worktree_creation")
    
    def log_merge_operation(self, repository: str, source_branch: str,
                           target_branch: str, merge_result: str,
                           merge_duration: float, conflicts: List[str] = None):
        """Log merge operation event."""
        level = "warning" if merge_result != "success" else "info"
        self._log_with_context(level, "Merge operation",
                             repository=repository,
                             source_branch=source_branch,
                             target_branch=target_branch,
                             merge_result=merge_result,
                             merge_duration=merge_duration,
                             conflicts=conflicts,
                             conflict_count=len(conflicts) if conflicts else 0,
                             event_type="merge_operation")
    
    def log_cleanup_operation(self, operation: str, items_cleaned: int,
                            space_freed: int, cleanup_duration: float):
        """Log cleanup operation event."""
        self.info("Cleanup operation", 
                 operation=operation,
                 items_cleaned=items_cleaned,
                 space_freed=space_freed,
                 cleanup_duration=cleanup_duration,
                 event_type="cleanup_operation")


class WorkflowOrchestratorLogger(AgentLogger):
    """Logger for Workflow Orchestrator agent."""
    
    def __init__(self):
        super().__init__("workflow-orchestrator", "orchestrator")
    
    def log_workflow_execution(self, workflow_id: str, workflow_type: str,
                             total_steps: int, execution_duration: float,
                             success: bool, failed_steps: List[str] = None):
        """Log workflow execution event."""
        level = "error" if not success else "info"
        self._log_with_context(level, "Workflow execution",
                             workflow_id=workflow_id,
                             workflow_type=workflow_type,
                             total_steps=total_steps,
                             execution_duration=execution_duration,
                             success=success,
                             failed_steps=failed_steps,
                             failed_step_count=len(failed_steps) if failed_steps else 0,
                             event_type="workflow_execution")
    
    def log_step_coordination(self, workflow_id: str, step_name: str,
                            step_type: str, assigned_agent: str,
                            coordination_duration: float):
        """Log step coordination event."""
        self.info("Step coordinated", 
                 workflow_id=workflow_id,
                 step_name=step_name,
                 step_type=step_type,
                 assigned_agent=assigned_agent,
                 coordination_duration=coordination_duration,
                 event_type="step_coordination")
    
    def log_error_recovery(self, workflow_id: str, step_name: str,
                          error_type: str, recovery_action: str,
                          recovery_successful: bool, recovery_duration: float):
        """Log error recovery event."""
        level = "error" if not recovery_successful else "warning"
        self._log_with_context(level, "Error recovery",
                             workflow_id=workflow_id,
                             step_name=step_name,
                             error_type=error_type,
                             recovery_action=recovery_action,
                             recovery_successful=recovery_successful,
                             recovery_duration=recovery_duration,
                             event_type="error_recovery")
    
    def log_agent_handoff(self, workflow_id: str, from_agent: str,
                        to_agent: str, handoff_reason: str,
                        handoff_duration: float):
        """Log agent handoff event."""
        self.info("Agent handoff", 
                 workflow_id=workflow_id,
                 from_agent=from_agent,
                 to_agent=to_agent,
                 handoff_reason=handoff_reason,
                 handoff_duration=handoff_duration,
                 event_type="agent_handoff")


class VerificationFeedbackLogger(AgentLogger):
    """Logger for Verification Feedback agent."""
    
    def __init__(self):
        super().__init__("verification-feedback", "verifier")
    
    def log_code_analysis(self, analysis_id: str, file_path: str,
                        analysis_type: str, analysis_duration: float,
                        issues_found: List[Dict[str, Any]]):
        """Log code analysis event."""
        severity_level = "error" if any(issue.get('severity') == 'critical' for issue in issues_found) else "info"
        self._log_with_context(severity_level, "Code analysis",
                             analysis_id=analysis_id,
                             file_path=file_path,
                             analysis_type=analysis_type,
                             analysis_duration=analysis_duration,
                             issues_found=issues_found,
                             issue_count=len(issues_found),
                             event_type="code_analysis")
    
    def log_security_scanning(self, scan_id: str, target: str,
                            scan_type: str, scan_duration: float,
                            vulnerabilities_found: List[Dict[str, Any]]):
        """Log security scanning event."""
        severity_level = "critical" if any(vuln.get('severity') == 'critical' for vuln in vulnerabilities_found) else "warning"
        self._log_with_context(severity_level, "Security scan",
                             scan_id=scan_id,
                             target=target,
                             scan_type=scan_type,
                             scan_duration=scan_duration,
                             vulnerabilities_found=vulnerabilities_found,
                             vulnerability_count=len(vulnerabilities_found),
                             event_type="security_scanning")
    
    def log_quality_assessment(self, assessment_id: str, target: str,
                             assessment_type: str, quality_score: float,
                             assessment_duration: float, metrics: Dict[str, float]):
        """Log quality assessment event."""
        level = "warning" if quality_score < 0.7 else "info"
        self._log_with_context(level, "Quality assessment",
                             assessment_id=assessment_id,
                             target=target,
                             assessment_type=assessment_type,
                             quality_score=quality_score,
                             assessment_duration=assessment_duration,
                             metrics=metrics,
                             event_type="quality_assessment")
    
    def log_verification_report(self, report_id: str, target: str,
                               overall_score: float, verification_duration: float,
                               recommendations: List[str]):
        """Log verification report event."""
        level = "warning" if overall_score < 0.8 else "info"
        self._log_with_context(level, "Verification report",
                             report_id=report_id,
                             target=target,
                             overall_score=overall_score,
                             verification_duration=verification_duration,
                             recommendations=recommendations,
                             recommendation_count=len(recommendations),
                             event_type="verification_report")


class LLMOperationLogger(AgentLogger):
    """Logger for LLM operations across all agents."""
    
    def __init__(self, agent_name: str = "llm-operations"):
        super().__init__(agent_name, "llm")
    
    def log_model_call(self, model_name: str, operation: str, 
                      prompt_length: int, response_length: int,
                      duration: float, token_usage: Dict[str, int] = None,
                      success: bool = True, error_message: str = None):
        """Log LLM model call event."""
        level = "error" if not success else "info"
        self._log_with_context(level, "LLM model call",
                             model_name=model_name,
                             operation=operation,
                             prompt_length=prompt_length,
                             response_length=response_length,
                             duration=duration,
                             token_usage=token_usage,
                             success=success,
                             error_message=error_message,
                             event_type="llm_model_call")
    
    def log_token_usage(self, model_name: str, prompt_tokens: int,
                       completion_tokens: int, total_tokens: int,
                       cost_estimate: float = None):
        """Log token usage event."""
        self.info("Token usage", 
                 model_name=model_name,
                 prompt_tokens=prompt_tokens,
                 completion_tokens=completion_tokens,
                 total_tokens=total_tokens,
                 cost_estimate=cost_estimate,
                 event_type="token_usage")
    
    def log_model_performance(self, model_name: str, response_time: float,
                            throughput: float, error_rate: float,
                            context_window_usage: float):
        """Log model performance metrics."""
        level = "warning" if error_rate > 0.1 or response_time > 10.0 else "info"
        self._log_with_context(level, "Model performance",
                             model_name=model_name,
                             response_time=response_time,
                             throughput=throughput,
                             error_rate=error_rate,
                             context_window_usage=context_window_usage,
                             event_type="model_performance")


class CollaborationLogger(AgentLogger):
    """Logger for agent collaboration workflows."""
    
    def __init__(self):
        super().__init__("collaboration", "workflow")
    
    def log_collaboration_start(self, collaboration_id: str, collaboration_type: str,
                              participants: List[str], task_description: str):
        """Log collaboration start event."""
        self.info("Collaboration started", 
                 collaboration_id=collaboration_id,
                 collaboration_type=collaboration_type,
                 participants=participants,
                 participant_count=len(participants),
                 task_description=task_description,
                 event_type="collaboration_start")
    
    def log_message_exchange(self, collaboration_id: str, from_agent: str,
                           to_agent: str, message_type: str, message_content: str):
        """Log message exchange event."""
        self.info("Message exchanged", 
                 collaboration_id=collaboration_id,
                 from_agent=from_agent,
                 to_agent=to_agent,
                 message_type=message_type,
                 message_content=message_content,
                 event_type="message_exchange")
    
    def log_consensus_reached(self, collaboration_id: str, consensus_type: str,
                            final_decision: str, confidence_score: float,
                            participation_rate: float):
        """Log consensus reached event."""
        self.info("Consensus reached", 
                 collaboration_id=collaboration_id,
                 consensus_type=consensus_type,
                 final_decision=final_decision,
                 confidence_score=confidence_score,
                 participation_rate=participation_rate,
                 event_type="consensus_reached")
    
    def log_collaboration_end(self, collaboration_id: str, result: str,
                            duration: float, success: bool):
        """Log collaboration end event."""
        level = "error" if not success else "info"
        self._log_with_context(level, "Collaboration ended",
                             collaboration_id=collaboration_id,
                             result=result,
                             duration=duration,
                             success=success,
                             event_type="collaboration_end")


# Factory function to get appropriate logger
def get_agent_logger(agent_name: str) -> AgentLogger:
    """Get the appropriate logger for an agent."""
    if agent_name == "model-router":
        return ModelRouterLogger()
    elif agent_name == "plan-management":
        return PlanManagementLogger()
    elif agent_name == "git-worktree-manager":
        return GitWorktreeLogger()
    elif agent_name == "workflow-orchestrator":
        return WorkflowOrchestratorLogger()
    elif agent_name == "verification-feedback":
        return VerificationFeedbackLogger()
    else:
        return AgentLogger(agent_name)


def get_llm_logger(agent_name: str = None) -> LLMOperationLogger:
    """Get LLM operation logger."""
    return LLMOperationLogger(agent_name)


def get_collaboration_logger() -> CollaborationLogger:
    """Get collaboration logger."""
    return CollaborationLogger()


# Convenience functions for common logging patterns
def log_agent_operation(agent_name: str, operation: str, **context):
    """Log an agent operation with timing."""
    logger = get_agent_logger(agent_name)
    return logger.operation(operation, **context)


def log_llm_call(model_name: str, operation: str, prompt_length: int,
                response_length: int, duration: float, **context):
    """Log an LLM call."""
    logger = get_llm_logger()
    logger.log_model_call(model_name, operation, prompt_length, response_length,
                         duration, **context)


def log_collaboration_event(collaboration_type: str, event_type: str, **context):
    """Log a collaboration event."""
    logger = get_collaboration_logger()
    getattr(logger, f"log_{event_type}")(collaboration_type, **context)