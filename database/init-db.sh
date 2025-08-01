#!/bin/bash
# init-db.sh

set -e

DB_USER="mcp_user"
DB_PASS="${POSTGRES_PASSWORD:-mcp_secure_password}"
DB_HOST="localhost"
DB_NAMES=(mcp_database model_router_db plan_management_db git_worktree_db workflow_orchestrator_db verification_feedback_db grafana_db)

echo "Waiting for PostgreSQL to be ready..."
until pg_isready -h "$DB_HOST" -U postgres > /dev/null 2>&1; do
  sleep 1
done

echo "Creating user and main database if they don't exist..."
psql -h "$DB_HOST" -U postgres -tc "SELECT 1 FROM pg_user WHERE usename = '$DB_USER'" | grep -q 1 || psql -h "$DB_HOST" -U postgres -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASS';"
psql -h "$DB_HOST" -U postgres -tc "SELECT 1 FROM pg_database WHERE datname = 'mcp_database'" | grep -q 1 || psql -h "$DB_HOST" -U postgres -c "CREATE DATABASE mcp_database OWNER $DB_USER;"
psql -h "$DB_HOST" -U postgres -d mcp_database -c "GRANT ALL PRIVILEGES ON DATABASE mcp_database TO $DB_USER;"

for DB in "${DB_NAMES[@]}"; do
  echo "Checking database: $DB"
  if ! psql -h "$DB_HOST" -U "$DB_USER" -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='$DB'" | grep -q 1; then
    echo "Creating database: $DB"
    createdb -h "$DB_HOST" -U "$DB_USER" "$DB"
  else
    echo "Database $DB already exists."
  fi
done