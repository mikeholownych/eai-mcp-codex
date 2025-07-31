-- database/init.sql - Database Initialization
-- Create databases for each service safely

CREATE DATABASE grafana_db;

-- Create shared tables in mcp_database
CREATE TABLE IF NOT EXISTS service_registry (
    id SERIAL PRIMARY KEY,
    service_name VARCHAR(100) NOT NULL,
    service_url VARCHAR(255) NOT NULL,
    health_status VARCHAR(20) DEFAULT 'unknown',
    last_heartbeat TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS audit_log (
    id SERIAL PRIMARY KEY,
    service_name VARCHAR(100) NOT NULL,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100),
    resource_id VARCHAR(100),
    user_id VARCHAR(100),
    details JSONB,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS metrics_summary (
    id SERIAL PRIMARY KEY,
    metric_name VARCHAR(100) NOT NULL,
    metric_value NUMERIC,
    labels JSONB DEFAULT '{}',
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_service_registry_name ON service_registry(service_name);
CREATE INDEX IF NOT EXISTS idx_audit_log_service ON audit_log(service_name);
CREATE INDEX IF NOT EXISTS idx_audit_log_timestamp ON audit_log(timestamp);
CREATE INDEX IF NOT EXISTS idx_metrics_summary_name ON metrics_summary(metric_name);
CREATE INDEX IF NOT EXISTS idx_metrics_summary_timestamp ON metrics_summary(timestamp);

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO mcp_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO mcp_user;