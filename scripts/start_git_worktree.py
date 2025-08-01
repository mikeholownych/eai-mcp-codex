import sys
import os

sys.path.insert(0, os.getcwd())

from uvicorn import run

from src.git_worktree.app import app
from src.git_worktree.config import settings

if __name__ == "__main__":
    run(app, host="0.0.0.0", port=settings.service_port)
