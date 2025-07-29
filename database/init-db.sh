#!/bin/bash
# init-db.sh

set -e

DB_USER="mcp_user"
DB_PASS="${POSTGRES_PASSWORD:-mcp_secure_password}"
DB_HOST="localhost"
DB_NAMES=(model_router_db plan_management_db git_worktree_db workflow_orchestrator_db verification_feedback_db)

echo "Waiting for PostgreSQL to be ready..."
until pg_isready -h "$DB_HOST" -U "$DB_USER" > /dev/null 2>&1; do
  sleep 1
done

for DB in "${DB_NAMES[@]}"; do
  echo "Checking database: $DB"
  if ! psql -h "$DB_HOST" -U "$DB_USER" -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='$DB'" | grep -q 1; then
    echo "Creating database: $DB"
    createdb -h "$DB_HOST" -U "$DB_USER" "$DB"
  else
    echo "Database $DB already exists."
  fi
done
