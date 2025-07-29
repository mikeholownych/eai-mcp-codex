"""API routes for the Git Worktree service."""

from fastapi import APIRouter, HTTPException

from src.common.metrics import record_request

from .models import WorktreeRequest, Worktree
from .worktree_manager import get_worktree_manager

router = APIRouter(prefix="/worktree", tags=["git-worktree"])


@router.post("/", response_model=Worktree)
async def create_worktree_route(request: WorktreeRequest) -> Worktree:
    record_request("git-worktree")
    manager = await get_worktree_manager()
    try:
        worktree = await manager.create_worktree(request)
        return worktree
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create worktree: {e}")