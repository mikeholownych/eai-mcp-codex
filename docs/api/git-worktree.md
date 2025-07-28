# Git worktree API

The Git Worktree service manages lightweight checkouts used by the workflow orchestrator. It allows creating worktrees for isolated development tasks.

## Endpoints

- `POST /worktree/` – create a worktree at the given path.
- `GET /health` – health status endpoint.

Results are simple strings containing the path to the created worktree.
