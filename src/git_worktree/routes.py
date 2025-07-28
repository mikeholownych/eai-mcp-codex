"""Routes for Git Worktree."""

from fastapi import APIRouter

from .models import Repo

router = APIRouter()


@router.get("/repos/{name}")
def get_repo(name: str) -> Repo:
    return Repo(name=name)
