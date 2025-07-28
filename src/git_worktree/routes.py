"""API routes for the Git Worktree service."""

from fastapi import APIRouter

from src.common.metrics import record_request

from .worktree_manager import create

router = APIRouter(prefix="/worktree", tags=["git-worktree"])


@router.post("/", response_model=str)
def create_worktree(path: str) -> str:
    record_request("git-worktree")
    return create(path)
