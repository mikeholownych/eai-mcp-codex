from src.model_router.router import route
from src.model_router.models import ModelRequest


def test_route() -> None:
    result = route(ModelRequest(text="hi"))
    assert result.result.startswith("haiku:")
