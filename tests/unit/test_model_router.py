from src.model_router.router import route
from src.model_router.models import ModelRequest


def test_route():
    assert route(ModelRequest(text="hi")).result == "hi"
