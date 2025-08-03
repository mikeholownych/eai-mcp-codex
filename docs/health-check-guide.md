# MCP Health Check Framework Guide

## Overview

The MCP (Multimodal Content Processor) Health Check Framework provides comprehensive health monitoring and alerting for all MCP services. This framework ensures system reliability, performance monitoring, and proactive issue detection across the entire MCP ecosystem.

## Architecture

### Core Components

1. **Enhanced Health Check Framework** (`src/common/enhanced_health_check.py`)
   - Base health checking infrastructure
   - Support for multiple check types (liveness, readiness, dependency, resource, business logic, performance)
   - Timeout handling and retry mechanisms
   - Metrics collection and tracing integration

2. **Service-Specific Health Checkers**
   - Model Router Health Checker (`src/model_router/health_checks.py`)
   - Plan Management Health Checker (`src/plan_management/health_checks.py`)
   - Git Worktree Health Checker (`src/git_worktree/health_checks.py`)
   - Workflow Orchestrator Health Checker (`src/workflow_orchestrator/health_checks.py`)
   - Verification Feedback Health Checker (`src/verification_feedback/health_checks.py`)

3. **Health Aggregation Service** (`src/common/health_aggregator.py`)
   - Centralized health data collection
   - System-wide health status calculation
   - Health trend analysis
   - Historical health data storage

4. **Health Monitoring and Alerting** (`src/common/health_monitoring.py`)
   - Real-time health monitoring
   - Configurable alert rules
   - Multi-channel notifications (email, Slack, PagerDuty, webhook)
   - Alert lifecycle management

5. **Health Check Testing** (`src/common/health_check_testing.py`)
   - Comprehensive test suites
   - Performance benchmarking
   - Load testing capabilities
   - Validation utilities

6. **Health Check Service** (`src/health_service/app.py`)
   - Central health check API
   - RESTful endpoints for all health operations
   - Integration with monitoring systems
   - Management interface for alerts and rules

## Health Check Types

### 1. Liveness Checks
- **Purpose**: Determine if a service is running and responsive
- **Use Case**: Kubernetes liveness probes, basic service availability
- **Response Time**: < 1 second
- **Criticality**: High

### 2. Readiness Checks
- **Purpose**: Determine if a service is ready to handle requests
- **Use Case**: Kubernetes readiness probes, traffic routing decisions
- **Response Time**: < 5 seconds
- **Criticality**: High

### 3. Dependency Checks
- **Purpose**: Verify connectivity to external dependencies
- **Use Case**: Database connections, API endpoints, message queues
- **Response Time**: < 10 seconds
- **Criticality**: Medium

### 4. Resource Checks
- **Purpose**: Monitor system resource utilization
- **Use Case**: Memory, CPU, disk space, file handles
- **Response Time**: < 5 seconds
- **Criticality**: Medium

### 5. Business Logic Checks
- **Purpose**: Validate core business functionality
- **Use Case**: Model availability, routing logic, workflow execution
- **Response Time**: < 30 seconds
- **Criticality**: High

### 6. Performance Checks
- **Purpose**: Monitor performance metrics and SLAs
- **Use Case**: Response times, throughput, error rates
- **Response Time**: < 15 seconds
- **Criticality**: Medium

## Service-Specific Health Checks

### Model Router Health Checks

#### Core Functionality
- **Model Availability**: Check if all configured models are accessible
- **Routing Logic**: Validate model selection and routing algorithms
- **API Connectivity**: Verify connectivity to model providers
- **Performance Metrics**: Monitor response times and throughput

#### Health Check Endpoints
```python
# Liveness check
GET /health/liveness

# Readiness check
GET /health/readiness

# Comprehensive health check
GET /health

# Model-specific health
GET /health/models/{model_name}
```

#### Example Response
```json
{
  "service": "model-router",
  "status": "healthy",
  "timestamp": "2025-08-03T01:00:00.000Z",
  "checks": {
    "model_availability": {
      "status": "healthy",
      "message": "All models are available",
      "models": {
        "claude-3": "available",
        "gpt-4": "available",
        "llama-2": "degraded"
      }
    },
    "routing_logic": {
      "status": "healthy",
      "message": "Routing logic functioning normally",
      "routing_accuracy": 0.98
    },
    "api_connectivity": {
      "status": "healthy",
      "message": "All API endpoints reachable",
      "endpoints": {
        "anthropic": "connected",
        "openai": "connected",
        "local": "connected"
      }
    }
  }
}
```

### Plan Management Health Checks

#### Core Functionality
- **Task Decomposition**: Verify task breakdown capabilities
- **Consensus Building**: Check multi-agent consensus mechanisms
- **Storage Operations**: Validate plan storage and retrieval
- **Backup Status**: Monitor backup processes and integrity

#### Health Check Endpoints
```python
# Liveness check
GET /health/liveness

# Readiness check
GET /health/readiness

# Comprehensive health check
GET /health

# Plan storage health
GET /health/storage
```

#### Example Response
```json
{
  "service": "plan-management",
  "status": "healthy",
  "timestamp": "2025-08-03T01:00:00.000Z",
  "checks": {
    "task_decomposition": {
      "status": "healthy",
      "message": "Task decomposition working correctly",
      "decomposition_accuracy": 0.95
    },
    "consensus_building": {
      "status": "healthy",
      "message": "Consensus building operational",
      "consensus_time_avg": 5.2
    },
    "storage_operations": {
      "status": "healthy",
      "message": "Storage operations normal",
      "storage_usage": "65%"
    }
  }
}
```

### Git Worktree Health Checks

#### Core Functionality
- **Repository Access**: Verify Git repository connectivity
- **Worktree Operations**: Check worktree creation and management
- **Merge Capabilities**: Validate merge conflict resolution
- **Cleanup Status**: Monitor cleanup processes

#### Health Check Endpoints
```python
# Liveness check
GET /health/liveness

# Readiness check
GET /health/readiness

# Comprehensive health check
GET /health

# Repository health
GET /health/repository/{repo_name}
```

#### Example Response
```json
{
  "service": "git-worktree",
  "status": "healthy",
  "timestamp": "2025-08-03T01:00:00.000Z",
  "checks": {
    "repository_access": {
      "status": "healthy",
      "message": "All repositories accessible",
      "repositories": {
        "main": "accessible",
        "staging": "accessible",
        "feature": "accessible"
      }
    },
    "worktree_operations": {
      "status": "healthy",
      "message": "Worktree operations normal",
      "active_worktrees": 3
    },
    "merge_capabilities": {
      "status": "healthy",
      "message": "Merge capabilities functioning",
      "merge_success_rate": 0.97
    }
  }
}
```

### Workflow Orchestrator Health Checks

#### Core Functionality
- **Workflow Execution**: Monitor workflow execution processes
- **Agent Coordination**: Check inter-agent communication
- **Step Processing**: Verify step execution and transitions
- **Error Recovery**: Validate error handling and recovery

#### Health Check Endpoints
```python
# Liveness check
GET /health/liveness

# Readiness check
GET /health/readiness

# Comprehensive health check
GET /health

# Workflow health
GET /health/workflow/{workflow_id}
```

#### Example Response
```json
{
  "service": "workflow-orchestrator",
  "status": "healthy",
  "timestamp": "2025-08-03T01:00:00.000Z",
  "checks": {
    "workflow_execution": {
      "status": "healthy",
      "message": "Workflow execution normal",
      "active_workflows": 5,
      "completed_workflows": 142
    },
    "agent_coordination": {
      "status": "healthy",
      "message": "Agent coordination working",
      "coordination_latency": 0.5
    },
    "step_processing": {
      "status": "healthy",
      "message": "Step processing operational",
      "step_success_rate": 0.96
    }
  }
}
```

### Verification Feedback Health Checks

#### Core Functionality
- **Code Analysis**: Verify code analysis capabilities
- **Security Scanning**: Check security scanning functionality
- **Quality Assessment**: Monitor quality assessment processes
- **Verification Status**: Track verification completion rates

#### Health Check Endpoints
```python
# Liveness check
GET /health/liveness

# Readiness check
GET /health/readiness

# Comprehensive health check
GET /health

# Verification health
GET /health/verification/{verification_id}
```

#### Example Response
```json
{
  "service": "verification-feedback",
  "status": "healthy",
  "timestamp": "2025-08-03T01:00:00.000Z",
  "checks": {
    "code_analysis": {
      "status": "healthy",
      "message": "Code analysis functioning",
      "analysis_accuracy": 0.94
    },
    "security_scanning": {
      "status": "healthy",
      "message": "Security scanning operational",
      "vulnerabilities_detected": 2
    },
    "quality_assessment": {
      "status": "healthy",
      "message": "Quality assessment working",
      "quality_score": 8.5
    }
  }
}
```

## Health Aggregation

### System Health Report

The health aggregation service collects health data from all services and provides a comprehensive system health report.

#### Endpoints
```python
# Get system health
GET /health/system

# Get health history
GET /health/history?hours=24

# Get service health trend
GET /health/trend/{service_name}?hours=24
```

#### Example System Health Response
```json
{
  "timestamp": "2025-08-03T01:00:00.000Z",
  "overall_status": "healthy",
  "total_services": 5,
  "healthy_services": 4,
  "degraded_services": 1,
  "unhealthy_services": 0,
  "error_services": 0,
  "service_summaries": [
    {
      "service_name": "model-router",
      "overall_status": "healthy",
      "healthy_checks": 4,
      "degraded_checks": 0,
      "unhealthy_checks": 0,
      "error_checks": 0,
      "total_checks": 4,
      "last_updated": "2025-08-03T01:00:00.000Z",
      "critical_issues": [],
      "warnings": []
    }
  ],
  "system_issues": [],
  "recommendations": [
    "System is healthy. Continue monitoring."
  ],
  "uptime_percentage": 99.8,
  "response_time_avg_ms": 45.2
}
```

## Monitoring and Alerting

### Alert Rules

Alert rules define conditions that trigger notifications when health issues are detected.

#### Default Alert Rules
1. **Service Down**: Critical alert when service status is error
2. **Service Unhealthy**: Error alert when service status is unhealthy
3. **Service Degraded**: Warning alert when service status is degraded
4. **System Degraded**: Warning alert when overall system status is degraded
5. **System Unhealthy**: Error alert when overall system status is unhealthy
6. **High Error Rate**: Error alert when error rate exceeds 10%
7. **Slow Response**: Warning alert when response time exceeds 5 seconds
8. **Resource Exhaustion**: Error alert when resource usage exceeds 90%

#### Alert Management Endpoints
```python
# Get active alerts
GET /alerts

# Get alert history
GET /alerts/history?hours=24

# Get alert rules
GET /alerts/rules

# Add alert rule
POST /alerts/rules

# Update alert rule
PUT /alerts/rules/{rule_name}

# Delete alert rule
DELETE /alerts/rules/{rule_name}
```

#### Example Alert Rule
```json
{
  "name": "high_error_rate",
  "enabled": true,
  "condition": "error_rate > 0.1",
  "severity": "error",
  "alert_type": "high_error_rate",
  "threshold": 0.1,
  "duration": 300,
  "services": [],
  "notification_channels": ["email", "slack"]
}
```

### Notification Channels

The system supports multiple notification channels:

1. **Email**: SMTP-based email notifications
2. **Slack**: Slack webhook integration
3. **PagerDuty**: PagerDuty incident management
4. **Webhook**: Custom webhook notifications

## Testing and Validation

### Test Suites

The framework includes comprehensive test suites for validating health check functionality:

1. **Basic Health Checks**: Tests for basic health check functionality
2. **Health Checker Functionality**: Tests for health checker operations
3. **Health Aggregator**: Tests for health aggregation functionality
4. **Health Monitoring**: Tests for monitoring and alerting
5. **Integration Tests**: End-to-end integration tests

#### Testing Endpoints
```python
# Run tests
POST /tests/run

# Get test results
GET /tests/results

# Get test summary
GET /tests/summary

# Benchmark health checks
POST /tests/benchmark

# Load test health aggregator
POST /tests/load
```

### Performance Testing

The framework includes performance testing capabilities:

1. **Benchmarking**: Measure individual health check performance
2. **Load Testing**: Test system performance under load
3. **Stress Testing**: Validate system behavior under stress

## Configuration

### Health Check Configuration

Health checks can be configured through YAML files:

```yaml
# config/health_checks.yml
health_checks:
  check_interval: 30  # seconds
  timeout: 10  # seconds
  retry_attempts: 3
  
  # Service-specific configurations
  services:
    model-router:
      check_interval: 15
      timeout: 5
      
    plan-management:
      check_interval: 30
      timeout: 10
      
    git-worktree:
      check_interval: 60
      timeout: 15
      
    workflow-orchestrator:
      check_interval: 20
      timeout: 8
      
    verification-feedback:
      check_interval: 45
      timeout: 12
```

### Alert Configuration

Alert rules can be configured through YAML files:

```yaml
# config/alert_rules.yml
alert_rules:
  - name: service_down
    enabled: true
    condition: "service_status == 'error'"
    severity: critical
    alert_type: service_down
    threshold: 1.0
    duration: 60
    services: []
    notification_channels: [email, slack, pagerduty]
    
  - name: high_error_rate
    enabled: true
    condition: "error_rate > 0.1"
    severity: error
    alert_type: high_error_rate
    threshold: 0.1
    duration: 300
    services: []
    notification_channels: [email, slack]
```

## Deployment

### Kubernetes Deployment

The health check service can be deployed as a Kubernetes deployment:

```yaml
# kubernetes/health-service-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: health-service
  labels:
    app: health-service
spec:
  replicas: 2
  selector:
    matchLabels:
      app: health-service
  template:
    metadata:
      labels:
        app: health-service
    spec:
      containers:
      - name: health-service
        image: mcp/health-service:latest
        ports:
        - containerPort: 8006
        env:
        - name: ENVIRONMENT
          value: "production"
        - name: LOG_LEVEL
          value: "info"
        livenessProbe:
          httpGet:
            path: /health/liveness
            port: 8006
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health/readiness
            port: 8006
          initialDelaySeconds: 5
          periodSeconds: 5
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
```

### Service Configuration

```yaml
# kubernetes/health-service-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: health-service
  labels:
    app: health-service
spec:
  selector:
    app: health-service
  ports:
  - protocol: TCP
    port: 8006
    targetPort: 8006
  type: ClusterIP
```

## Monitoring Integration

### Prometheus Integration

The health check service exposes metrics for Prometheus:

```yaml
# monitoring/prometheus.yml
scrape_configs:
  - job_name: 'health-service'
    static_configs:
      - targets: ['health-service:8006']
    metrics_path: '/metrics'
    scrape_interval: 30s
```

### Grafana Dashboard

A pre-configured Grafana dashboard is available for visualizing health check metrics:

1. **System Health Overview**: Overall system health status
2. **Service Health Details**: Individual service health metrics
3. **Alert History**: Historical alert data
4. **Performance Metrics**: Response times and throughput
5. **Resource Usage**: System resource utilization

## Best Practices

### Health Check Implementation

1. **Keep it Simple**: Health checks should be fast and reliable
2. **Use Timeouts**: Always implement timeouts for health checks
3. **Handle Failures Gracefully**: Provide meaningful error messages
4. **Monitor Dependencies**: Check external dependencies
5. **Test Thoroughly**: Validate health check functionality

### Alert Configuration

1. **Set Appropriate Thresholds**: Avoid alert fatigue with proper thresholds
2. **Use Multiple Channels**: Configure multiple notification channels
3. **Implement Escalation**: Set up alert escalation policies
4. **Test Alerts**: Regularly test alert functionality
5. **Review and Update**: Periodically review and update alert rules

### Monitoring Strategy

1. **Monitor Everything**: Monitor all critical components
2. **Use Dashboards**: Create visual dashboards for monitoring
3. **Set Up Alerts**: Configure alerts for critical issues
4. **Review Metrics**: Regularly review monitoring metrics
5. **Optimize Performance**: Use metrics to optimize performance

## Troubleshooting

### Common Issues

1. **Health Check Timeouts**: Increase timeout values or optimize health check performance
2. **False Alerts**: Adjust alert thresholds or conditions
3. **Missing Metrics**: Verify metrics collection and configuration
4. **Notification Failures**: Check notification channel configuration
5. **Performance Issues**: Use benchmarking to identify bottlenecks

### Debug Commands

```bash
# Check health service logs
kubectl logs -f deployment/health-service

# Test health check endpoints
curl http://health-service:8006/health
curl http://health-service:8006/health/liveness
curl http://health-service:8006/health/readiness

# Check service health
kubectl get pods -l app=health-service
kubectl describe pod <pod-name>

# Check metrics
curl http://health-service:8006/metrics
```

## API Reference

### Health Check Endpoints

#### GET /health
Get comprehensive health check for all services.

**Response:**
```json
{
  "timestamp": "2025-08-03T01:00:00.000Z",
  "overall_status": "healthy",
  "service_summaries": [...]
}
```

#### GET /health/liveness
Get liveness status.

**Response:**
```json
{
  "service": "health-service",
  "status": "alive",
  "timestamp": "2025-08-03T01:00:00.000Z"
}
```

#### GET /health/readiness
Get readiness status.

**Response:**
```json
{
  "service": "health-service",
  "status": "ready",
  "timestamp": "2025-08-03T01:00:00.000Z"
}
```

### Alert Management Endpoints

#### GET /alerts
Get active alerts.

**Parameters:**
- `severity` (optional): Filter by severity level
- `alert_type` (optional): Filter by alert type

**Response:**
```json
{
  "alerts": [...],
  "total_count": 0
}
```

#### POST /alerts/rules
Add a new alert rule.

**Request Body:**
```json
{
  "name": "custom_alert",
  "enabled": true,
  "condition": "error_rate > 0.05",
  "severity": "warning",
  "alert_type": "high_error_rate",
  "threshold": 0.05,
  "duration": 300,
  "services": [],
  "notification_channels": ["email"]
}
```

### Testing Endpoints

#### POST /tests/run
Run health check tests.

**Request Body:**
```json
{
  "suite_name": "basic_health_checks",
  "iterations": 100,
  "concurrent_requests": 50
}
```

#### GET /tests/results
Get test results.

**Parameters:**
- `suite_name` (optional): Filter by test suite name

**Response:**
```json
{
  "suite_name": "basic_health_checks",
  "total_tests": 4,
  "passed_tests": 4,
  "failed_tests": 0,
  "success_rate": 1.0
}
```

## Conclusion

The MCP Health Check Framework provides a comprehensive solution for monitoring and managing the health of all MCP services. With its modular architecture, extensive testing capabilities, and integration with monitoring systems, it ensures the reliability and performance of the entire MCP ecosystem.

For more information or assistance with implementation, please refer to the source code documentation or contact the development team.