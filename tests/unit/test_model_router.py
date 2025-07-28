import importlib
import os

from src.model_router import config as config_module, router as router_module
from src.model_router.models import ModelRequest


def test_route(tmp_path) -> None:
    rules_file = tmp_path / "rules.yml"
    rules_file.write_text(
        "rules:\n- match: 'urgent'\n  model: sonnet\n- match: '.*'\n  model: haiku\n"
    )
    os.environ["MODEL_ROUTER_RULES_FILE"] = str(rules_file)
    importlib.reload(config_module)
    importlib.reload(router_module)
    result = router_module.route(ModelRequest(text="urgent task"))
    assert result.result.startswith("sonnet:")
