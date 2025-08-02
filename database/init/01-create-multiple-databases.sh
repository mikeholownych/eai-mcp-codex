#!/bin/bash
set -e

# Create multiple databases for MCP services
# This script runs during PostgreSQL container initialization

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    -- Create individual databases for each service
    CREATE DATABASE plan_management_db;
    CREATE DATABASE git_worktree_db;
    CREATE DATABASE workflow_orchestrator_db;
    CREATE DATABASE verification_feedback_db;
    CREATE DATABASE staff_db;
    CREATE DATABASE grafana_db;
    CREATE DATABASE auth_db;
    
    -- Grant all privileges to the mcp_user for all databases
    GRANT ALL PRIVILEGES ON DATABASE plan_management_db TO mcp_user;
    GRANT ALL PRIVILEGES ON DATABASE git_worktree_db TO mcp_user;
    GRANT ALL PRIVILEGES ON DATABASE workflow_orchestrator_db TO mcp_user;
    GRANT ALL PRIVILEGES ON DATABASE verification_feedback_db TO mcp_user;
    GRANT ALL PRIVILEGES ON DATABASE staff_db TO mcp_user;
    GRANT ALL PRIVILEGES ON DATABASE grafana_db TO mcp_user;
    GRANT ALL PRIVILEGES ON DATABASE auth_db TO mcp_user;
    
    -- Create extensions that might be needed
    \c plan_management_db;
    CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
    CREATE EXTENSION IF NOT EXISTS "pgcrypto";
    
    \c git_worktree_db;
    CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
    CREATE EXTENSION IF NOT EXISTS "pgcrypto";
    
    \c workflow_orchestrator_db;
    CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
    CREATE EXTENSION IF NOT EXISTS "pgcrypto";
    
    \c verification_feedback_db;
    CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
    CREATE EXTENSION IF NOT EXISTS "pgcrypto";
    
    \c staff_db;
    CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
    CREATE EXTENSION IF NOT EXISTS "pgcrypto";
    
    \c grafana_db;
    CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
    
    \c auth_db;
    CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
    CREATE EXTENSION IF NOT EXISTS "pgcrypto";
EOSQL

echo "All databases created successfully!"