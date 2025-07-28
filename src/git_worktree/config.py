"""Git Worktree configuration."""

import os

SERVICE_NAME = "git-worktree"
SERVICE_PORT = int(os.getenv("GIT_WORKTREE_PORT", 8003))
