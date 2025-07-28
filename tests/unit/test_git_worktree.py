from pathlib import Path

from src.git_worktree.worktree_manager import create


def test_create(tmp_path: Path) -> None:
    path = tmp_path / "repo"
    result = create(str(path))
    assert Path(result).exists()
