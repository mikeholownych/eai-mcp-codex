"""Data models for Git Worktree operations."""

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class WorktreeStatus(str, Enum):
    """Worktree status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    LOCKED = "locked"
    BROKEN = "broken"


class BranchStatus(str, Enum):
    """Branch status enumeration."""
    UP_TO_DATE = "up_to_date"
    AHEAD = "ahead"
    BEHIND = "behind"
    DIVERGED = "diverged"
    UNTRACKED = "untracked"


class Repo(BaseModel):
    """Git repository model."""
    name: str
    path: str
    remote_url: Optional[str] = None
    default_branch: str = "main"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Worktree(BaseModel):
    """Git worktree model."""
    id: str
    repo_name: str
    branch: str
    path: str
    status: WorktreeStatus = WorktreeStatus.ACTIVE
    is_bare: bool = False
    is_detached: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_used: Optional[datetime] = None
    commit_hash: Optional[str] = None
    upstream_branch: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BranchInfo(BaseModel):
    """Branch information model."""
    name: str
    commit_hash: str
    commit_message: str
    author: str
    commit_date: datetime
    is_current: bool = False
    upstream: Optional[str] = None
    status: BranchStatus = BranchStatus.UP_TO_DATE
    ahead_count: int = 0
    behind_count: int = 0


class WorktreeRequest(BaseModel):
    """Request model for creating worktrees."""
    repo_name: str
    branch: str
    path: Optional[str] = None
    create_branch: bool = False
    checkout_existing: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)


class WorktreeOperation(BaseModel):
    """Model for worktree operations."""
    operation: str  # create, delete, lock, unlock, move
    worktree_id: str
    params: Dict[str, Any] = Field(default_factory=dict)
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    success: bool = False
    error_message: Optional[str] = None
    result: Dict[str, Any] = Field(default_factory=dict)
