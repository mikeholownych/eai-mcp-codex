from src.git_worktree.worktree_manager import create


def test_create():
    assert create("path") == "created:path"
