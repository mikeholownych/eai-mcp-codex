"""
Git Worktree Application Performance Monitoring (APM) implementation.
Provides comprehensive performance monitoring for repository operations, worktree management, and merge operations.
"""

import logging
import time
import asyncio
import os
import subprocess
from typing import Dict, Any, Optional, List, Union, Tuple
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import statistics
import json

from opentelemetry import trace, metrics
from opentelemetry.trace import Status, StatusCode, SpanKind
from opentelemetry.semconv.trace import SpanAttributes

from src.common.apm import (
    APMInstrumentation, 
    APMOperationType, 
    APMConfig, 
    PerformanceMetrics,
    get_apm
)
from src.common.tracing import get_tracing_config

logger = logging.getLogger(__name__)


class GitWorktreeOperationType(Enum):
    """Git Worktree specific operation types."""
    REPOSITORY_CLONE = "repository_clone"
    REPOSITORY_FETCH = "repository_fetch"
    WORKTREE_CREATE = "worktree_create"
    WORKTREE_REMOVE = "worktree_remove"
    WORKTREE_SWITCH = "worktree_switch"
    BRANCH_CREATE = "branch_create"
    BRANCH_DELETE = "branch_delete"
    BRANCH_MERGE = "branch_merge"
    COMMIT_CREATE = "commit_create"
    COMMIT_PUSH = "commit_push"
    CONFLICT_RESOLUTION = "conflict_resolution"
    FILE_OPERATION = "file_operation"
    STATUS_CHECK = "status_check"
    DIFF_OPERATION = "diff_operation"


@dataclass
class RepositoryMetrics:
    """Repository-specific performance metrics."""
    repository_url: str
    clone_duration: float = 0.0
    fetch_duration: float = 0.0
    total_commits: int = 0
    total_branches: int = 0
    total_worktrees: int = 0
    repository_size: int = 0  # bytes
    last_accessed: float = 0.0
    operation_count: int = 0
    error_count: int = 0
    
    @property
    def error_rate(self) -> float:
        """Calculate error rate."""
        if self.operation_count == 0:
            return 0.0
        return self.error_count / self.operation_count


@dataclass
class WorktreeMetrics:
    """Worktree-specific performance metrics."""
    worktree_path: str
    repository_url: str
    branch_name: str
    creation_duration: float = 0.0
    switch_duration: float = 0.0
    file_count: int = 0
    size_bytes: int = 0
    last_accessed: float = 0.0
    operation_count: int = 0
    error_count: int = 0
    
    @property
    def error_rate(self) -> float:
        """Calculate error rate."""
        if self.operation_count == 0:
            return 0.0
        return self.error_count / self.operation_count


@dataclass
class MergeMetrics:
    """Merge operation metrics."""
    merge_id: str
    repository_url: str
    source_branch: str
    target_branch: str
    duration: float
    success: bool
    conflicts_count: int
    files_changed: int
    insertions: int
    deletions: int
    conflict_resolution_duration: float = 0.0
    strategy_used: str = "merge"
    error_message: Optional[str] = None


@dataclass
class FileOperationMetrics:
    """File operation metrics."""
    operation_type: str
    file_path: str
    worktree_path: str
    duration: float
    success: bool
    file_size: int = 0
    error_message: Optional[str] = None


class GitWorktreeAPM:
    """APM implementation for Git Worktree service."""
    
    def __init__(self, config: APMConfig = None):
        """Initialize Git Worktree APM."""
        self.config = config or APMConfig()
        self.apm = get_apm()
        self.tracer = get_tracing_config().get_tracer()
        self.meter = get_tracing_config().get_meter()
        
        # Performance tracking
        self.repository_metrics = defaultdict(lambda: RepositoryMetrics(repository_url=""))
        self.worktree_metrics = defaultdict(lambda: WorktreeMetrics(worktree_path="", repository_url="", branch_name=""))
        self.merge_metrics = []
        self.file_operation_metrics = []
        
        # Initialize metrics
        self._initialize_metrics()
        
        # Performance thresholds
        self.slow_clone_threshold = 60.0  # seconds
        self.slow_fetch_threshold = 30.0  # seconds
        self.slow_merge_threshold = 45.0  # seconds
        self.high_conflict_threshold = 10  # conflicts
        self.large_file_threshold = 10 * 1024 * 1024  # 10MB
        
        # History limits
        self.max_merge_history = 1000
        self.max_file_operation_history = 5000
    
    def _initialize_metrics(self):
        """Initialize OpenTelemetry metrics for Git Worktree."""
        # Counters
        self.repository_operations_counter = self.meter.create_counter(
            "git_worktree_repository_operations_total",
            description="Total number of repository operations"
        )
        
        self.worktree_operations_counter = self.meter.create_counter(
            "git_worktree_worktree_operations_total",
            description="Total number of worktree operations"
        )
        
        self.merge_operations_counter = self.meter.create_counter(
            "git_worktree_merge_operations_total",
            description="Total number of merge operations"
        )
        
        self.conflict_counter = self.meter.create_counter(
            "git_worktree_conflicts_total",
            description="Total number of merge conflicts"
        )
        
        self.file_operations_counter = self.meter.create_counter(
            "git_worktree_file_operations_total",
            description="Total number of file operations"
        )
        
        # Histograms
        self.clone_duration = self.meter.create_histogram(
            "git_worktree_clone_duration_seconds",
            description="Duration of repository clone operations"
        )
        
        self.fetch_duration = self.meter.create_histogram(
            "git_worktree_fetch_duration_seconds",
            description="Duration of repository fetch operations"
        )
        
        self.worktree_operation_duration = self.meter.create_histogram(
            "git_worktree_operation_duration_seconds",
            description="Duration of worktree operations"
        )
        
        self.merge_duration = self.meter.create_histogram(
            "git_worktree_merge_duration_seconds",
            description="Duration of merge operations"
        )
        
        self.conflict_resolution_duration = self.meter.create_histogram(
            "git_worktree_conflict_resolution_duration_seconds",
            description="Duration of conflict resolution operations"
        )
        
        self.file_operation_duration = self.meter.create_histogram(
            "git_worktree_file_operation_duration_seconds",
            description="Duration of file operations"
        )
        
        # Gauges
        self.active_repositories_gauge = self.meter.create_up_down_counter(
            "git_worktree_active_repositories",
            description="Number of currently active repositories"
        )
        
        self.active_worktrees_gauge = self.meter.create_up_down_counter(
            "git_worktree_active_worktrees",
            description="Number of currently active worktrees"
        )
        
        self.repository_size_gauge = self.meter.create_up_down_counter(
            "git_worktree_repository_size_bytes",
            description="Size of repositories in bytes"
        )
    
    @asynccontextmanager
    async def trace_repository_clone(self, repository_url: str, destination_path: str,
                                   depth: int = 0, branch: str = None):
        """Trace repository clone operation."""
        operation_name = "clone_repository"
        attributes = {
            "git.repository_url": repository_url,
            "git.destination_path": destination_path,
            "git.clone_depth": depth,
            "git.clone_branch": branch
        }
        
        start_time = time.time()
        success = True
        error_message = None
        repository_size = 0
        
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
                
                # Record repository metrics
                repo_metrics = self.repository_metrics[repository_url]
                repo_metrics.repository_url = repository_url
                repo_metrics.clone_duration = duration
                repo_metrics.repository_size = repository_size
                repo_metrics.last_accessed = end_time
                repo_metrics.operation_count += 1
                if not success:
                    repo_metrics.error_count += 1
                
                # Update metrics
                self.repository_operations_counter.add(1, {
                    "operation": "clone",
                    "success": success
                })
                
                self.clone_duration.record(duration, {
                    "repository_url": repository_url
                })
                
                self.repository_size_gauge.add(repository_size, {
                    "repository_url": repository_url
                })
    
    @asynccontextmanager
    async def trace_repository_fetch(self, repository_url: str, remote: str = "origin",
                                   prune: bool = False):
        """Trace repository fetch operation."""
        operation_name = "fetch_repository"
        attributes = {
            "git.repository_url": repository_url,
            "git.remote": remote,
            "git.prune": prune
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
                
                # Record repository metrics
                repo_metrics = self.repository_metrics[repository_url]
                repo_metrics.repository_url = repository_url
                repo_metrics.fetch_duration = duration
                repo_metrics.last_accessed = end_time
                repo_metrics.operation_count += 1
                if not success:
                    repo_metrics.error_count += 1
                
                # Update metrics
                self.repository_operations_counter.add(1, {
                    "operation": "fetch",
                    "success": success
                })
                
                self.fetch_duration.record(duration, {
                    "repository_url": repository_url
                })
    
    @asynccontextmanager
    async def trace_worktree_create(self, repository_url: str, worktree_path: str,
                                  branch_name: str, force: bool = False):
        """Trace worktree creation operation."""
        operation_name = "create_worktree"
        attributes = {
            "git.repository_url": repository_url,
            "git.worktree_path": worktree_path,
            "git.branch_name": branch_name,
            "git.force": force
        }
        
        start_time = time.time()
        success = True
        error_message = None
        file_count = 0
        
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
                
                # Record worktree metrics
                worktree_key = f"{repository_url}#{worktree_path}"
                worktree_metrics = self.worktree_metrics[worktree_key]
                worktree_metrics.worktree_path = worktree_path
                worktree_metrics.repository_url = repository_url
                worktree_metrics.branch_name = branch_name
                worktree_metrics.creation_duration = duration
                worktree_metrics.file_count = file_count
                worktree_metrics.last_accessed = end_time
                worktree_metrics.operation_count += 1
                if not success:
                    worktree_metrics.error_count += 1
                
                # Update metrics
                self.worktree_operations_counter.add(1, {
                    "operation": "create",
                    "success": success
                })
                
                self.worktree_operation_duration.record(duration, {
                    "repository_url": repository_url,
                    "operation": "create"
                })
    
    @asynccontextmanager
    async def trace_worktree_remove(self, worktree_path: str, repository_url: str):
        """Trace worktree removal operation."""
        operation_name = "remove_worktree"
        attributes = {
            "git.worktree_path": worktree_path,
            "git.repository_url": repository_url
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
                
                # Update metrics
                self.worktree_operations_counter.add(1, {
                    "operation": "remove",
                    "success": success
                })
                
                self.worktree_operation_duration.record(duration, {
                    "repository_url": repository_url,
                    "operation": "remove"
                })
    
    @asynccontextmanager
    async def trace_worktree_switch(self, worktree_path: str, branch_name: str,
                                 repository_url: str):
        """Trace worktree switch operation."""
        operation_name = "switch_worktree"
        attributes = {
            "git.worktree_path": worktree_path,
            "git.branch_name": branch_name,
            "git.repository_url": repository_url
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
                
                # Record worktree metrics
                worktree_key = f"{repository_url}#{worktree_path}"
                worktree_metrics = self.worktree_metrics[worktree_key]
                worktree_metrics.switch_duration = duration
                worktree_metrics.branch_name = branch_name
                worktree_metrics.last_accessed = end_time
                worktree_metrics.operation_count += 1
                if not success:
                    worktree_metrics.error_count += 1
                
                # Update metrics
                self.worktree_operations_counter.add(1, {
                    "operation": "switch",
                    "success": success
                })
                
                self.worktree_operation_duration.record(duration, {
                    "repository_url": repository_url,
                    "operation": "switch"
                })
    
    @asynccontextmanager
    async def trace_merge_operation(self, repository_url: str, source_branch: str,
                                  target_branch: str, strategy: str = "merge"):
        """Trace merge operation."""
        operation_name = "merge_branches"
        attributes = {
            "git.repository_url": repository_url,
            "git.source_branch": source_branch,
            "git.target_branch": target_branch,
            "git.merge_strategy": strategy
        }
        
        start_time = time.time()
        success = True
        error_message = None
        conflicts_count = 0
        files_changed = 0
        insertions = 0
        deletions = 0
        conflict_resolution_duration = 0.0
        merge_id = f"{repository_url}#{source_branch}#{target_branch}#{int(time.time())}"
        
        async with self.apm.trace_async_operation(
            operation_name, APMOperationType.BUSINESS_TRANSACTION, attributes
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
                
                # Record merge metrics
                merge_metrics = MergeMetrics(
                    merge_id=merge_id,
                    repository_url=repository_url,
                    source_branch=source_branch,
                    target_branch=target_branch,
                    duration=duration,
                    success=success,
                    conflicts_count=conflicts_count,
                    files_changed=files_changed,
                    insertions=insertions,
                    deletions=deletions,
                    conflict_resolution_duration=conflict_resolution_duration,
                    strategy_used=strategy,
                    error_message=error_message
                )
                self.merge_metrics.append(merge_metrics)
                
                # Keep only recent merge data
                if len(self.merge_metrics) > self.max_merge_history:
                    self.merge_metrics.pop(0)
                
                # Update metrics
                self.merge_operations_counter.add(1, {
                    "repository_url": repository_url,
                    "strategy": strategy,
                    "success": success
                })
                
                self.merge_duration.record(duration, {
                    "repository_url": repository_url,
                    "strategy": strategy
                })
                
                self.conflict_counter.add(conflicts_count, {
                    "repository_url": repository_url,
                    "strategy": strategy
                })
                
                if conflicts_count > 0:
                    self.conflict_resolution_duration.record(conflict_resolution_duration, {
                        "repository_url": repository_url,
                        "strategy": strategy
                    })
    
    @asynccontextmanager
    async def trace_conflict_resolution(self, repository_url: str, conflict_count: int,
                                      strategy: str = "manual"):
        """Trace conflict resolution operation."""
        operation_name = "resolve_conflicts"
        attributes = {
            "git.repository_url": repository_url,
            "git.conflict_count": conflict_count,
            "git.resolution_strategy": strategy
        }
        
        start_time = time.time()
        success = True
        error_message = None
        
        async with self.apm.trace_async_operation(
            operation_name, APMOperationType.BUSINESS_TRANSACTION, attributes
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
                
                # Update metrics
                self.conflict_resolution_duration.record(duration, {
                    "repository_url": repository_url,
                    "strategy": strategy
                })
    
    @asynccontextmanager
    async def trace_file_operation(self, operation: str, file_path: str, worktree_path: str,
                                 file_size: int = 0):
        """Trace file operation."""
        operation_name = f"file_{operation}"
        attributes = {
            "file.operation": operation,
            "file.path": file_path,
            "file.worktree_path": worktree_path,
            "file.size": file_size
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
                
                # Record file operation metrics
                file_metrics = FileOperationMetrics(
                    operation_type=operation,
                    file_path=file_path,
                    worktree_path=worktree_path,
                    duration=duration,
                    success=success,
                    file_size=file_size,
                    error_message=error_message
                )
                self.file_operation_metrics.append(file_metrics)
                
                # Keep only recent file operation data
                if len(self.file_operation_metrics) > self.max_file_operation_history:
                    self.file_operation_metrics.pop(0)
                
                # Update metrics
                self.file_operations_counter.add(1, {
                    "operation": operation,
                    "success": success
                })
                
                self.file_operation_duration.record(duration, {
                    "operation": operation,
                    "file_size_category": self._get_file_size_category(file_size)
                })
    
    def _get_file_size_category(self, file_size: int) -> str:
        """Get file size category for metrics."""
        if file_size < 1024:
            return "small"
        elif file_size < 1024 * 1024:
            return "medium"
        elif file_size < 10 * 1024 * 1024:
            return "large"
        else:
            return "xlarge"
    
    def get_repository_performance_summary(self, repository_url: str = None) -> Dict[str, Any]:
        """Get performance summary for repositories."""
        if repository_url:
            metrics = self.repository_metrics.get(repository_url)
            if not metrics or metrics.repository_url == "":
                return {"repository_url": repository_url, "message": "No data available"}
            
            return {
                "repository_url": repository_url,
                "clone_duration": metrics.clone_duration,
                "fetch_duration": metrics.fetch_duration,
                "total_commits": metrics.total_commits,
                "total_branches": metrics.total_branches,
                "total_worktrees": metrics.total_worktrees,
                "repository_size": metrics.repository_size,
                "last_accessed": metrics.last_accessed,
                "operation_count": metrics.operation_count,
                "error_count": metrics.error_count,
                "error_rate": metrics.error_rate
            }
        else:
            # Return summary for all repositories
            summary = {}
            for repo_url, metrics in self.repository_metrics.items():
                if metrics.repository_url:
                    summary[repo_url] = self.get_repository_performance_summary(repo_url)
            return summary
    
    def get_worktree_performance_summary(self, worktree_path: str = None) -> Dict[str, Any]:
        """Get performance summary for worktrees."""
        if worktree_path:
            # Find worktree by path
            for key, metrics in self.worktree_metrics.items():
                if metrics.worktree_path == worktree_path:
                    return {
                        "worktree_path": metrics.worktree_path,
                        "repository_url": metrics.repository_url,
                        "branch_name": metrics.branch_name,
                        "creation_duration": metrics.creation_duration,
                        "switch_duration": metrics.switch_duration,
                        "file_count": metrics.file_count,
                        "size_bytes": metrics.size_bytes,
                        "last_accessed": metrics.last_accessed,
                        "operation_count": metrics.operation_count,
                        "error_count": metrics.error_count,
                        "error_rate": metrics.error_rate
                    }
            return {"worktree_path": worktree_path, "message": "No data available"}
        else:
            # Return summary for all worktrees
            summary = {}
            for key, metrics in self.worktree_metrics.items():
                if metrics.worktree_path:
                    summary[metrics.worktree_path] = self.get_worktree_performance_summary(metrics.worktree_path)
            return summary
    
    def get_merge_performance_summary(self) -> Dict[str, Any]:
        """Get merge operation summary."""
        if not self.merge_metrics:
            return {"message": "No merge operations recorded"}
        
        merge_data = self.merge_metrics
        total_merges = len(merge_data)
        successful_merges = sum(1 for m in merge_data if m.success)
        
        # Calculate average duration
        avg_duration = statistics.mean(m.duration for m in merge_data)
        
        # Calculate average conflict count
        avg_conflicts = statistics.mean(m.conflicts_count for m in merge_data)
        
        # Calculate total files changed
        total_files_changed = sum(m.files_changed for m in merge_data)
        
        # Calculate total insertions and deletions
        total_insertions = sum(m.insertions for m in merge_data)
        total_deletions = sum(m.deletions for m in merge_data)
        
        # Get strategy distribution
        strategy_distribution = defaultdict(int)
        for m in merge_data:
            strategy_distribution[m.strategy_used] += 1
        
        # Get conflict distribution
        conflict_distribution = defaultdict(int)
        for m in merge_data:
            if m.conflicts_count == 0:
                conflict_distribution["no_conflicts"] += 1
            elif m.conflicts_count <= 5:
                conflict_distribution["few_conflicts"] += 1
            elif m.conflicts_count <= 20:
                conflict_distribution["moderate_conflicts"] += 1
            else:
                conflict_distribution["many_conflicts"] += 1
        
        return {
            "total_merge_operations": total_merges,
            "success_rate": successful_merges / total_merges if total_merges > 0 else 0,
            "average_duration": avg_duration,
            "average_conflict_count": avg_conflicts,
            "total_files_changed": total_files_changed,
            "total_insertions": total_insertions,
            "total_deletions": total_deletions,
            "strategy_distribution": dict(strategy_distribution),
            "conflict_distribution": dict(conflict_distribution)
        }
    
    def get_file_operation_summary(self) -> Dict[str, Any]:
        """Get file operation summary."""
        if not self.file_operation_metrics:
            return {"message": "No file operations recorded"}
        
        file_ops = self.file_operation_metrics
        total_operations = len(file_ops)
        successful_operations = sum(1 for op in file_ops if op.success)
        
        # Calculate average duration by operation type
        operation_durations = defaultdict(list)
        for op in file_ops:
            operation_durations[op.operation_type].append(op.duration)
        
        avg_durations = {}
        for op_type, durations in operation_durations.items():
            avg_durations[op_type] = statistics.mean(durations)
        
        # Get operation type distribution
        operation_distribution = defaultdict(int)
        for op in file_ops:
            operation_distribution[op.operation_type] += 1
        
        # Get file size distribution
        size_distribution = defaultdict(int)
        for op in file_ops:
            size_category = self._get_file_size_category(op.file_size)
            size_distribution[size_category] += 1
        
        return {
            "total_file_operations": total_operations,
            "success_rate": successful_operations / total_operations if total_operations > 0 else 0,
            "average_durations_by_operation": avg_durations,
            "operation_distribution": dict(operation_distribution),
            "file_size_distribution": dict(size_distribution)
        }
    
    def get_performance_insights(self) -> List[Dict[str, Any]]:
        """Get performance insights and recommendations."""
        insights = []
        
        # Analyze repository operations
        for repo_url, metrics in self.repository_metrics.items():
            if not metrics.repository_url:
                continue
            
            # Check for slow clone operations
            if metrics.clone_duration > self.slow_clone_threshold:
                insights.append({
                    "type": "slow_clone",
                    "repository_url": repo_url,
                    "severity": "warning",
                    "message": f"Repository {repo_url} has slow clone time ({metrics.clone_duration:.2f}s)",
                    "recommendation": "Consider using shallow clones or optimizing network connection"
                })
            
            # Check for slow fetch operations
            if metrics.fetch_duration > self.slow_fetch_threshold:
                insights.append({
                    "type": "slow_fetch",
                    "repository_url": repo_url,
                    "severity": "warning",
                    "message": f"Repository {repo_url} has slow fetch time ({metrics.fetch_duration:.2f}s)",
                    "recommendation": "Consider reducing fetch frequency or optimizing network connection"
                })
            
            # Check for high error rates
            if metrics.error_rate > 0.1 and metrics.operation_count > 10:
                insights.append({
                    "type": "high_repository_error_rate",
                    "repository_url": repo_url,
                    "severity": "error",
                    "message": f"Repository {repo_url} has high error rate ({metrics.error_rate:.2%})",
                    "recommendation": "Check repository health and access permissions"
                })
        
        # Analyze merge operations
        if self.merge_metrics:
            recent_merges = self.merge_metrics[-100:]  # Last 100 merge operations
            
            # Check for slow merges
            slow_merges = [m for m in recent_merges if m.duration > self.slow_merge_threshold]
            if len(slow_merges) > 5:
                insights.append({
                    "type": "slow_merges",
                    "severity": "warning",
                    "message": f"High number of slow merge operations ({len(slow_merges)} in last 100)",
                    "recommendation": "Optimize merge strategies or reduce merge complexity"
                })
            
            # Check for high conflict counts
            high_conflict_merges = [m for m in recent_merges if m.conflicts_count > self.high_conflict_threshold]
            if len(high_conflict_merges) > 5:
                insights.append({
                    "type": "high_conflict_merges",
                    "severity": "warning",
                    "message": f"High number of merge operations with many conflicts ({len(high_conflict_merges)} in last 100)",
                    "recommendation": "Improve branching strategy or merge process"
                })
        
        # Analyze file operations
        if self.file_operation_metrics:
            recent_file_ops = self.file_operation_metrics[-1000:]  # Last 1000 file operations
            
            # Check for large file operations
            large_file_ops = [op for op in recent_file_ops if op.file_size > self.large_file_threshold]
            if len(large_file_ops) > 10:
                insights.append({
                    "type": "large_file_operations",
                    "severity": "info",
                    "message": f"High number of large file operations ({len(large_file_ops)} in last 1000)",
                    "recommendation": "Consider using Git LFS for large files"
                })
        
        return insights
    
    def record_repository_size(self, repository_url: str, size: int):
        """Record repository size."""
        if repository_url in self.repository_metrics:
            self.repository_metrics[repository_url].repository_size = size
            self.repository_size_gauge.add(size, {"repository_url": repository_url})
    
    def record_branch_count(self, repository_url: str, count: int):
        """Record branch count."""
        if repository_url in self.repository_metrics:
            self.repository_metrics[repository_url].total_branches = count
    
    def record_commit_count(self, repository_url: str, count: int):
        """Record commit count."""
        if repository_url in self.repository_metrics:
            self.repository_metrics[repository_url].total_commits = count
    
    def record_worktree_file_count(self, worktree_path: str, repository_url: str, count: int):
        """Record worktree file count."""
        worktree_key = f"{repository_url}#{worktree_path}"
        if worktree_key in self.worktree_metrics:
            self.worktree_metrics[worktree_key].file_count = count
    
    def record_worktree_size(self, worktree_path: str, repository_url: str, size: int):
        """Record worktree size."""
        worktree_key = f"{repository_url}#{worktree_path}"
        if worktree_key in self.worktree_metrics:
            self.worktree_metrics[worktree_key].size_bytes = size


# Global instance
git_worktree_apm = None


def get_git_worktree_apm() -> GitWorktreeAPM:
    """Get the global Git Worktree APM instance."""
    global git_worktree_apm
    if git_worktree_apm is None:
        git_worktree_apm = GitWorktreeAPM()
    return git_worktree_apm


def initialize_git_worktree_apm(config: APMConfig = None):
    """Initialize the global Git Worktree APM instance."""
    global git_worktree_apm
    git_worktree_apm = GitWorktreeAPM(config)
    return git_worktree_apm


# Decorators for Git Worktree operations
def trace_repository_clone(operation_name: str = None):
    """Decorator to trace repository clone operations."""
    def decorator(func):
        name = operation_name or f"repository_clone.{func.__name__}"
        
        async def async_wrapper(*args, **kwargs):
            apm = get_git_worktree_apm()
            
            # Extract parameters
            repository_url = kwargs.get('repository_url', '')
            destination_path = kwargs.get('destination_path', '')
            depth = kwargs.get('depth', 0)
            branch = kwargs.get('branch', None)
            
            async with apm.trace_repository_clone(repository_url, destination_path, depth, branch) as span:
                return await func(*args, **kwargs)
        
        return async_wrapper
    
    return decorator


def trace_worktree_operation(operation_name: str = None):
    """Decorator to trace worktree operations."""
    def decorator(func):
        name = operation_name or f"worktree_operation.{func.__name__}"
        
        async def async_wrapper(*args, **kwargs):
            apm = get_git_worktree_apm()
            
            # Determine operation type
            operation = func.__name__
            worktree_path = kwargs.get('worktree_path', '')
            repository_url = kwargs.get('repository_url', '')
            
            if operation == 'create':
                branch_name = kwargs.get('branch_name', '')
                force = kwargs.get('force', False)
                async with apm.trace_worktree_create(repository_url, worktree_path, branch_name, force) as span:
                    return await func(*args, **kwargs)
            elif operation == 'remove':
                async with apm.trace_worktree_remove(worktree_path, repository_url) as span:
                    return await func(*args, **kwargs)
            elif operation == 'switch':
                branch_name = kwargs.get('branch_name', '')
                async with apm.trace_worktree_switch(worktree_path, branch_name, repository_url) as span:
                    return await func(*args, **kwargs)
            else:
                # Generic worktree operation
                async with apm.trace_worktree_operation(repository_url, worktree_path, operation) as span:
                    return await func(*args, **kwargs)
        
        return async_wrapper
    
    return decorator


def trace_merge_operation(operation_name: str = None):
    """Decorator to trace merge operations."""
    def decorator(func):
        name = operation_name or f"merge_operation.{func.__name__}"
        
        async def async_wrapper(*args, **kwargs):
            apm = get_git_worktree_apm()
            
            # Extract parameters
            repository_url = kwargs.get('repository_url', '')
            source_branch = kwargs.get('source_branch', '')
            target_branch = kwargs.get('target_branch', '')
            strategy = kwargs.get('strategy', 'merge')
            
            async with apm.trace_merge_operation(repository_url, source_branch, target_branch, strategy) as span:
                return await func(*args, **kwargs)
        
        return async_wrapper
    
    return decorator