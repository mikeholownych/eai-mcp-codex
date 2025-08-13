import os
import sys
from pathlib import Path
import asyncio
import pytest
import inspect

# Ensure src package is importable when running tests directly
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")
# Ensure testing mode is set before any imports initialize tracing/APM
os.environ.setdefault("TESTING_MODE", "true")
os.environ.setdefault("OTEL_SDK_DISABLED", "true")
os.environ.setdefault("JAEGER_ENABLED", "false")
os.environ.setdefault("OTLP_ENABLED", "false")


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


def pytest_collection_modifyitems(items):
    """Automatically mark async test functions with pytest.mark.asyncio when missing."""
    for item in items:
        test_obj = getattr(item, 'obj', None)
        if inspect.iscoroutinefunction(test_obj):
            has_asyncio_mark = any(mark.name == "asyncio" for mark in item.iter_markers())
            if not has_asyncio_mark:
                item.add_marker(pytest.mark.asyncio)


def pytest_configure(config):
    config.addinivalue_line("markers", "integration: mark a test as an integration test")
