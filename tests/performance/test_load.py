import time
from src.model_router.router import route
from src.model_router.models import ModelRequest


def test_router_under_load():
    start = time.time()
    for _ in range(1000):
        route(ModelRequest(text="load"))
    assert time.time() - start < 2
