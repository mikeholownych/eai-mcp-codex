from uvicorn import run

from src.git_worktree.app import app
from src.git_worktree.config import SERVICE_PORT

if __name__ == "__main__":
    run(app, host="0.0.0.0", port=SERVICE_PORT)
