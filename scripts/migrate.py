"""Run database migrations using Alembic."""

import subprocess

if __name__ == "__main__":
    subprocess.run(["alembic", "upgrade", "head"], check=True)
