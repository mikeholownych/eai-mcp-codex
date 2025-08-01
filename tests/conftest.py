import os
import sys
from pathlib import Path
import asyncio
import pytest

# Ensure src package is importable when running tests directly
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")


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
