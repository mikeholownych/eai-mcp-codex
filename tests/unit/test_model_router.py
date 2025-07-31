import importlib
import os
import pytest

# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

from src.model_router import config as config_module, router as router_module
from src.model_router.models import ModelRequest


@pytest.mark.asyncio
async def test_route(tmp_path) -> None:
    rules_file = tmp_path / "rules.yml"
    rules_file.write_text(
        "rules:\n- match: 'urgent'\n  model: sonnet\n- match: '.*'\n  model: haiku\n"
    )
    os.environ["MODEL_ROUTER_RULES_FILE"] = str(rules_file)
    importlib.reload(config_module)
    importlib.reload(router_module)
    result = await router_module.route_async(ModelRequest(text="urgent task"))
    assert result.result.startswith("sonnet:")