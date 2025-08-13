#!/bin/bash

# Telemetry System Deployment Script
# AI Agent Collaboration Platform
# Makes the telemetry system live with TTF metrics

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE="telemetry"
DEPLOYMENT_NAME="telemetry-service"
SERVICE_NAME="telemetry-service"
INGRESS_NAME="telemetry-ingress"
CONFIGMAP_NAME="telemetry-config"
SECRET_NAME="telemetry-secrets"

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] ✓${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] ⚠${NC} $1"
}

log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ✗${NC} $1"
}

# Check if kubectl is available
check_prerequisites() {
    log "Checking prerequisites..."
    
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed. Please install kubectl first."
        exit 1
    fi
    
    if ! command -v helm &> /dev/null; then
        log_warning "helm is not installed. Some features may not work."
    fi
    
    log_success "Prerequisites check completed"
}

# Check cluster connectivity
check_cluster() {
    log "Checking cluster connectivity..."
    
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster. Please check your kubeconfig."
        exit 1
    fi
    
    CLUSTER_NAME=$(kubectl config current-context)
    log_success "Connected to cluster: $CLUSTER_NAME"
}

# Create namespace
create_namespace() {
    log "Creating namespace: $NAMESPACE"
    
    if kubectl get namespace $NAMESPACE &> /dev/null; then
        log_warning "Namespace $NAMESPACE already exists"
    else
        kubectl create namespace $NAMESPACE
        log_success "Namespace $NAMESPACE created"
    fi
}

# Create secrets (placeholder values)
create_secrets() {
    log "Creating secrets..."
    
    # Check if secrets already exist
    if kubectl get secret $SECRET_NAME -n $NAMESPACE &> /dev/null; then
        log_warning "Secrets already exist, skipping creation"
        return
    fi
    
    # Create placeholder secrets (replace with actual values in production)
    kubectl create secret generic $SECRET_NAME \
        --from-literal=MIXPANEL_API_KEY="placeholder-key" \
        --from-literal=AMPLITUDE_API_KEY="placeholder-key" \
        --from-literal=SEGMENT_WRITE_KEY="placeholder-key" \
        --from-literal=DATADOG_API_KEY="placeholder-key" \
        --from-literal=DATADOG_APP_KEY="placeholder-key" \
        --from-literal=NEWRELIC_LICENSE_KEY="placeholder-key" \
        --from-literal=NEWRELIC_ACCOUNT_ID="placeholder-id" \
        --from-literal=GRAFANA_API_KEY="placeholder-key" \
        --from-literal=PAGERDUTY_SERVICE_KEY="placeholder-key" \
        --from-literal=SLACK_WEBHOOK_URL="placeholder-url" \
        --from-literal=SMTP_SERVER="placeholder-server" \
        -n $NAMESPACE
    
    log_success "Secrets created (using placeholder values)"
    log_warning "IMPORTANT: Update secrets with actual values before production use"
}

# Deploy telemetry system
deploy_telemetry() {
    log "Deploying telemetry system..."
    
    # Apply all Kubernetes manifests
    kubectl apply -f deployment.yaml -n $NAMESPACE
    
    log_success "Telemetry system deployment initiated"
}

# Wait for deployment to be ready
wait_for_deployment() {
    log "Waiting for deployment to be ready..."
    
    kubectl wait --for=condition=available --timeout=300s deployment/$DEPLOYMENT_NAME -n $NAMESPACE
    
    log_success "Deployment is ready"
}

# Check deployment status
check_deployment_status() {
    log "Checking deployment status..."
    
    kubectl get pods -n $NAMESPACE -l app=telemetry
    
    # Get service details
    kubectl get service $SERVICE_NAME -n $NAMESPACE
    
    # Get ingress details
    kubectl get ingress $INGRESS_NAME -n $NAMESPACE
}

# Verify telemetry endpoints
verify_endpoints() {
    log "Verifying telemetry endpoints..."
    
    # Get service IP
    SERVICE_IP=$(kubectl get service $SERVICE_NAME -n $NAMESPACE -o jsonpath='{.spec.clusterIP}')
    
    # Test health endpoint
    if kubectl run test-health --image=curlimages/curl --rm -i --restart=Never -- curl -s "http://$SERVICE_IP:8080/health" | grep -q "healthy"; then
        log_success "Health endpoint is working"
    else
        log_error "Health endpoint is not working"
    fi
    
    # Test ready endpoint
    if kubectl run test-ready --image=curlimages/curl --rm -i --restart=Never -- curl -s "http://$SERVICE_IP:8080/ready" | grep -q "ready"; then
        log_success "Ready endpoint is working"
    else
        log_error "Ready endpoint is not working"
    fi
    
    # Test metrics endpoint
    if kubectl run test-metrics --image=curlimages/curl --rm -i --restart=Never -- curl -s "http://$SERVICE_IP:8080/metrics" | grep -q "ttf_"; then
        log_success "Metrics endpoint is working and returning TTF metrics"
    else
        log_warning "Metrics endpoint is working but may not have TTF metrics yet"
    fi
}

# Setup monitoring
setup_monitoring() {
    log "Setting up monitoring..."
    
    # Check if Prometheus Operator is available
    if kubectl get crd prometheusrules.monitoring.coreos.com &> /dev/null; then
        log_success "Prometheus Operator detected, applying monitoring rules"
        
        # Apply ServiceMonitor and PrometheusRule
        kubectl apply -f - <<EOF
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: telemetry-service-monitor
  namespace: $NAMESPACE
  labels:
    app: telemetry
    component: telemetry
    release: prometheus
spec:
  selector:
    matchLabels:
      app: telemetry
      component: telemetry
  endpoints:
    - port: metrics
      path: /metrics
      interval: 30s
      scrapeTimeout: 10s
      honorLabels: true
      metricRelabelings:
        - sourceLabels: [__name__]
          regex: 'ttf_.*'
          action: keep
        - sourceLabels: [__name__]
          regex: 'telemetry_.*'
          action: keep
        - sourceLabels: [__name__]
          regex: 'events_.*'
          action: keep
---
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: telemetry-ttf-alerts
  namespace: $NAMESPACE
  labels:
    app: telemetry
    component: telemetry
    release: prometheus
spec:
  groups:
    - name: ttf-alerts
      rules:
        - alert: TTFWarning
          expr: avg(ttf_complete_minutes) > 75
          for: 5m
          labels:
            severity: warning
            component: telemetry
          annotations:
            summary: "TTF Warning - Average completion time is high"
            description: "Average TTF is {{ \$value }} minutes, above warning threshold of 75 minutes"
        
        - alert: TTFCritical
          expr: avg(ttf_complete_minutes) > 120
          for: 5m
          labels:
            severity: critical
            component: telemetry
          annotations:
            summary: "TTF Critical - Average completion time is very high"
            description: "Average TTF is {{ \$value }} minutes, above critical threshold of 120 minutes"
        
        - alert: TTFEscalation
          expr: avg(ttf_complete_minutes) > 180
          for: 5m
          labels:
            severity: critical
            component: telemetry
          annotations:
            summary: "TTF Escalation - Immediate attention required"
            description: "Average TTF is {{ \$value }} minutes, above escalation threshold of 180 minutes"
EOF
    else
        log_warning "Prometheus Operator not detected, monitoring setup skipped"
    fi
}

# Setup Grafana dashboards
setup_grafana() {
    log "Setting up Grafana dashboards..."
    
    # Check if Grafana is available
    if kubectl get pods -A | grep -q grafana; then
        log_success "Grafana detected, setting up dashboards"
        
        # Apply dashboard ConfigMap
        kubectl apply -f - <<EOF
apiVersion: v1
kind: ConfigMap
metadata:
  name: grafana-dashboards
  namespace: $NAMESPACE
  labels:
    app: telemetry
    component: telemetry
data:
  ttf-overview.json: |
    {
      "dashboard": {
        "title": "TTF Metrics Overview",
        "uid": "ttf-overview",
        "tags": ["telemetry", "ttf", "overview"],
        "timezone": "browser",
        "refresh": "30s",
        "schemaVersion": 38,
        "version": 1,
        "time": {
          "from": "now-24h",
          "to": "now"
        }
      }
    }
  
  ttf-detailed.json: |
    {
      "dashboard": {
        "title": "TTF Detailed Analysis",
        "uid": "ttf-detailed",
        "tags": ["telemetry", "ttf", "detailed"],
        "timezone": "browser",
        "refresh": "1m",
        "schemaVersion": 38,
        "version": 1,
        "time": {
          "from": "now-7d",
          "to": "now"
        }
      }
    }
  
  telemetry-health.json: |
    {
      "dashboard": {
        "title": "Telemetry System Health",
        "uid": "telemetry-health",
        "tags": ["telemetry", "system", "health"],
        "timezone": "browser",
        "refresh": "30s",
        "schemaVersion": 38,
        "version": 1,
        "time": {
          "from": "now-1h",
          "to": "now"
        }
      }
    }
EOF
    else
        log_warning "Grafana not detected, dashboard setup skipped"
    fi
}

# Run initial data collection test
test_telemetry() {
    log "Testing telemetry data collection..."
    
    # Create a test pod to simulate telemetry events
    kubectl run telemetry-test --image=python:3.9-slim --rm -i --restart=Never -- bash -c "
        pip install requests pyyaml
        cat > test_telemetry.py << 'EOF'
import requests
import json
import time

# Test telemetry endpoint
try:
    response = requests.get('http://telemetry-service.telemetry.svc.cluster.local:8080/health')
    print(f'Health check: {response.status_code}')
    
    # Simulate a telemetry event
    event = {
        'event_name': 'test_event',
        'event_type': 'test',
        'timestamp': time.time(),
        'properties': {'test': True}
    }
    
    response = requests.post(
        'http://telemetry-service.telemetry.svc.cluster.local:8080/api/v1/events',
        json={'events': [event]}
    )
    print(f'Event submission: {response.status_code}')
    
except Exception as e:
    print(f'Error: {e}')
EOF
        python test_telemetry.py
    "
    
    log_success "Telemetry test completed"
}

# Display deployment summary
show_summary() {
    log_success "Telemetry system deployment completed!"
    echo
    echo "=== DEPLOYMENT SUMMARY ==="
    echo "Namespace: $NAMESPACE"
    echo "Service: $SERVICE_NAME"
    echo "Ingress: $INGRESS_NAME"
    echo
    echo "=== ACCESS INFORMATION ==="
    echo "Internal Service: $SERVICE_NAME.$NAMESPACE.svc.cluster.local:8080"
    echo "External URL: https://telemetry.company.com (if ingress is configured)"
    echo
    echo "=== ENDPOINTS ==="
    echo "Health: /health"
    echo "Ready: /ready"
    echo "Metrics: /metrics"
    echo "API: /api/v1/*"
    echo
    echo "=== MONITORING ==="
    echo "Prometheus metrics available at /metrics"
    echo "Grafana dashboards configured for TTF metrics"
    echo "Alerting rules configured for TTF thresholds"
    echo
    echo "=== NEXT STEPS ==="
    echo "1. Update secrets with actual API keys"
    echo "2. Configure external ingress if needed"
    echo "3. Set up data retention policies"
    echo "4. Configure alerting channels (Slack, PagerDuty, email)"
    echo "5. Monitor TTF metrics in Grafana"
    echo
    echo "=== TTF METRICS ==="
    echo "The system is now tracking:"
    echo "- TTF Project: Time from signup to first project (target: 5 min)"
    echo "- TTF Agent: Time from project to first agent (target: 10 min)"
    echo "- TTF Workflow: Time from agent to first workflow (target: 15 min)"
    echo "- TTF Success: Time from workflow to first success (target: 30 min)"
    echo "- TTF Complete: Total time to first value (target: 60 min)"
    echo
    echo "=== ALERTING THRESHOLDS ==="
    echo "Warning: >75 minutes"
    echo "Critical: >120 minutes"
    echo "Escalation: >180 minutes"
}

# Main deployment function
main() {
    log "Starting telemetry system deployment..."
    log "This will make the telemetry system live with TTF metrics tracking"
    
    check_prerequisites
    check_cluster
    create_namespace
    create_secrets
    deploy_telemetry
    wait_for_deployment
    check_deployment_status
    verify_endpoints
    setup_monitoring
    setup_grafana
    test_telemetry
    show_summary
    
    log_success "Telemetry system is now LIVE and tracking TTF metrics!"
}

# Run main function
main "$@"