import importlib


def test_initial_migration_has_upgrade_and_downgrade() -> None:
    mod = importlib.import_module("database.migrations.versions.0001_initial_schema")
    assert hasattr(mod, "upgrade")
    assert hasattr(mod, "downgrade")
