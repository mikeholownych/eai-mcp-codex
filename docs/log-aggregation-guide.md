# MCP Log Aggregation and Analysis Pipeline

This comprehensive guide covers the implementation and management of the MCP (Multimodal Content Processor) log aggregation and analysis pipeline. The pipeline provides centralized log collection, processing, storage, and analysis capabilities for all MCP services.

## Overview

The log aggregation pipeline consists of the following components:

- **Fluentd**: Log collection, processing, and routing
- **Elasticsearch**: Log storage and indexing
- **Kibana**: Log analysis and visualization
- **Prometheus**: Metrics collection and alerting
- **Grafana**: Metrics visualization
- **Alertmanager**: Alert management and notification
- **Elastic Beats**: Additional log and metrics collection

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   MCP Services  │───▶│     Fluentd     │───▶│  Elasticsearch  │
│                 │    │                 │    │                 │
│ • Model Router  │    │ • Collection    │    │ • Storage       │
│ • Plan Mgmt     │    │ • Processing    │    │ • Indexing      │
│ • Git Worktree  │    │ • Enrichment    │    │ • Search        │
│ • Workflow Orch │    │ • Routing       │    │ • ILM Policies  │
│ • Verification  │    │ • Buffering     │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       ▼                       ▼
         │              ┌─────────────────┐    ┌─────────────────┐
         │              │   Prometheus    │    │     Kibana      │
         │              │                 │    │                 │
         │              │ • Metrics       │    │ • Dashboards    │
         │              │ • Alerting      │    │ • Visualizations│
         │              │ • Recording     │    │ • Search        │
         │              │ • Rules         │    │ • Discovery     │
         │              └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       ▼                       ▼
         │              ┌─────────────────┐    ┌─────────────────┐
         └─────────────▶│  Alertmanager   │    │     Grafana     │
                        │                 │    │                 │
                        │ • Routing       │    │ • Dashboards    │
                        │ • Grouping      │    │ • Panels        │
                        │ • Notification │    │ • Alerts        │
                        │ • Silencing     │    │ • Metrics       │
                        └─────────────────┘    └─────────────────┘
```

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.8+
- Sufficient disk space for log storage
- Network access for service communication

### Installation

1. Clone the repository:
```bash
git clone https://github.com/your-org/mcp-platform.git
cd mcp-platform
```

2. Make the setup script executable:
```bash
chmod +x scripts/setup-log-aggregation.py
```

3. Initialize the pipeline:
```bash
python scripts/setup-log-aggregation.py init
```

4. Verify the installation:
```bash
python scripts/setup-log-aggregation.py health
```

### Accessing the Services

- **Kibana**: http://localhost:5601
- **Grafana**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9090
- **Alertmanager**: http://localhost:9093

## Configuration

### Fluentd Configuration

The Fluentd configuration is located in `fluentd/conf/fluent.conf`. Key features include:

- **Multi-source input**: Application logs, system logs, container logs
- **Log enrichment**: Hostname, environment, trace correlation
- **Security filtering**: Sensitive data sanitization
- **Performance metrics**: Response time, memory, CPU extraction
- **Multi-output routing**: Elasticsearch, files, cloud storage

### Elasticsearch Configuration

Elasticsearch configuration includes:

- **Index templates**: Consistent mapping across indices
- **ILM policies**: Automated index lifecycle management
- **Sharding strategies**: Optimal performance and scalability
- **Retention policies**: Compliance and storage optimization

### Kibana Configuration

Kibana provides:

- **Pre-built dashboards**: Error rates, performance metrics, security events
- **Visualizations**: Charts, graphs, tables for log analysis
- **Saved searches**: Quick access to common log patterns
- **Index patterns**: Structured log field discovery

### Prometheus Configuration

Prometheus configuration includes:

- **Log-based metrics**: Metrics extracted from log data
- **Alerting rules**: Threshold-based alerting
- **Recording rules**: Aggregated metrics computation
- **Service discovery**: Automatic service monitoring

### Alertmanager Configuration

Alertmanager provides:

- **Alert routing**: Category-based alert distribution
- **Notification channels**: Email, Slack, PagerDuty
- **Alert grouping**: Related alerts bundled together
- **Silencing**: Temporary alert suppression

## Features

### Log Collection

The pipeline collects logs from multiple sources:

- **Application logs**: Structured JSON logs from MCP services
- **System logs**: Operating system and service logs
- **Container logs**: Docker container stdout/stderr
- **Security logs**: Authentication, authorization, audit events
- **Performance logs**: Response times, resource usage

### Log Processing

Advanced log processing capabilities:

- **Parsing**: JSON, syslog, and custom format parsing
- **Enrichment**: Adding metadata, trace correlation
- **Transformation**: Field mapping, data normalization
- **Filtering**: Sensitive data redaction, noise reduction
- **Validation**: Schema validation, quality checks

### Log Storage

Scalable log storage with:

- **Elasticsearch**: Full-text search and analytics
- **Index lifecycle management**: Automated rollover and deletion
- **Sharding**: Horizontal scaling and load distribution
- **Replication**: Data redundancy and high availability
- **Compression**: Storage optimization

### Log Analysis

Comprehensive log analysis tools:

- **Kibana dashboards**: Visual log analysis
- **Saved searches**: Common log pattern discovery
- **Field extraction**: Structured data analysis
- **Aggregation**: Statistical analysis and reporting
- **Correlation**: Trace and request correlation

### Monitoring and Alerting

Proactive monitoring and alerting:

- **Metrics extraction**: Performance and business metrics
- **Threshold alerting**: Configurable alert thresholds
- **Pattern detection**: Anomaly and pattern recognition
- **Notification routing**: Multi-channel alert delivery
- **Alert management**: Grouping, silencing, escalation

### Security and Compliance

Security and compliance features:

- **Access control**: Role-based access control
- **Data encryption**: In-transit and at-rest encryption
- **Audit trails**: Complete audit logging
- **Compliance frameworks**: GDPR, HIPAA, SOX, PCI-DSS
- **Retention policies**: Configurable data retention

## Usage

### Sending Logs to the Pipeline

#### Using the Python Logging Handler

```python
from fluent import handler
import logging

# Configure Fluentd handler
fluent_handler = handler.FluentHandler('mcp', host='localhost', port=24224)
fluent_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(name)s %(levelname)s %(message)s'
))

# Get logger and add handler
logger = logging.getLogger('my-service')
logger.addHandler(fluent_handler)
logger.setLevel(logging.INFO)

# Log messages
logger.info('Service started', extra={'user_id': '123', 'operation': 'startup'})
logger.error('Processing failed', extra={'error_code': 500, 'duration': 1500})
```

#### Using the Structured Logging Configuration

```python
from src.common.logging_config import get_logger

# Get structured logger
logger = get_logger('my-service')

# Log with structured data
logger.info('Processing request', 
           request_id='req-123',
           user_id='user-456',
           operation='process_data',
           duration_ms=250)
```

#### Using Filebeat for File-based Logs

```yaml
# filebeat.yml
filebeat.inputs:
- type: log
  enabled: true
  paths:
    - /var/log/my-service/*.log
  json.keys_under_root: true
  json.add_error_key: true

output.elasticsearch:
  hosts: ["localhost:9200"]
  index: "mcp-logs-%{[agent.version]}-%{+yyyy.MM.dd}"
```

### Querying and Analyzing Logs

#### Using Kibana Discover

1. Navigate to Kibana → Discover
2. Select the `mcp-logs-*` index pattern
3. Use the search bar to filter logs
4. Add filters for specific fields
5. View and analyze log entries

#### Using Kibana Dashboards

1. Navigate to Kibana → Dashboard
2. Select a pre-built dashboard:
   - MCP Service Overview
   - Error Analysis
   - Performance Metrics
   - Security Events
   - Audit Trail
3. Interact with visualizations and filters
4. Drill down into specific time periods or services

#### Using the Elasticsearch API

```bash
# Search for errors
curl -X GET "localhost:9200/mcp-logs-*/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "match": {
      "log_level": "ERROR"
    }
  }
}
'

# Aggregate by service
curl -X GET "localhost:9200/mcp-logs-*/_search" -H 'Content-Type: application/json' -d'
{
  "size": 0,
  "aggs": {
    "services": {
      "terms": {
        "field": "service_name"
      }
    }
  }
}
'
```

### Creating Custom Dashboards

1. Navigate to Kibana → Dashboard
2. Click "Create dashboard"
3. Add visualizations:
   - Metrics: Count, average, sum, percentiles
   - Charts: Line, bar, pie, area
   - Tables: Data tables with filtering
   - Maps: Geographic visualization
4. Configure panel properties and filters
5. Save the dashboard with a descriptive name

### Setting Up Custom Alerts

1. Navigate to Kibana → Stack Management → Rules
2. Click "Create rule"
3. Select rule type:
   - Query threshold: Alert on query results
   - Index threshold: Alert on index patterns
   - Log threshold: Alert on log patterns
4. Configure alert conditions and thresholds
5. Set up notification channels
6. Configure alert actions and escalation

## Monitoring and Maintenance

### Health Checks

Regular health checks ensure pipeline reliability:

```bash
# Check service health
python scripts/setup-log-aggregation.py health

# Check Elasticsearch cluster health
curl -X GET "localhost:9200/_cluster/health"

# Check Kibana status
curl -X GET "localhost:5601/api/status"

# Check Prometheus targets
curl -X GET "localhost:9090/api/v1/targets"
```

### Performance Monitoring

Monitor key performance metrics:

- **Log ingestion rate**: Logs per second
- **Processing latency**: Time from log generation to indexing
- **Storage usage**: Disk space and index size
- **Query performance**: Search response times
- **Error rates**: Processing and indexing errors

### Backup and Recovery

Regular backups ensure data durability:

```bash
# Create Elasticsearch snapshot
curl -X PUT "localhost:9200/_snapshot/mcp_backup/snapshot_$(date +%Y%m%d)?wait_for_completion=true"

# Restore from snapshot
curl -X POST "localhost:9200/_snapshot/mcp_backup/snapshot_20231201/_restore"

# Backup configuration files
tar -czf mcp-logs-config-$(date +%Y%m%d).tar.gz fluentd/ monitoring/ config/
```

### Scaling the Pipeline

Scale components based on load:

- **Fluentd**: Add more workers, increase buffer size
- **Elasticsearch**: Add more nodes, increase heap size
- **Kibana**: Add more instances, use load balancer
- **Prometheus**: Add more instances, configure federation
- **Storage**: Add more disk space, use cloud storage

## Troubleshooting

### Common Issues

#### Fluentd Not Starting

Check Fluentd configuration syntax:

```bash
# Test configuration
fluentd --config fluentd/conf/fluent.conf --dry-run

# Check logs
docker logs mcp-fluentd
```

#### Elasticsearch Indexing Issues

Check Elasticsearch cluster health:

```bash
# Check cluster health
curl -X GET "localhost:9200/_cluster/health"

# Check index status
curl -X GET "localhost:9200/_cat/indices?v"

# Check node status
curl -X GET "localhost:9200/_cat/nodes?v"
```

#### Kibana Connection Issues

Verify Kibana configuration:

```bash
# Check Kibana logs
docker logs mcp-kibana

# Test Elasticsearch connection
curl -X GET "localhost:5601/api/elasticsearch/ping"
```

### Performance Issues

#### Slow Query Performance

Optimize Elasticsearch queries:

```bash
# Check slow logs
curl -X GET "localhost:9200/_search?pretty" -H 'Content-Type: application/json' -d'
{
  "profile": true,
  "query": {
    "match_all": {}
  }
}
'

# Optimize index settings
curl -X PUT "localhost:9200/mcp-logs-*/_settings" -H 'Content-Type: application/json' -d'
{
  "index": {
    "number_of_replicas": 1,
    "refresh_interval": "30s"
  }
}
'
```

#### High Memory Usage

Monitor and optimize memory usage:

```bash
# Check JVM heap usage
curl -X GET "localhost:9200/_cat/nodes?v&h=heap*&s=heap.current"

# Adjust heap size
export ES_JAVA_OPTS="-Xms4g -Xmx4g"
```

### Log Quality Issues

#### Missing Fields

Ensure consistent log structure:

```python
# Validate log structure
required_fields = ['timestamp', 'service_name', 'log_level', 'message']
for field in required_fields:
    if field not in log_record:
        logger.warning(f"Missing required field: {field}")
```

#### Inconsistent Timestamps

Standardize timestamp formats:

```python
# Use ISO 8601 timestamps
from datetime import datetime, timezone

timestamp = datetime.now(timezone.utc).isoformat()
log_record['timestamp'] = timestamp
```

## Security Considerations

### Access Control

Implement role-based access control:

```yaml
# Elasticsearch roles
roles:
  log_reader:
    indices:
      - names: ['mcp-logs-*']
        privileges: ['read']
  
  log_writer:
    indices:
      - names: ['mcp-logs-*']
        privileges: ['write', 'create_index']
  
  log_admin:
    indices:
      - names: ['mcp-logs-*']
        privileges: ['all']
```

### Data Encryption

Enable encryption for sensitive data:

```yaml
# Elasticsearch encryption
xpack.security.enabled: true
xpack.security.transport.ssl.enabled: true
xpack.security.http.ssl.enabled: true
```

### Audit Logging

Enable comprehensive audit logging:

```yaml
# Elasticsearch audit logging
xpack.security.audit.enabled: true
xpack.security.audit.logfile.events.include: ['access_granted', 'access_denied']
```

## Best Practices

### Log Structure

Use consistent log structure:

```json
{
  "timestamp": "2023-12-01T10:00:00Z",
  "service_name": "model-router",
  "service_version": "1.0.0",
  "log_level": "INFO",
  "message": "Request processed successfully",
  "request_id": "req-123",
  "trace_id": "trace-456",
  "span_id": "span-789",
  "user_id": "user-abc",
  "operation": "process_request",
  "duration_ms": 250,
  "status_code": 200,
  "metadata": {
    "environment": "production",
    "region": "us-east-1"
  }
}
```

### Log Levels

Use appropriate log levels:

- **DEBUG**: Detailed diagnostic information
- **INFO**: Normal operational information
- **WARNING**: Potentially harmful situations
- **ERROR**: Error events that might still allow continued operation
- **CRITICAL**: Very severe errors that might cause the application to terminate

### Performance Optimization

Optimize for performance:

- Use appropriate index sharding strategies
- Implement index lifecycle management
- Optimize query patterns and filters
- Monitor and adjust resource allocation
- Use caching for frequent queries

### Cost Optimization

Optimize costs:

- Implement data retention policies
- Use tiered storage (hot, warm, cold)
- Compress archived data
- Monitor and optimize resource usage
- Use cloud storage for long-term archival

## API Reference

### Fluentd API

#### Input Sources

```xml
<!-- Forward input -->
<source>
  @type forward
  port 24224
  bind 0.0.0.0
</source>

<!-- Tail input -->
<source>
  @type tail
  path /var/log/*.log
  pos_file /var/log/fluentd/log.pos
  format json
</source>
```

#### Output Destinations

```xml
<!-- Elasticsearch output -->
<match mcp.**>
  @type elasticsearch
  host localhost
  port 9200
  index_name mcp-logs-${tag}
  type_name _doc
</match>
```

### Elasticsearch API

#### Index Management

```bash
# Create index
PUT /mcp-logs-2023.12.01
{
  "settings": {
    "number_of_shards": 3,
    "number_of_replicas": 1
  }
}

# Delete index
DELETE /mcp-logs-2023.12.01

# Get index settings
GET /mcp-logs-2023.12.01/_settings
```

#### Search API

```bash
# Search with query
GET /mcp-logs-*/_search
{
  "query": {
    "match": {
      "message": "error"
    }
  }
}

# Search with filters
GET /mcp-logs-*/_search
{
  "query": {
    "bool": {
      "filter": [
        { "term": { "log_level": "ERROR" } },
        { "range": { "timestamp": { "gte": "2023-12-01T00:00:00Z" } } }
      ]
    }
  }
}
```

### Kibana API

#### Dashboard Management

```bash
# Create dashboard
POST /api/saved_objects/dashboard
{
  "attributes": {
    "title": "Custom Dashboard",
    "panelsJSON": "[...]"
  }
}

# Get dashboard
GET /api/saved_objects/dashboard/custom-dashboard
```

#### Visualization Management

```bash
# Create visualization
POST /api/saved_objects/visualization
{
  "attributes": {
    "title": "Error Rate",
    "visState": "{...}",
    "uiStateJSON": "{}",
    "description": "Error rate over time"
  }
}
```

## Contributing

### Development Setup

1. Set up development environment:
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

2. Run tests:
```bash
# Run unit tests
pytest tests/unit/

# Run integration tests
pytest tests/integration/

# Run all tests
pytest
```

3. Lint code:
```bash
# Lint Python code
flake8 src/

# Lint configuration files
yamllint fluentd/conf/
```

### Submitting Changes

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

This project is licensed under the MIT License. See the LICENSE file for details.

## Support

For support and questions:

- **Documentation**: [docs.mcp.ai](https://docs.mcp.ai)
- **Issues**: [GitHub Issues](https://github.com/your-org/mcp-platform/issues)
- **Community**: [Slack Channel](https://mcp.ai/slack)
- **Email**: support@mcp.ai

## Changelog

### Version 1.0.0 (2023-12-01)

- Initial release of log aggregation pipeline
- Complete Fluentd configuration with advanced processing
- Elasticsearch integration with ILM policies
- Kibana dashboards and visualizations
- Prometheus metrics extraction and alerting
- Security and compliance features
- Comprehensive documentation