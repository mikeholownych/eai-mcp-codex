"""Alembic environment setup."""

import os
import sys

# Add the parent directory to sys.path to import models
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from alembic import context
from sqlalchemy import create_engine, pool

# Import your models here
# target_metadata = Base.metadata  # If you have SQLAlchemy models
target_metadata = None  # For now, use None

config = context.config

# Set the sqlalchemy.url from environment variable if not set
if not config.get_main_option('sqlalchemy.url'):
    db_url = os.environ.get('DATABASE_URL', 'postgresql://mcp_user:mcp_secure_password@postgres:5432/plan_management_db')
    config.set_main_option('sqlalchemy.url', db_url)


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = create_engine(
        config.get_main_option("sqlalchemy.url"), poolclass=pool.NullPool
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
