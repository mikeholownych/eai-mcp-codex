# Telemetry System with TTF Metrics

## Overview

The AI Agent Collaboration Platform Telemetry System is a production-ready, enterprise-grade telemetry solution that tracks Time-to-First-Value (TTF) metrics in real-time. This system provides comprehensive visibility into user onboarding success, performance bottlenecks, and business impact.

## 🎯 What This System Tracks

### TTF Journey Stages
1. **Signup to First Project** (Target: 5 minutes)
2. **First Project to First Agent** (Target: 10 minutes)  
3. **First Agent to First Workflow** (Target: 15 minutes)
4. **First Workflow to First Success** (Target: 30 minutes)
5. **Total TTF** (Target: 60 minutes)

### Key Metrics
- **TTF Completion Rate**: Percentage of users who complete the full journey
- **TTF Efficiency Score**: Weighted score based on completion time vs. targets
- **TTF Distribution**: Histogram of completion times across user segments
- **Real-time Alerts**: Automated notifications when TTF exceeds thresholds

## 🏗️ Architecture

### Components
- **Telemetry Client**: Python client for event tracking and TTF calculation
- **Telemetry Service**: Kubernetes-deployed service with REST API
- **Data Storage**: TimescaleDB (primary), S3 (archival), Redis (cache)
- **Monitoring**: Prometheus metrics, Grafana dashboards, alerting rules
- **Integrations**: Mixpanel, Amplitude, Segment, Datadog, New Relic

### Data Flow
```
User Action → Telemetry Client → Event Validation → PII Masking → 
Enrichment → Storage → TTF Calculation → Metrics → Dashboards → Alerts
```

## 🚀 Quick Start

### Prerequisites
- Kubernetes cluster (1.20+)
- kubectl configured
- Helm (optional, for advanced features)

### 1. Deploy the System
```bash
cd launch/telemetry
./deploy.sh
```

### 2. Verify Deployment
```bash
kubectl get pods -n telemetry
kubectl get service telemetry-service -n telemetry
```

### 3. Test Endpoints
```bash
# Health check
curl http://telemetry-service.telemetry.svc.cluster.local:8080/health

# Metrics
curl http://telemetry-service.telemetry.svc.cluster.local:8080/metrics

# API
curl -X POST http://telemetry-service.telemetry.svc.cluster.local:8080/api/v1/events \
  -H "Content-Type: application/json" \
  -d '{"events":[{"event_name":"test","event_type":"test"}]}'
```

## 📊 Using the Telemetry Client

### Basic Usage
```python
from telemetry.client import TelemetryClient

# Initialize client
client = TelemetryClient()

# Track user actions
client.track_event(
    event_name="project_created",
    event_type="user_action",
    user_id="user_123",
    properties={"project_name": "My AI Project"}
)

# Track TTF milestones
client.track_ttf_milestone("first_project_created", user_id="user_123")
client.track_ttf_milestone("first_agent_created", user_id="user_123")
client.track_ttf_milestone("first_workflow_executed", user_id="user_123")
client.track_ttf_milestone("first_success_event", user_id="user_123")

# Flush events
client.flush_events()
```

### TTF Tracking
```python
# The client automatically tracks TTF progression
# Each milestone updates the TTF metrics

# Check TTF status
ttf_metrics = client.get_ttf_metrics("user_123")
print(f"TTF Complete: {ttf_metrics.ttf_complete_minutes} minutes")
print(f"Efficiency Score: {ttf_metrics.ttf_efficiency_score}")

# Get TTF alerts
alerts = client.check_ttf_alerts("user_123")
if alerts:
    print(f"TTF Alert: {alerts[0].message}")
```

## 🔧 Configuration

### Environment Variables
```bash
# Required
TELEMETRY_API_URL=https://telemetry.company.com
TELEMETRY_API_KEY=your-api-key

# Optional (for integrations)
MIXPANEL_API_KEY=your-mixpanel-key
AMPLITUDE_API_KEY=your-amplitude-key
SEGMENT_WRITE_KEY=your-segment-key
DATADOG_API_KEY=your-datadog-key
NEWRELIC_LICENSE_KEY=your-newrelic-key
GRAFANA_API_KEY=your-grafana-key
PAGERDUTY_SERVICE_KEY=your-pagerduty-key
SLACK_WEBHOOK_URL=your-slack-webhook
```

### Configuration File
The system uses `config.yaml` for comprehensive configuration:
- Sampling rates and batching
- PII detection and masking
- Storage and retention policies
- Performance thresholds
- Alerting rules

## 📈 Monitoring & Dashboards

### Grafana Dashboards
1. **TTF Metrics Overview**: High-level TTF completion and trends
2. **TTF Detailed Analysis**: Deep dive into user segments and channels
3. **Telemetry System Health**: System performance and error rates

### Prometheus Metrics
- `ttf_complete_minutes`: Total TTF time
- `ttf_efficiency_score`: Weighted efficiency score
- `ttf_completion_total`: Number of completed journeys
- `telemetry_events_total`: Total events processed
- `telemetry_errors_total`: Error count

### Alerting Rules
- **TTF Warning**: >75 minutes (5 minutes)
- **TTF Critical**: >120 minutes (5 minutes)
- **TTF Escalation**: >180 minutes (5 minutes)
- **Service Down**: Service unavailable (1 minute)
- **High Error Rate**: >0.1 errors/sec (2 minutes)
- **High Latency**: >0.5s 95th percentile (5 minutes)

## 🔒 Security & Compliance

### Data Protection
- **PII Detection**: Automatic identification of personal data
- **Data Masking**: Hashing and encryption of sensitive fields
- **Encryption**: AES-256-GCM for data at rest and in transit
- **Access Control**: RBAC with audit logging

### Compliance
- **GDPR**: Data residency, right to deletion, consent management
- **CCPA**: California privacy compliance
- **SOX**: Financial reporting compliance
- **Data Residency**: Configurable storage locations

## 📊 Performance & Scaling

### Resource Requirements
- **CPU**: 250m request, 1000m limit per pod
- **Memory**: 256Mi request, 1Gi limit per pod
- **Replicas**: 2-10 pods with HPA
- **Storage**: 1GB per pod for logs and cache

### Scaling Behavior
- **CPU-based**: Scales up at 70% utilization
- **Memory-based**: Scales up at 80% utilization
- **Scale Down**: 10% reduction every 60 seconds
- **Scale Up**: 100% increase every 15 seconds

## 🚨 Troubleshooting

### Common Issues

#### Service Not Starting
```bash
# Check pod status
kubectl get pods -n telemetry

# Check logs
kubectl logs -n telemetry -l app=telemetry

# Check events
kubectl get events -n telemetry --sort-by='.lastTimestamp'
```

#### Metrics Not Appearing
```bash
# Verify Prometheus scraping
kubectl get servicemonitor -n telemetry

# Check metrics endpoint
curl http://telemetry-service.telemetry.svc.cluster.local:8080/metrics

# Verify ServiceMonitor labels
kubectl get servicemonitor telemetry-service-monitor -n telemetry -o yaml
```

#### TTF Alerts Not Firing
```bash
# Check PrometheusRule
kubectl get prometheusrule -n telemetry

# Verify alerting rules
kubectl get prometheusrule telemetry-ttf-alerts -n telemetry -o yaml

# Check Prometheus targets
kubectl port-forward -n monitoring svc/prometheus-operated 9090:9090
# Then visit http://localhost:9090/targets
```

### Debug Mode
```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Enable client debug mode
client = TelemetryClient(debug=True)
```

## 🔄 Maintenance

### Data Retention
- **Real-time Data**: 30 days
- **Analytics Data**: 1 year
- **Compliance Data**: 7 years
- **Archived Data**: 10 years

### Backup & Recovery
- **Daily Backups**: Automated S3 archival
- **Point-in-time Recovery**: TimescaleDB continuous backups
- **Disaster Recovery**: Multi-region S3 replication

### Updates
```bash
# Update deployment
kubectl set image deployment/telemetry-service \
  telemetry-service=ai-agent-collaboration/telemetry:latest \
  -n telemetry

# Rollback if needed
kubectl rollout undo deployment/telemetry-service -n telemetry
```

## 📚 API Reference

### Endpoints

#### POST /api/v1/events
Submit telemetry events
```json
{
  "events": [
    {
      "event_name": "string",
      "event_type": "string",
      "user_id": "string",
      "timestamp": "number",
      "properties": "object"
    }
  ]
}
```

#### GET /api/v1/ttf/{user_id}
Get TTF metrics for a user
```json
{
  "user_id": "string",
  "ttf_project_minutes": "number",
  "ttf_agent_minutes": "number",
  "ttf_workflow_minutes": "number",
  "ttf_success_minutes": "number",
  "ttf_complete_minutes": "number",
  "ttf_efficiency_score": "number"
}
```

#### GET /metrics
Prometheus metrics endpoint

#### GET /health
Health check endpoint

#### GET /ready
Readiness check endpoint

## 🎯 Best Practices

### Event Design
- Use consistent event naming (`snake_case`)
- Include relevant properties for analysis
- Avoid PII in event names
- Use appropriate event types

### TTF Optimization
- Set realistic targets based on user research
- Monitor segment-specific performance
- A/B test onboarding flows
- Use TTF data to prioritize product improvements

### Performance
- Batch events when possible
- Use appropriate sampling rates
- Monitor client-side performance impact
- Implement circuit breakers for failures

## 🔗 Integration Examples

### React/Next.js
```typescript
import { TelemetryClient } from '@company/telemetry-client';

const telemetry = new TelemetryClient({
  apiUrl: process.env.TELEMETRY_API_URL,
  apiKey: process.env.TELEMETRY_API_KEY,
});

// Track user actions
telemetry.trackEvent('button_clicked', {
  button_id: 'create_project',
  page: 'dashboard',
});

// Track TTF milestones
telemetry.trackTTFMilestone('first_project_created');
```

### Python Backend
```python
from telemetry.client import TelemetryClient

telemetry = TelemetryClient()

@app.route('/api/projects', methods=['POST'])
def create_project():
    # Create project logic...
    
    # Track TTF milestone
    telemetry.track_ttf_milestone(
        "first_project_created", 
        user_id=current_user.id
    )
    
    return jsonify({"success": True})
```

### Mobile (React Native)
```typescript
import { TelemetryClient } from '@company/telemetry-client-react-native';

const telemetry = new TelemetryClient({
  apiUrl: Config.TELEMETRY_API_URL,
  apiKey: Config.TELEMETRY_API_KEY,
});

// Track app usage
telemetry.trackEvent('app_opened', {
  platform: Platform.OS,
  version: Config.APP_VERSION,
});
```

## 📞 Support

### Getting Help
- **Documentation**: This README and inline code comments
- **Issues**: GitHub issues for bugs and feature requests
- **Discussions**: GitHub discussions for questions and ideas
- **Slack**: #telemetry-support channel

### Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This telemetry system is part of the AI Agent Collaboration Platform and is licensed under the same terms as the main project.

---

**Status**: ✅ Production Ready  
**Last Updated**: $(date)  
**Version**: 1.0.0  
**Maintainer**: Platform Team