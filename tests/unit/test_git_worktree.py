from pathlib import Path
import pytest

# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

from src.git_worktree.worktree_manager import create


@pytest.mark.asyncio
async def test_create(tmp_path: Path) -> None:
    path = tmp_path / "repo"
    result = await create(str(path))
    assert Path(result).exists()
