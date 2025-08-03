"""
Git Worktree Manager service-specific tracing instrumentation.
Provides custom spans and metrics for Git operations, worktree management, and merge operations.
"""

import logging
from typing import Dict, Any, Optional, List
from contextlib import asynccontextmanager
import time
import subprocess

from opentelemetry import trace, metrics
from opentelemetry.trace import Status, StatusCode, SpanKind
from opentelemetry.semconv.trace import SpanAttributes
from src.common.tracing import (
    TracingUtils, 
    traced, 
    TraceContextManager,
    get_tracing_config,
    get_instrumentation_manager
)

logger = logging.getLogger(__name__)


class GitWorktreeTracing:
    """Tracing instrumentation specific to Git Worktree operations."""
    
    def __init__(self):
        self.tracer = None
        self.meter = None
        self._initialize_metrics()
    
    def _initialize_metrics(self):
        """Initialize metrics for git worktree operations."""
        config = get_tracing_config()
        self.tracer = config.get_tracer()
        self.meter = config.get_meter()
        
        # Create metrics
        self.worktree_creation_counter = self.meter.create_counter(
            "git_worktree_creations_total",
            description="Total number of worktrees created"
        )
        
        self.worktree_deletion_counter = self.meter.create_counter(
            "git_worktree_deletions_total",
            description="Total number of worktrees deleted"
        )
        
        self.worktree_operation_duration = self.meter.create_histogram(
            "git_worktree_operation_duration_seconds",
            description="Duration of worktree operations"
        )
        
        self.git_operation_counter = self.meter.create_counter(
            "git_operations_total",
            description="Total number of Git operations"
        )
        
        self.git_operation_duration = self.meter.create_histogram(
            "git_operation_duration_seconds",
            description="Duration of Git operations"
        )
        
        self.merge_operation_counter = self.meter.create_counter(
            "git_merge_operations_total",
            description="Total number of merge operations"
        )
        
        self.merge_conflict_counter = self.meter.create_counter(
            "git_merge_conflicts_total",
            description="Total number of merge conflicts"
        )
        
        self.sync_operation_counter = self.meter.create_counter(
            "git_sync_operations_total",
            description="Total number of sync operations"
        )
        
        self.git_error_counter = self.meter.create_counter(
            "git_errors_total",
            description="Total number of Git errors"
        )
        
        self.worktree_lock_counter = self.meter.create_counter(
            "git_worktree_locks_total",
            description="Total number of worktree lock operations"
        )
    
    @asynccontextmanager
    async def trace_worktree_creation(self, repo_name: str, branch_name: str, worktree_path: str):
        """Trace worktree creation process."""
        span_name = "git_worktree.create_worktree"
        attributes = {
            "git_worktree.repo_name": repo_name,
            "git_worktree.branch_name": branch_name,
            "git_worktree.worktree_path": worktree_path
        }
        
        with self.tracer.start_as_current_span(span_name, attributes=attributes) as span:
            start_time = time.time()
            try:
                yield span
                duration = time.time() - start_time
                self.worktree_operation_duration.record(duration, {"operation": "create"})
                self.worktree_creation_counter.add(1)
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                self.git_error_counter.add(1, {
                    "operation": "create_worktree",
                    "error_type": type(e).__name__
                })
                raise
    
    @asynccontextmanager
    async def trace_worktree_deletion(self, worktree_id: str, force: bool = False):
        """Trace worktree deletion process."""
        span_name = "git_worktree.delete_worktree"
        attributes = {
            "git_worktree.worktree_id": worktree_id,
            "git_worktree.force_delete": force
        }
        
        with self.tracer.start_as_current_span(span_name, attributes=attributes) as span:
            start_time = time.time()
            try:
                yield span
                duration = time.time() - start_time
                self.worktree_operation_duration.record(duration, {"operation": "delete"})
                self.worktree_deletion_counter.add(1, {"force": force})
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                self.git_error_counter.add(1, {
                    "operation": "delete_worktree",
                    "error_type": type(e).__name__
                })
                raise
    
    @asynccontextmanager
    async def trace_git_operation(self, operation: str, repo_name: str, 
                                command: List[str], worktree_id: str = None):
        """Trace Git command execution."""
        span_name = f"git_worktree.git_{operation}"
        attributes = {
            "git_worktree.operation": operation,
            "git_worktree.repo_name": repo_name,
            "git_worktree.command": " ".join(command)
        }
        
        if worktree_id:
            attributes["git_worktree.worktree_id"] = worktree_id
        
        with self.tracer.start_as_current_span(span_name, attributes=attributes) as span:
            start_time = time.time()
            try:
                yield span
                duration = time.time() - start_time
                self.git_operation_duration.record(duration, {"operation": operation})
                self.git_operation_counter.add(1, {"operation": operation})
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                self.git_error_counter.add(1, {
                    "operation": f"git_{operation}",
                    "error_type": type(e).__name__
                })
                raise
    
    @asynccontextmanager
    async def trace_merge_operation(self, worktree_id: str, source_branch: str, 
                                  target_branch: str, strategy: str = "merge"):
        """Trace merge operation."""
        span_name = "git_worktree.merge_operation"
        attributes = {
            "git_worktree.worktree_id": worktree_id,
            "git_worktree.source_branch": source_branch,
            "git_worktree.target_branch": target_branch,
            "git_worktree.merge_strategy": strategy
        }
        
        with self.tracer.start_as_current_span(span_name, attributes=attributes) as span:
            start_time = time.time()
            conflict_count = 0
            try:
                yield span
                duration = time.time() - start_time
                self.git_operation_duration.record(duration, {"operation": "merge"})
                self.merge_operation_counter.add(1, {"strategy": strategy})
                
                # Record conflict count if available
                if conflict_count > 0:
                    self.merge_conflict_counter.add(conflict_count)
                    span.set_attribute("git_worktree.conflict_count", conflict_count)
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                
                # Check if it's a merge conflict error
                if "conflict" in str(e).lower():
                    self.merge_conflict_counter.add(1)
                    span.set_attribute("git_worktree.merge_conflict", True)
                
                self.git_error_counter.add(1, {
                    "operation": "merge",
                    "error_type": type(e).__name__
                })
                raise
    
    @asynccontextmanager
    async def trace_sync_operation(self, repo_name: str, sync_type: str = "full"):
        """Trace worktree sync operation."""
        span_name = "git_worktree.sync_worktrees"
        attributes = {
            "git_worktree.repo_name": repo_name,
            "git_worktree.sync_type": sync_type
        }
        
        with self.tracer.start_as_current_span(span_name, attributes=attributes) as span:
            start_time = time.time()
            try:
                yield span
                duration = time.time() - start_time
                self.git_operation_duration.record(duration, {"operation": "sync"})
                self.sync_operation_counter.add(1, {"sync_type": sync_type})
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                self.git_error_counter.add(1, {
                    "operation": "sync",
                    "error_type": type(e).__name__
                })
                raise
    
    @asynccontextmanager
    async def trace_worktree_lock(self, worktree_id: str, operation: str, reason: str = ""):
        """Trace worktree lock/unlock operations."""
        span_name = f"git_worktree.{operation}_lock"
        attributes = {
            "git_worktree.worktree_id": worktree_id,
            "git_worktree.lock_operation": operation,
            "git_worktree.lock_reason": reason
        }
        
        with self.tracer.start_as_current_span(span_name, attributes=attributes) as span:
            try:
                yield span
                self.worktree_lock_counter.add(1, {"operation": operation})
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                self.git_error_counter.add(1, {
                    "operation": f"{operation}_lock",
                    "error_type": type(e).__name__
                })
                raise
    
    def record_git_command_metrics(self, operation: str, duration: float, 
                                 success: bool, repo_name: str = None):
        """Record Git command execution metrics."""
        self.git_operation_duration.record(duration, {"operation": operation})
        self.git_operation_counter.add(1, {
            "operation": operation,
            "success": success
        })
        
        if not success:
            self.git_error_counter.add(1, {
                "operation": operation,
                "repo_name": repo_name or "unknown"
            })
    
    def record_worktree_metrics(self, operation: str, duration: float, 
                              repo_name: str, worktree_count: int = None):
        """Record worktree operation metrics."""
        self.worktree_operation_duration.record(duration, {"operation": operation})
        
        if worktree_count is not None:
            self.git_operation_counter.add(1, {
                "operation": operation,
                "repo_name": repo_name,
                "worktree_count": worktree_count
            })
    
    def record_merge_metrics(self, duration: float, conflict_count: int, 
                           success: bool, strategy: str = "merge"):
        """Record merge operation metrics."""
        self.git_operation_duration.record(duration, {"operation": "merge"})
        self.merge_operation_counter.add(1, {
            "strategy": strategy,
            "success": success
        })
        
        if conflict_count > 0:
            self.merge_conflict_counter.add(conflict_count)
    
    def add_worktree_attributes(self, span, worktree_id: str, repo_name: str, 
                               branch_name: str, worktree_path: str):
        """Add worktree attributes to span."""
        span.set_attribute("git_worktree.worktree_id", worktree_id)
        span.set_attribute("git_worktree.repo_name", repo_name)
        span.set_attribute("git_worktree.branch_name", branch_name)
        span.set_attribute("git_worktree.worktree_path", worktree_path)
    
    def add_git_command_attributes(self, span, operation: str, command: List[str], 
                                 exit_code: int, output_lines: int):
        """Add Git command attributes to span."""
        span.set_attribute("git_worktree.operation", operation)
        span.set_attribute("git_worktree.command", " ".join(command))
        span.set_attribute("git_worktree.exit_code", exit_code)
        span.set_attribute("git_worktree.output_lines", output_lines)
    
    def add_merge_attributes(self, span, worktree_id: str, source_branch: str, 
                           target_branch: str, conflict_count: int):
        """Add merge operation attributes to span."""
        span.set_attribute("git_worktree.worktree_id", worktree_id)
        span.set_attribute("git_worktree.source_branch", source_branch)
        span.set_attribute("git_worktree.target_branch", target_branch)
        span.set_attribute("git_worktree.conflict_count", conflict_count)
    
    def add_error_attributes(self, span, error_type: str, error_message: str, 
                           operation: str = None, worktree_id: str = None):
        """Add error attributes to span."""
        span.set_attribute("error.type", error_type)
        span.set_attribute("error.message", error_message)
        if operation:
            span.set_attribute("git_worktree.operation", operation)
        if worktree_id:
            span.set_attribute("git_worktree.worktree_id", worktree_id)


# Decorators for git worktree operations
def trace_worktree_operation(operation_name: str = None):
    """Decorator to trace worktree operations."""
    def decorator(func):
        name = operation_name or f"git_worktree.{func.__name__}"
        
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


def trace_git_command(operation_name: str = None):
    """Decorator to trace Git command execution."""
    def decorator(func):
        name = operation_name or f"git_worktree.git.{func.__name__}"
        
        async def async_wrapper(*args, **kwargs):
            tracer = get_tracing_config().get_tracer()
            with tracer.start_as_current_span(name, kind=SpanKind.INTERNAL) as span:
                start_time = time.time()
                try:
                    result = await func(*args, **kwargs)
                    duration = time.time() - start_time
                    
                    # Record metrics
                    git_tracing = GitWorktreeTracing()
                    git_tracing.git_operation_duration.record(duration, {"operation": name})
                    git_tracing.git_operation_counter.add(1, {"operation": name})
                    
                    span.set_status(Status(StatusCode.OK))
                    span.set_attribute("git_worktree.duration_ms", duration * 1000)
                    
                    return result
                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    git_tracing = GitWorktreeTracing()
                    git_tracing.git_error_counter.add(1, {
                        "operation": name,
                        "error_type": type(e).__name__
                    })
                    raise
        
        if hasattr(func, '__call__') and hasattr(func, '__code__') and func.__code__.co_flags & 0x80:
            return async_wrapper
        return func
    
    return decorator


def trace_merge_operation(operation_name: str = None):
    """Decorator to trace merge operations."""
    def decorator(func):
        name = operation_name or f"git_worktree.merge.{func.__name__}"
        
        async def async_wrapper(*args, **kwargs):
            tracer = get_tracing_config().get_tracer()
            with tracer.start_as_current_span(name, kind=SpanKind.INTERNAL) as span:
                start_time = time.time()
                try:
                    result = await func(*args, **kwargs)
                    duration = time.time() - start_time
                    
                    # Record metrics
                    git_tracing = GitWorktreeTracing()
                    git_tracing.git_operation_duration.record(duration, {"operation": "merge"})
                    git_tracing.merge_operation_counter.add(1)
                    
                    span.set_status(Status(StatusCode.OK))
                    span.set_attribute("git_worktree.duration_ms", duration * 1000)
                    
                    return result
                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    
                    # Check for merge conflicts
                    if "conflict" in str(e).lower():
                        git_tracing = GitWorktreeTracing()
                        git_tracing.merge_conflict_counter.add(1)
                        span.set_attribute("git_worktree.merge_conflict", True)
                    
                    git_tracing = GitWorktreeTracing()
                    git_tracing.git_error_counter.add(1, {
                        "operation": "merge",
                        "error_type": type(e).__name__
                    })
                    raise
        
        if hasattr(func, '__call__') and hasattr(func, '__code__') and func.__code__.co_flags & 0x80:
            return async_wrapper
        return func
    
    return decorator


# Global instance
git_worktree_tracing = GitWorktreeTracing()


def get_git_worktree_tracing() -> GitWorktreeTracing:
    """Get the global git worktree tracing instance."""
    return git_worktree_tracing


def initialize_git_worktree_tracing():
    """Initialize git worktree tracing."""
    config = get_tracing_config()
    config.initialize("git-worktree-manager")
    
    # Instrument database clients
    manager = get_instrumentation_manager()
    manager.instrument_database()
    
    logger.info("Git worktree tracing initialized")