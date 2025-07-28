"""Manage Git worktrees."""

from pathlib import Path


def create(path: str) -> str:
    """Create a directory representing a worktree."""
    worktree = Path(path)
    worktree.mkdir(parents=True, exist_ok=True)
    return str(worktree.resolve())
