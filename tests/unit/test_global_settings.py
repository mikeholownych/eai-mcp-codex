import importlib
from pytest import raises
import sys


def test_jwt_secret_required_in_production(monkeypatch):
    monkeypatch.delenv("JWT_SECRET", raising=False)
    monkeypatch.setenv("ENVIRONMENT", "production")
    if "src.common.settings" in sys.modules:
        del sys.modules["src.common.settings"]
    with raises(ValueError):
        importlib.import_module("src.common.settings")
