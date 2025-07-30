import pytest
import os
import asyncio

@pytest.fixture(scope="session", autouse=True)
def set_testing_mode():
    os.environ["TESTING_MODE"] = "true"
    yield
    os.environ["TESTING_MODE"] = "false"

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()