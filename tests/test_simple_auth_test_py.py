import importlib
import runpy
import sys

import pytest

# Framework note:
# - Using pytest for test discovery and assertions.
# - Using pytest's monkeypatch and capsys fixtures for patching and output capture.

@pytest.fixture(autouse=True)
def restore_module_cache():
    """
    Ensure simple_auth_test module is reloaded fresh for each test to avoid cross-test state.
    """
    modname = "simple_auth_test"
    if modname in sys.modules:
        del sys.modules[modname]
    yield
    if modname in sys.modules:
        del sys.modules[modname]


def test_modified_auth_happy_path(capsys):
    """
    Verifies the happy path: function returns True and emits success markers.
    """
    sat = importlib.import_module("simple_auth_test")
    result = sat.test_modified_auth()
    captured = capsys.readouterr().out

    assert result is True
    # Spot-check key success messages printed by the script
    assert "Testing Modified Authentication Logic..." in captured
    assert "✅ ALL TESTS PASSED!" in captured
    assert "Successfully modified default admin credentials:" in captured
    assert "Username: mike.holownych@gmail.com" in captured
    assert "Role: superadmin" in captured
    assert "API Key: superadmin-api-key-456" in captured


def test_modified_auth_password_verification_failure(monkeypatch, capsys):
    """
    Forces password verification to fail by raising on the second invocation of pbkdf2_hmac.
    The first call (hashing) succeeds, the second (verify) raises -> verify_password returns False.
    """
    sat = importlib.import_module("simple_auth_test")

    call_count = {"n": 0}

    real_pbkdf2 = sat.hashlib.pbkdf2_hmac

    def pbkdf2_side_effect(name, password, salt, iterations):
        call_count["n"] += 1
        # First call: allow hashing to succeed
        if call_count["n"] == 1:
            return real_pbkdf2(name, password, salt, iterations)
        # Second call: simulate failure during verification
        raise ValueError("Simulated KDF error")

    monkeypatch.setattr(sat.hashlib, "pbkdf2_hmac", pbkdf2_side_effect)

    result = sat.test_modified_auth()
    captured = capsys.readouterr().out

    assert result is False
    assert "Password verification failed" in captured


def test_modified_auth_permission_failure(monkeypatch, capsys):
    """
    Induce permission check failure by replacing UserRole with a stub whose `.value` objects
    never compare equal (so 'in' membership checks always return False).
    This causes all permission checks to be denied and the function to return False.
    """

    class NeverEqual:
        def __eq__(self, other):  # pragma: no cover - behavior is straightforward
            return False
        def __repr__(self):
            return "<NeverEqual>"

    class Member:
        def __init__(self, v):
            self.value = v

    class DummyUserRole:
        SUPERADMIN = Member(NeverEqual())
        ADMIN = Member(NeverEqual())
        USER = Member("user")        # Not used to grant all permissions
        SERVICE = Member("service")
        READONLY = Member("readonly")

    sat = importlib.import_module("simple_auth_test")
    # Swap out the UserRole enum in the module for our dummy object.
    monkeypatch.setattr(sat, "UserRole", DummyUserRole, raising=True)

    result = sat.test_modified_auth()
    captured = capsys.readouterr().out

    assert result is False
    assert "Some permissions denied to superadmin" in captured


def test_main_success_exit_code_zero(monkeypatch):
    """
    Running the module as __main__ should exit with code 0 when tests pass.
    """
    # Ensure fresh import state
    modname = "simple_auth_test"
    if modname in sys.modules:
        del sys.modules[modname]

    with pytest.raises(SystemExit) as excinfo:
        runpy.run_module(modname, run_name="__main__")

    assert excinfo.value.code == 0


def test_main_failure_exit_code_one(monkeypatch, capsys):
    """
    Force a failure (password verification) and verify the __main__ path exits with code 1.
    """
    modname = "simple_auth_test"
    if modname in sys.modules:
        del sys.modules[modname]

    # Load the module so we can patch it before running as __main__
    sat = importlib.import_module(modname)

    call_count = {"n": 0}
    real_pbkdf2 = sat.hashlib.pbkdf2_hmac

    def pbkdf2_side_effect(name, password, salt, iterations):
        call_count["n"] += 1
        if call_count["n"] == 1:
            return real_pbkdf2(name, password, salt, iterations)
        raise RuntimeError("verification failure")

    # Patch then run as __main__
    import importlib as _importlib
    _importlib.reload(sat)
    monkeypatch.setattr(sat.hashlib, "pbkdf2_hmac", pbkdf2_side_effect)

    # Now execute the module as a script
    with pytest.raises(SystemExit) as excinfo:
        runpy.run_module(modname, run_name="__main__")

    assert excinfo.value.code == 1
    out = capsys.readouterr().out
    assert "Tests failed!" in out or "Password verification failed" in out