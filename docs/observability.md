# 📊 Complete Observability Stack - Grafana Triad

This documentation covers the comprehensive observability implementation for the MCP Agent Network, featuring the complete Grafana observability triad: **Prometheus** (metrics), **Loki** (logs), and **Tempo** (traces).

## 🔍 Overview

The observability stack provides enterprise-grade monitoring with:

- **📈 Metrics**: Prometheus + Grafana for performance monitoring
- **📝 Logs**: Loki + Promtail for centralized log aggregation  
- **🔗 Traces**: Tempo + OpenTelemetry for distributed tracing
- **📊 Unified View**: Grafana dashboards with correlated data

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Applications  │    │   Applications  │    │   Applications  │
│                 │    │                 │    │                 │
│ Structured JSON │    │ OpenTelemetry   │    │ Prometheus      │
│ Logs            │    │ Traces          │    │ Metrics         │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          ▼                      ▼                      ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│    Promtail     │    │     Tempo       │    │   Prometheus    │
│ Log Aggregation │    │ Trace Storage   │    │ Metrics Storage │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          ▼                      ▼                      ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│      Loki       │    │                 │    │                 │
│  Log Storage    │    │                 │    │                 │
└─────────┬───────┘    │                 │    │                 │
          │            │    Grafana      │    │                 │
          └────────────► Unified         ◄────┘                 │
                       │ Observability   │                      │
                       │ Dashboard       ◄──────────────────────┘
                       └─────────────────┘
```

## 🚀 Services Overview

### Core Observability Services

| Service | Port | Purpose | Configuration |
|---------|------|---------|---------------|
| **Grafana** | 3005 | Unified dashboards and visualization | `grafana_data:/var/lib/grafana` |
| **Prometheus** | 9090 | Metrics collection and storage | `prometheus_data:/prometheus` |
| **Loki** | 3100 | Log aggregation and storage | `loki_data:/loki` |
| **Tempo** | 3200 | Distributed tracing storage | `tempo_data:/tmp/tempo` |
| **Promtail** | 9080 | Log shipping to Loki | Log parsing and forwarding |

### Legacy Services (Optional)

| Service | Port | Purpose | Profile |
|---------|------|---------|---------|
| **Elasticsearch** | 9200 | Legacy log storage | `legacy-logging` |
| **Kibana** | 5601 | Legacy log visualization | `legacy-logging` |
| **Filebeat** | - | Legacy log shipping | `legacy-logging` |

## 📝 Configuration Files

### Loki Configuration
**File**: `monitoring/loki-config.yml`

Key features:
- **Retention**: 7 days (168h)
- **Storage**: Local filesystem with BoltDB shipper
- **Limits**: 4MB ingestion rate, 256KB max line size
- **Compaction**: 10-minute intervals with retention cleanup

### Tempo Configuration  
**File**: `monitoring/tempo-config.yml`

Key features:
- **Receivers**: OTLP (gRPC/HTTP), Jaeger, Zipkin, OpenCensus
- **Metrics Generation**: Service graphs and span metrics
- **Storage**: Local filesystem with WAL
- **Retention**: 1 hour for demo (configurable)

### Promtail Configuration
**File**: `monitoring/promtail-config.yml`

Log parsing for:
- **MCP Services**: JSON structured logs
- **Docker Containers**: Container log parsing
- **Nginx**: Access and error logs
- **PostgreSQL**: Database logs with timestamps
- **Redis**: Redis server logs

### Grafana Datasources
**File**: `monitoring/grafana/datasources/prometheus.yml`

Configured datasources:
- **Prometheus**: Default metrics source
- **Loki**: Log queries with 1000 line limit
- **Tempo**: Trace queries with logs/metrics correlation

## 🔧 Environment Configuration

### Observability Environment Variables

All microservices include these environment variables:

```yaml
# Structured Logging
- LOG_FORMAT=json              # Enable JSON logging for Loki
- LOG_LEVEL=INFO              # Set logging level

# Distributed Tracing  
- TRACING_ENABLED=true        # Enable OpenTelemetry tracing
- TEMPO_OTLP_ENDPOINT=http://tempo:4317  # Tempo OTLP receiver
```

### Service-Specific Configuration

Each microservice automatically includes:
- **Service Name**: Identifies the service in traces and logs
- **JSON Logging**: Structured logs with timestamps, levels, and metadata
- **Automatic Instrumentation**: FastAPI, HTTP clients, databases
- **Trace Correlation**: Links logs and traces via trace/span IDs

## 📊 Dashboard Access

### Primary Interfaces

| Interface | URL | Credentials | Purpose |
|-----------|-----|-------------|---------|
| **Grafana** | http://localhost:3005 | admin/admin123 | Unified observability |
| **Prometheus** | http://localhost:9090 | None | Raw metrics queries |
| **Loki** | http://localhost:3100 | None | Direct log queries |
| **Tempo** | http://localhost:3200 | None | Direct trace queries |

### Legacy Interfaces (Optional)

| Interface | URL | Profile | Purpose |
|-----------|-----|---------|---------|
| **Kibana** | http://localhost:5601 | `legacy-logging` | Legacy log analysis |
| **Elasticsearch** | http://localhost:9200 | `legacy-logging` | Legacy log storage |

## 🔍 Key Features

### 1. Structured JSON Logging

All microservices output structured JSON logs:

```json
{
  "timestamp": "2025-01-02T10:30:45Z",
  "level": "INFO",
  "service_name": "model-router",
  "logger": "model_router.app",
  "message": "Processing chat request",
  "request_id": "req_123456",
  "model": "claude-3-sonnet",
  "latency_ms": 1250,
  "tokens": 150
}
```

### 2. Distributed Tracing

OpenTelemetry integration provides:
- **Automatic Instrumentation**: FastAPI, HTTP clients, databases
- **Custom Spans**: Business logic tracing with `@trace_function`
- **Trace Correlation**: Links between services and operations
- **Error Tracking**: Exception capture and span attribution

### 3. Metrics-Logs-Traces Correlation

Grafana provides unified views:
- **Trace → Logs**: Click trace spans to see related logs
- **Logs → Traces**: Filter logs by trace ID
- **Metrics → Traces**: Drill down from high-level metrics
- **Service Maps**: Visual representation of service dependencies

## 🚀 Usage Examples

### Starting the Observability Stack

```bash
# Start all services including observability
docker-compose up -d

# Start only legacy logging (optional)
docker-compose --profile legacy-logging up -d elasticsearch kibana filebeat

# Check service health
docker-compose ps
```

### Querying Logs in Loki

```logql
# All logs from model-router service
{job="model-router"}

# Error logs across all services
{} |= "ERROR"

# Logs for specific request
{} | json | request_id="req_123456"

# High latency requests
{job="model-router"} | json | latency_ms > 1000
```

### Querying Traces in Tempo

Search traces by:
- **Service Name**: `service.name=model-router`
- **Operation**: `operation=POST /chat`
- **Duration**: `duration>1s`
- **Status**: `status=error`

### Prometheus Metrics

```promql
# Request rate by service
rate(http_requests_total[5m])

# 95th percentile latency
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Error rate
rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m])
```

## 🔧 Development Setup

### Adding Tracing to New Services

```python
from common.tracing import setup_tracing, instrument_fastapi, trace_function

# Initialize tracing
setup_tracing("my-service")

# Instrument FastAPI app
app = FastAPI()
instrument_fastapi(app)

# Trace custom functions
@trace_function(name="business_logic", attributes={"version": "1.0"})
async def process_request(data):
    # Your code here
    pass
```

### Adding Structured Logging

```python
from common.logging import get_service_logger

# Get logger with service context
logger = get_service_logger("my-service", request_id="req_123")

# Log with structured data
logger.info("Processing request", extra={
    "user_id": "user_456",
    "operation": "create_plan",
    "duration_ms": 150
})
```

## 📈 Monitoring Best Practices

### 1. Log Levels and Volume
- **DEBUG**: Development only
- **INFO**: Business events and request flows
- **WARN**: Recoverable errors and degraded performance
- **ERROR**: Failures requiring attention

### 2. Trace Sampling
- **Development**: 100% sampling for debugging
- **Production**: 10-20% sampling for performance
- **High-Traffic**: 1-5% sampling with error sampling

### 3. Metrics Cardinality
- Limit label combinations to avoid cardinality explosion
- Use histogram buckets appropriate for your latency distribution
- Monitor metrics storage usage and retention

### 4. Alert Configuration
- **SLI/SLO**: Define service level objectives
- **Error Budgets**: Track acceptable failure rates
- **Latency Percentiles**: Monitor P95/P99 latencies
- **Saturation**: Track resource utilization

## 🔧 Migration from Legacy Stack

To migrate from Elasticsearch/Kibana to Loki/Grafana:

```bash
# 1. Start new stack alongside legacy
docker-compose up -d loki tempo promtail grafana

# 2. Verify new stack is receiving data
curl http://localhost:3100/ready
curl http://localhost:3200/ready

# 3. Import existing dashboards to Grafana
# 4. Stop legacy services
docker-compose stop elasticsearch kibana filebeat

# 5. Remove legacy profile requirement
# Edit docker-compose.yml to remove 'profiles: legacy-logging'
```

## 🎯 Enterprise Readiness

The observability stack provides:

✅ **Production Ready**: Persistent storage, health checks, resource limits  
✅ **Scalable**: Horizontal scaling for high-throughput environments  
✅ **Secure**: No authentication required for internal network access  
✅ **Compliant**: Audit logs, retention policies, data governance  
✅ **Cost Effective**: Optimized storage and retention policies  

## 📚 Additional Resources

- [Grafana Documentation](https://grafana.com/docs/)
- [Prometheus Operator](https://prometheus-operator.dev/)
- [Loki LogQL Guide](https://grafana.com/docs/loki/latest/logql/)
- [Tempo Tracing Guide](https://grafana.com/docs/tempo/latest/)
- [OpenTelemetry Python](https://opentelemetry.io/docs/instrumentation/python/)

---

This complete observability implementation provides enterprise-grade monitoring with unified metrics, logs, and traces accessible through Grafana dashboards, ready for investor demonstrations and production deployments.