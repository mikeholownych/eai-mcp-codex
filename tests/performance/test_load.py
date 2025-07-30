import time
import pytest
from src.model_router.router import route_async
from src.model_router.models import ModelRequest
import sys
import os

# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

@pytest.mark.asyncio
async def test_router_under_load():
    start = time.time()
    for _ in range(1000):
        await route_async(ModelRequest(text="load"))
    assert time.time() - start < 2