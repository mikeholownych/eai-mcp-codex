-- database/sample_data.sql - Sample data for development
-- This file contains sample data for development and testing

-- Insert sample service registry entries
INSERT INTO service_registry (service_name, service_url, health_status, metadata) VALUES
('model-router', 'http://model-router:8001', 'healthy', '{"version": "1.0.0", "capabilities": ["claude-o3", "sonnet-4", "sonnet-3.7"]}'),
('plan-management', 'http://plan-management:8002', 'healthy', '{"version": "1.0.0", "max_plans": 100}'),
('git-worktree-manager', 'http://git-worktree-manager:8003', 'healthy', '{"version": "1.0.0", "max_worktrees": 50}'),
('workflow-orchestrator', 'http://workflow-orchestrator:8004', 'healthy', '{"version": "1.0.0", "max_concurrent": 10}'),
('verification-feedback', 'http://verification-feedback:8005', 'healthy', '{"version": "1.0.0", "verification_types": ["syntax", "security", "performance"]}')
ON CONFLICT (service_name) DO NOTHING;

-- Insert sample audit log entries
INSERT INTO audit_log (service_name, action, resource_type, resource_id, user_id, details) VALUES
('model-router', 'request', 'model', 'claude-o3', 'system', '{"tokens": 1500, "response_time": 250}'),
('plan-management', 'create', 'plan', 'plan-001', 'user-123', '{"title": "Sample Development Plan", "tasks": 5}'),
('git-worktree-manager', 'create', 'worktree', 'wt-001', 'user-123', '{"repo": "sample-repo", "branch": "feature-branch"}')
ON CONFLICT DO NOTHING;

-- Insert sample metrics
INSERT INTO metrics_summary (metric_name, metric_value, labels) VALUES
('requests_total', 150, '{"service": "model-router", "status": "success"}'),
('response_time_ms', 245, '{"service": "model-router", "percentile": "p95"}'),
('active_plans', 12, '{"service": "plan-management"}'),
('active_worktrees', 8, '{"service": "git-worktree-manager"}'),
('verification_score', 0.95, '{"service": "verification-feedback", "type": "security"}')
ON CONFLICT DO NOTHING;