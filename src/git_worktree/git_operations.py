"""Utilities to perform Git operations."""

import subprocess
from pathlib import Path


def clone(url: str, dest: str) -> str:
    """Clone a Git repository to the destination."""
    subprocess.run(["git", "clone", url, dest], check=True)
    return str(Path(dest).resolve())
