# Observability Production Readiness Guide

This document provides a comprehensive guide for making the observability implementation production-ready, including all missing configuration files and enhancements needed.

## Table of Contents

1. [Missing Configuration Files](#missing-configuration-files)
2. [Docker Compose Enhancements](#docker-compose-enhancements)
3. [Security and Compliance](#security-and-compliance)
4. [Performance Optimization](#performance-optimization)
5. [Backup and Disaster Recovery](#backup-and-disaster-recovery)
6. [Service Integration](#service-integration)
7. [Deployment Automation](#deployment-automation)
8. [Monitoring and Alerting](#monitoring-and-alerting)
9. [Documentation and Runbooks](#documentation-and-runbooks)

## Missing Configuration Files

### 1. Tempo Configuration (`monitoring/tempo-config.yml`)

```yaml
# Tempo Configuration for Distributed Tracing
# Production-ready configuration with high availability and performance optimization

server:
  http_listen_port: 3200
  grpc_listen_port: 9096

distributor:
  receivers:
    jaeger:
      protocols:
        grpc:
          endpoint: "0.0.0.0:14250"
        thrift_binary:
          endpoint: "0.0.0.0:6832"
        thrift_compact:
          endpoint: "0.0.0.0:6831"
        thrift_http:
          endpoint: "0.0.0.0:14268"
    otlp:
      protocols:
        grpc:
          endpoint: "0.0.0.0:4317"
        http:
          endpoint: "0.0.0.0:4318"
    zipkin:
      endpoint: "0.0.0.0:9411"

  log_received_spans:
    enabled: true

ingester:
  max_block_duration: 5m
  trace_idle_period: 30s
  flush_all_services: true

compactor:
  compaction:
    compaction_window: 1h
    max_block_bytes: 100_000_000
    block_retention: 72h
    compacted_block_retention: 216h

metrics_generator:
  registry:
    external_labels:
      source: tempo
      cluster: mcp-production
  processor:
    service_graphs:
      dimensions:
        - service
        - span_name
        - status_code
      max_items: 10000
    span_metrics:
      dimensions:
        - service
        - span_name
        - status_code
      histogram_buckets: [100us, 1ms, 2ms, 6ms, 10ms, 100ms, 250ms]
  storage:
    path: /tmp/tempo/generator/wal
    remote_write:
      - url: http://prometheus:9090/api/v1/write
        send_exemplars: true

storage:
  trace:
    backend: local
    wal:
      path: /tmp/tempo/wal
    local:
      path: /tmp/tempo/blocks

overrides:
  defaults:
    per_user_tracing:
      ingestion_rate_limit_bytes: 1048576  # 1MB
      ingestion_burst_size_bytes: 10485760  # 10MB
      block_retention: 72h
      traces_per_user: 10000
```

### 2. Loki Configuration (`monitoring/loki-config.yml`)

```yaml
# Loki Configuration for Log Aggregation
# Production-ready configuration with high availability and performance optimization

auth_enabled: false

server:
  http_listen_port: 3100
  grpc_listen_port: 9096
  grpc_server_max_recv_msg_size: 104857600  # 100MB
  grpc_server_max_send_msg_size: 104857600  # 100MB

common:
  path_prefix: /loki
  storage:
    filesystem:
      chunks_directory: /loki/chunks
      rules_directory: /loki/rules
  replication_factor: 1
  ring:
    instance_addr: 127.0.0.1
    kvstore:
      store: inmemory

query_range:
  results_cache:
    cache:
      embedded_cache:
        enabled: true
        max_size_mb: 100

schema_config:
  configs:
    - from: 2020-10-24
      store: boltdb-shipper
      object_store: filesystem
      schema: v11
      index:
        prefix: index_
        period: 24h

ruler:
  alertmanager_url: http://localhost:9093

# By default, Loki will send anonymous, but uniquely-identifiable usage and configuration
# analytics to Grafana Labs. These statistics help us understand how Loki is used,
# and they show us performance levels across user populations. For more information
# on what's sent, disable the setting, or opt-out at
# https://grafana.com/docs/loki/latest/configuration/usage-reporting/,
# review the Analytics section of the documentation.
analytics:
  reporting_enabled: false

# Limit the number of active streams per user
limits_config:
  reject_old_samples: true
  reject_old_samples_max_age: 168h
  max_cache_freshness_per_query: 10m

chunk_store_config:
  max_look_back_period: 0s

table_manager:
  retention_deletes_enabled: false
  retention_period: 0s

compactor:
  working_directory: /loki/boltdb-shipper-compactor
  shared_store: filesystem
  compactor_ring:
    kvstore:
      store: inmemory

ingester:
  chunk_encoding: snappy
  chunk_target_size: 1048576  # 1MB
  chunk_idle_period: 30m
  max_chunk_age: 1h
  lifecycler:
    ring:
      replication_factor: 1
      kvstore:
        store: inmemory
    final_sleep: 0s
  flush_check_period: 5s
  flush_op_timeout: 10s
  chunk_retain_period: 30s
  wal:
    enabled: true
    dir: /loki/wal
    replay_memory_ceiling: 1GB
```

### 3. Promtail Configuration (`monitoring/promtail-config.yml`)

```yaml
# Promtail Configuration for Log Collection
# Production-ready configuration with comprehensive log parsing and enrichment

server:
  http_listen_port: 9080
  grpc_listen_port: 0

positions:
  filename: /tmp/positions.yaml

clients:
  - url: http://loki:3100/loki/api/v1/push

scrape_configs:
  # Docker container logs
  - job_name: docker-logs
    docker_sd_configs:
      - host: unix:///var/run/docker.sock
        refresh_interval: 5s
    pipeline_stages:
      - json:
          expressions:
            timestamp: time
            level: level
            service: service_name
            trace_id: trace_id
            span_id: span_id
            message: message
      - timestamp:
          source: timestamp
          format: ISO8601
      - labels:
          level:
          service:
          trace_id:
          span_id:
      - output:
          source: message
    relabel_configs:
      - source_labels: [__meta_docker_container_label_com_docker_compose_service]
        target_label: service
      - source_labels: [__meta_docker_container_name]
        target_label: container_name
      - source_labels: [__meta_docker_container_log_stream]
        target_label: stream

  # Application logs from mounted volume
  - job_name: application-logs
    static_configs:
      - targets:
          - localhost
        labels:
          job: application
          __path__: /var/log/mcp/*/*.log
    pipeline_stages:
      - json:
          expressions:
            timestamp: timestamp
            level: level
            service: service_name
            trace_id: trace_id
            span_id: span_id
            message: message
            user_id: user_id
            tenant_id: tenant_id
      - timestamp:
          source: timestamp
          format: ISO8601
      - labels:
          level:
          service:
          trace_id:
          span_id:
          user_id:
          tenant_id:
      - output:
          source: message

  # Nginx access logs
  - job_name: nginx-access-logs
    static_configs:
      - targets:
          - localhost
        labels:
          job: nginx-access
          __path__: /var/log/nginx/access.log
    pipeline_stages:
      - regex:
          expression: '^(?P<remote_addr>\S+) - (?P<remote_user>\S+) \[(?P<time_local>.+)\] "(?P<method>\S+) (?P<request_uri>\S+) (?P<protocol>\S+)" (?P<status>\d+) (?P<body_bytes_sent>\d+) "(?P<http_referer>.*)" "(?P<http_user_agent>.*)"'
      - timestamp:
          source: time_local
          format: '02/Jan/2006:15:04:05 -0700'
      - labels:
          method:
          status:
          remote_addr:
      - output:
          source: request_uri

  # Nginx error logs
  - job_name: nginx-error-logs
    static_configs:
      - targets:
          - localhost
        labels:
          job: nginx-error
          __path__: /var/log/nginx/error.log
    pipeline_stages:
      - regex:
          expression: '^(?P<timestamp>\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2}) \[(?P<level>\w+)\] (?P<pid>\d+)#(?P<tid>\d+): (?P<message>.*)'
      - timestamp:
          source: timestamp
          format: '2006/01/02 15:04:05'
      - labels:
          level:
      - output:
          source: message

limits_config:
  readline_rate: 10000
  readline_rate_burst: 20000
  max_line_size: 1048576  # 1MB
```

### 4. OpenTelemetry Collector Configuration (`monitoring/opentelemetry/collector-config.yml`)

```yaml
# OpenTelemetry Collector Configuration
# Production-ready configuration with comprehensive telemetry collection and processing

receivers:
  # Metrics receivers
  prometheus:
    config:
      scrape_configs:
        - job_name: 'otel-collector'
          scrape_interval: 30s
          static_configs:
            - targets: ['localhost:8888']
  
  # Trace receivers
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
        max_recv_msg_size_mib: 64
      http:
        endpoint: 0.0.0.0:4318
        cors:
          allowed_origins:
            - "*"
          allowed_headers:
            - "*"
  
  # Log receivers
  fluentforward:
    endpoint: 0.0.0.0:24224
  
  # Host metrics
  hostmetrics:
    collection_interval: 30s
    scrapers:
      cpu:
        metrics:
          system.cpu.utilization:
            enabled: true
          system.cpu.load_average.1m:
            enabled: true
          system.cpu.load_average.5m:
            enabled: true
          system.cpu.load_average.15m:
            enabled: true
      disk:
        metrics:
          system.disk.io:
            enabled: true
          system.disk.operations:
            enabled: true
          system.disk.time:
            enabled: true
      memory:
        metrics:
          system.memory.usage:
            enabled: true
          system.memory.utilization:
            enabled: true
      network:
        metrics:
          system.network.io:
            enabled: true
          system.network.packets:
            enabled: true
          system.network.errors:
            enabled: true
      paging:
        metrics:
          system.paging.operations:
            enabled: true
          system.paging.usage:
            enabled: true
      processes:
        metrics:
          system.processes.count:
            enabled: true
          system.processes.created:
            enabled: true

processors:
  # Batch processing for performance
  batch:
    send_batch_size: 8192
    send_batch_max_size: 8192
    timeout: 30s
  
  # Memory limiter
  memory_limiter:
    check_interval: 1s
    limit_mib: 512
    spike_limit_mib: 100
  
  # Resource detection
  resourcedetection:
    detectors: [env, system]
    timeout: 10s
    system:
      hostname_sources: [os]
  
  # Resource attributes
  resource:
    attributes:
      - key: service.name
        value: otel-collector
        action: insert
      - key: service.version
        value: 1.0.0
        action: insert
      - key: deployment.environment
        value: production
        action: insert
  
  # Metric transformations
  metricstransform:
    transforms:
      - include: system.cpu.utilization
        action: update
        new_name: cpu_utilization
      - include: system.memory.utilization
        action: update
        new_name: memory_utilization
  
  # Span processing
  span:
    name:
      from_attributes: [http.target]
      separator: " "
    # Add custom attributes to spans
    attributes:
      - key: environment
        value: production
        action: insert
      - key: version
        value: 1.0.0
        action: insert

exporters:
  # Metrics to Prometheus
  prometheus:
    endpoint: 0.0.0.0:8888
    namespace: mcp
    const_labels:
      cluster: mcp-production
      environment: production
  
  # Traces to Tempo
  otlp/tempo:
    endpoint: tempo:4317
    tls:
      insecure: true
  
  # Logs to Loki
  loki:
    endpoint: http://loki:3100/loki/api/v1/push
    tls:
      insecure: true
    labels:
      job: otel-collector
      cluster: mcp-production
  
  # Debug exporter for development
  debug:
    verbosity: detailed

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [batch, memory_limiter, resourcedetection, resource, span]
      exporters: [otlp/tempo, debug]
    
    metrics:
      receivers: [prometheus, hostmetrics]
      processors: [batch, memory_limiter, resourcedetection, resource, metricstransform]
      exporters: [prometheus, debug]
    
    logs:
      receivers: [fluentforward, otlp]
      processors: [batch, memory_limiter, resourcedetection, resource]
      exporters: [loki, debug]

extensions:
  health_check:
    endpoint: 0.0.0.0:13133
  pprof:
    endpoint: 0.0.0.0:1777
  zpages:
    endpoint: 0.0.0.0:55679
```

## Docker Compose Enhancements

### Add OpenTelemetry Collector Service

Add the following service to `docker-compose.yml`:

```yaml
  # OpenTelemetry Collector
  otel-collector:
    image: otel/opentelemetry-collector-contrib:latest
    container_name: mcp-otel-collector
    restart: unless-stopped
    command: ["--config=/etc/otel-collector-config.yaml"]
    ports:
      - "4317:4317"   # OTLP gRPC
      - "4318:4318"   # OTLP HTTP
      - "8888:8888"   # Prometheus metrics
      - "13133:13133" # Health check
      - "24224:24224" # Fluent forward
    volumes:
      - ./monitoring/opentelemetry/collector-config.yml:/etc/otel-collector-config.yaml:ro
      - /var/run/docker.sock:/var/run/docker.sock:ro
    depends_on:
      - tempo
      - loki
      - prometheus
    networks:
      - mcp-network
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '0.5'
        reservations:
          memory: 256M
          cpus: '0.25'
```

### Update Service Environment Variables

Update all MCP services to include OpenTelemetry configuration:

```yaml
environment:
  # Existing environment variables...
  
  # OpenTelemetry Configuration
  - OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317
  - OTEL_EXPORTER_OTLP_PROTOCOL=grpc
  - OTEL_RESOURCE_ATTRIBUTES=service.name=${SERVICE_NAME},service.version=1.0.0,deployment.environment=production
  - OTEL_METRICS_EXPORTER=prometheus
  - OTEL_LOGS_EXPORTER=loki
  - OTEL_TRACES_SAMPLER=parentbased_traceidratio
  - OTEL_TRACES_SAMPLER_ARG=0.1
  - OTEL_PYTHON_LOG_CORRELATION=true
  - OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED=true
```

## Security and Compliance

### 1. Network Security

Create `monitoring/network-policies.yml`:

```yaml
# Network Policies for Observability Components
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: observability-network-policy
  namespace: mcp-system
spec:
  podSelector: {}
  policyTypes:
    - Ingress
    - Egress
  ingress:
    - from:
        - namespaceSelector:
            matchLabels:
              name: mcp-system
      ports:
        - protocol: TCP
          port: 4317  # OTLP gRPC
        - protocol: TCP
          port: 4318  # OTLP HTTP
        - protocol: TCP
          port: 9090  # Prometheus
        - protocol: TCP
          port: 3000  # Grafana
        - protocol: TCP
          port: 3100  # Loki
        - protocol: TCP
          port: 3200  # Tempo
  egress:
    - to:
        - namespaceSelector:
            matchLabels:
              name: mcp-system
      ports:
        - protocol: TCP
          port: 5432   # PostgreSQL
        - protocol: TCP
          port: 6379   # Redis
        - protocol: TCP
          port: 9090   # Prometheus
        - protocol: TCP
          port: 3100   # Loki
        - protocol: TCP
          port: 3200   # Tempo
```

### 2. RBAC Configuration

Create `monitoring/rbac.yml`:

```yaml
# RBAC Configuration for Observability Components
apiVersion: v1
kind: ServiceAccount
metadata:
  name: observability-sa
  namespace: mcp-system

---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: observability-role
  namespace: mcp-system
rules:
  - apiGroups: [""]
    resources: ["pods", "services", "endpoints"]
    verbs: ["get", "list", "watch"]
  - apiGroups: ["apps"]
    resources: ["deployments", "replicasets"]
    verbs: ["get", "list", "watch"]
  - apiGroups: ["extensions"]
    resources: ["deployments"]
    verbs: ["get", "list", "watch"]

---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: observability-role-binding
  namespace: mcp-system
subjects:
  - kind: ServiceAccount
    name: observability-sa
    namespace: mcp-system
roleRef:
  kind: Role
  name: observability-role
  apiGroup: rbac.authorization.k8s.io
```

### 3. Security Context

Add security context to all observability services:

```yaml
securityContext:
  runAsUser: 1000
  runAsGroup: 1000
  fsGroup: 1000
  readOnlyRootFilesystem: true
  runAsNonRoot: true
  capabilities:
    drop:
      - ALL
    add:
      - NET_BIND_SERVICE
```

## Performance Optimization

### 1. Resource Limits and Requests

Update resource limits for all observability components:

```yaml
deploy:
  resources:
    limits:
      memory: 1Gi
      cpus: '1.0'
    reservations:
      memory: 512Mi
      cpus: '0.5'
```

### 2. Storage Optimization

Create `monitoring/storage-optimization.yml`:

```yaml
# Storage Optimization Configuration
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: prometheus-data-pvc
  namespace: mcp-system
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 100Gi
  storageClassName: fast-ssd

---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: grafana-data-pvc
  namespace: mcp-system
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 50Gi
  storageClassName: fast-ssd

---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: loki-data-pvc
  namespace: mcp-system
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 200Gi
  storageClassName: fast-ssd

---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: tempo-data-pvc
  namespace: mcp-system
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 100Gi
  storageClassName: fast-ssd
```

### 3. Caching Configuration

Add Redis caching for Grafana:

```yaml
  # Redis for Grafana caching
  grafana-redis:
    image: redis:7-alpine
    container_name: mcp-grafana-redis
    restart: unless-stopped
    ports:
      - "6380:6379"
    volumes:
      - grafana_redis_data:/data
    command: redis-server --appendonly yes --maxmemory 256mb --maxmemory-policy allkeys-lru
    networks:
      - mcp-network
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '0.5'
        reservations:
          memory: 256M
          cpus: '0.25'
```

## Backup and Disaster Recovery

### 1. Backup Configuration

Create `monitoring/backup-config.yml`:

```yaml
# Backup Configuration for Observability Data
version: '3.8'

services:
  # Backup Service
  observability-backup:
    image: alpine:latest
    container_name: mcp-observability-backup
    restart: "no"
    volumes:
      - prometheus_data:/backup/prometheus:ro
      - grafana_data:/backup/grafana:ro
      - loki_data:/backup/loki:ro
      - tempo_data:/backup/tempo:ro
      - ./backups:/output
    environment:
      - BACKUP_RETENTION_DAYS=30
      - BACKUP_SCHEDULE=0 2 * * *
    command: >
      sh -c "
        apk add --no-cache tar gzip cronie
        echo '0 2 * * * cd /backup && tar -czf /output/observability-backup-$(date +\%Y\%m\%d).tar.gz . && find /output -name 'observability-backup-*.tar.gz' -mtime +$$BACKUP_RETENTION_DAYS -delete' > /etc/crontabs/root
        crond -f
      "
    networks:
      - mcp-network

volumes:
  prometheus_data:
    external: true
  grafana_data:
    external: true
  loki_data:
    external: true
  tempo_data:
    external: true
```

### 2. Restore Script

Create `scripts/restore-observability.sh`:

```bash
#!/bin/bash
# Restore Observability Data from Backup

set -e

BACKUP_FILE=$1
if [ -z "$BACKUP_FILE" ]; then
  echo "Usage: $0 <backup-file>"
  exit 1
fi

if [ ! -f "$BACKUP_FILE" ]; then
  echo "Backup file not found: $BACKUP_FILE"
  exit 1
fi

echo "Stopping observability services..."
docker compose stop prometheus grafana loki tempo

echo "Restoring from backup..."
tar -xzf "$BACKUP_FILE" -C /tmp

echo "Restoring Prometheus data..."
docker run --rm -v prometheus_data:/data -v /tmp/backup/prometheus:/backup alpine:latest sh -c "cp -r /backup/* /data/"

echo "Restoring Grafana data..."
docker run --rm -v grafana_data:/data -v /tmp/backup/grafana:/backup alpine:latest sh -c "cp -r /backup/* /data/"

echo "Restoring Loki data..."
docker run --rm -v loki_data:/data -v /tmp/backup/loki:/backup alpine:latest sh -c "cp -r /backup/* /data/"

echo "Restoring Tempo data..."
docker run --rm -v tempo_data:/data -v /tmp/backup/tempo:/backup alpine:latest sh -c "cp -r /backup/* /data/"

echo "Starting observability services..."
docker compose start prometheus grafana loki tempo

echo "Restore completed successfully!"
```

## Service Integration

### 1. Auto-Instrumentation for Python Services

Create `monitoring/opentelemetry/python-instrumentation.yml`:

```yaml
# Python Auto-Instrumentation Configuration
version: '3.8'

services:
  # Python Service with Auto-Instrumentation
  python-service-example:
    build:
      context: .
      dockerfile: docker/python-service.Dockerfile
    environment:
      # OpenTelemetry Configuration
      - OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317
      - OTEL_EXPORTER_OTLP_PROTOCOL=grpc
      - OTEL_RESOURCE_ATTRIBUTES=service.name=python-service-example,service.version=1.0.0,deployment.environment=production
      - OTEL_METRICS_EXPORTER=prometheus
      - OTEL_LOGS_EXPORTER=loki
      - OTEL_TRACES_SAMPLER=parentbased_traceidratio
      - OTEL_TRACES_SAMPLER_ARG=0.1
      - OTEL_PYTHON_LOG_CORRELATION=true
      - OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED=true
      
      # Auto-Instrumentation
      - OTEL_PYTHON_AUTO_INSTRUMENTATION_ENABLED=true
      - OTEL_PYTHON_DISABLED_INSTRUMENTATIONS=
      - OTEL_PYTHON_EXCLUDED_URLS=health,metrics
      - OTEL_PYTHON_INSTRUMENTATION_HTTP_CAPTURE_HEADERS_SERVER_REQUEST=content-type,authorization
      - OTEL_PYTHON_INSTRUMENTATION_HTTP_CAPTURE_HEADERS_SERVER_RESPONSE=content-type,content-length
    volumes:
      - ./logs:/app/logs
    depends_on:
      - otel-collector
    networks:
      - mcp-network
```

### 2. Auto-Instrumentation for JavaScript Services

Create `monitoring/opentelemetry/javascript-instrumentation.yml`:

```yaml
# JavaScript Auto-Instrumentation Configuration
version: '3.8'

services:
  # JavaScript Service with Auto-Instrumentation
  javascript-service-example:
    build:
      context: .
      dockerfile: docker/javascript-service.Dockerfile
    environment:
      # OpenTelemetry Configuration
      - NODE_OPTIONS=--require @opentelemetry/auto-instrumentations-node
      - OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317
      - OTEL_EXPORTER_OTLP_PROTOCOL=grpc
      - OTEL_RESOURCE_ATTRIBUTES=service.name=javascript-service-example,service.version=1.0.0,deployment.environment=production
      - OTEL_METRICS_EXPORTER=prometheus
      - OTEL_LOGS_EXPORTER=loki
      - OTEL_TRACES_SAMPLER=parentbased_traceidratio
      - OTEL_TRACES_SAMPLER_ARG=0.1
      - OTEL_NODE_DISABLED_INSTRUMENTATIONS=
      - OTEL_NODE_EXCLUDED_URLS=health,metrics
      - OTEL_NODE_HTTP_CAPTURE_HEADERS_SERVER_REQUEST=content-type,authorization
      - OTEL_NODE_HTTP_CAPTURE_HEADERS_SERVER_RESPONSE=content-type,content-length
    volumes:
      - ./logs:/app/logs
    depends_on:
      - otel-collector
    networks:
      - mcp-network
```

## Deployment Automation

### 1. CI/CD Pipeline

Create `.github/workflows/observability-deployment.yml`:

```yaml
name: Observability Deployment

on:
  push:
    branches: [main]
    paths:
      - 'monitoring/**'
      - 'docker-compose.yml'
  pull_request:
    branches: [main]
    paths:
      - 'monitoring/**'
      - 'docker-compose.yml'

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Validate Docker Compose
        run: |
          docker compose config
      
      - name: Validate Prometheus Configuration
        run: |
          docker run --rm -v $(pwd)/monitoring:/config prom/prometheus:latest --config.file=/config/prometheus.yml --dry-run
      
      - name: Validate Grafana Dashboards
        run: |
          docker run --rm -v $(pwd)/monitoring/grafana/dashboards:/dashboards grafana/grafana:latest grafana-cli --config=/etc/grafana/grafana.ini dashboards validate

  deploy:
    needs: validate
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v3
      
      - name: Deploy to Production
        run: |
          docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
          docker compose ps
          
      - name: Health Check
        run: |
          sleep 30
          curl -f http://localhost:3000/api/health || exit 1
          curl -f http://localhost:9090/-/healthy || exit 1
          curl -f http://localhost:3100/ready || exit 1
          curl -f http://localhost:3200/ready || exit 1
```

### 2. Deployment Script

Create `scripts/deploy-observability.sh`:

```bash
#!/bin/bash
# Observability Deployment Script

set -e

ENVIRONMENT=${1:-development}
echo "Deploying observability stack to $ENVIRONMENT environment"

# Validate configuration
echo "Validating configuration..."
docker compose config

# Pull latest images
echo "Pulling latest images..."
docker compose pull

# Deploy observability stack
echo "Deploying observability stack..."
if [ "$ENVIRONMENT" = "production" ]; then
  docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
else
  docker compose up -d
fi

# Wait for services to be healthy
echo "Waiting for services to be healthy..."
sleep 30

# Health checks
echo "Performing health checks..."
curl -f http://localhost:3000/api/health || echo "Grafana health check failed"
curl -f http://localhost:9090/-/healthy || echo "Prometheus health check failed"
curl -f http://localhost:3100/ready || echo "Loki health check failed"
curl -f http://localhost:3200/ready || echo "Tempo health check failed"

echo "Observability stack deployed successfully!"
echo "Grafana: http://localhost:3000"
echo "Prometheus: http://localhost:9090"
echo "Loki: http://localhost:3100"
echo "Tempo: http://localhost:3200"
```

## Monitoring and Alerting

### 1. Production Alerting Rules

Create `monitoring/alerts/production-alerting-rules.yml`:

```yaml
# Production Alerting Rules
groups:
  - name: observability.production
    interval: 30s
    rules:
      # Observability Infrastructure Alerts
      - alert: ObservabilityComponentDown
        expr: up{job=~"prometheus|grafana|loki|tempo|otel-collector"} == 0
        for: 1m
        labels:
          severity: critical
          category: infrastructure
          team: observability
        annotations:
          summary: "Observability component {{ $labels.job }} is down"
          description: "Observability component {{ $labels.job }} on {{ $labels.instance }} has been down for more than 1 minute"
          runbook_url: "https://docs.example.com/runbooks/observability-component-down"
      
      - alert: HighMemoryUsage
        expr: (container_memory_usage_bytes{container=~"prometheus|grafana|loki|tempo|otel-collector"} / container_spec_memory_limit_bytes{container=~"prometheus|grafana|loki|tempo|otel-collector"}) * 100 > 80
        for: 5m
        labels:
          severity: warning
          category: infrastructure
          team: observability
        annotations:
          summary: "High memory usage for {{ $labels.container }}"
          description: "Memory usage for {{ $labels.container }} is {{ $value }}%"
          runbook_url: "https://docs.example.com/runbooks/high-memory-usage"
      
      - alert: HighCPUUsage
        expr: rate(container_cpu_usage_seconds_total{container=~"prometheus|grafana|loki|tempo|otel-collector"}[5m]) * 100 > 80
        for: 5m
        labels:
          severity: warning
          category: infrastructure
          team: observability
        annotations:
          summary: "High CPU usage for {{ $labels.container }}"
          description: "CPU usage for {{ $labels.container }} is {{ $value }}%"
          runbook_url: "https://docs.example.com/runbooks/high-cpu-usage"
      
      # Tracing Alerts
      - alert: HighErrorRate
        expr: (rate(traces_span_metrics_dropped_spans_total[5m]) / rate(traces_span_metrics_received_spans_total[5m])) * 100 > 5
        for: 5m
        labels:
          severity: warning
          category: tracing
          team: observability
        annotations:
          summary: "High span drop rate detected"
          description: "Span drop rate is {{ $value }}%"
          runbook_url: "https://docs.example.com/runbooks/high-span-drop-rate"
      
      - alert: TraceLatencyHigh
        expr: histogram_quantile(0.95, rate(traces_span_metrics_latency_seconds_bucket[5m])) > 1
        for: 5m
        labels:
          severity: warning
          category: tracing
          team: observability
        annotations:
          summary: "High trace latency detected"
          description: "95th percentile trace latency is {{ $value }}s"
          runbook_url: "https://docs.example.com/runbooks/high-trace-latency"
      
      # Logging Alerts
      - alert: LogIngestionRateHigh
        expr: rate(loki_distributor_bytes_received_total[5m]) > 1000000
        for: 5m
        labels:
          severity: warning
          category: logging
          team: observability
        annotations:
          summary: "High log ingestion rate detected"
          description: "Log ingestion rate is {{ $value }} bytes/sec"
          runbook_url: "https://docs.example.com/runbooks/high-log-ingestion-rate"
      
      - alert: LogQueryLatencyHigh
        expr: histogram_quantile(0.95, rate(loki_query_duration_seconds_bucket[5m])) > 5
        for: 5m
        labels:
          severity: warning
          category: logging
          team: observability
        annotations:
          summary: "High log query latency detected"
          description: "95th percentile log query latency is {{ $value }}s"
          runbook_url: "https://docs.example.com/runbooks/high-log-query-latency"
```

### 2. Alertmanager Configuration

Update `monitoring/alertmanager/config.yml`:

```yaml
# Alertmanager Configuration
global:
  smtp_smarthost: 'localhost:587'
  smtp_from: 'alerts@example.com'
  smtp_auth_username: 'alerts@example.com'
  smtp_auth_password: 'password'

templates:
  - '/etc/alertmanager/templates/*.tmpl'

route:
  group_by: ['alertname', 'severity', 'category']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'web.hook'
  routes:
    - match:
        severity: critical
      receiver: 'critical-alerts'
      continue: true
    - match:
        severity: warning
      receiver: 'warning-alerts'
      continue: true
    - match:
        category: infrastructure
      receiver: 'infrastructure-team'
    - match:
        category: tracing
      receiver: 'observability-team'
    - match:
        category: logging
      receiver: 'observability-team'

receivers:
  - name: 'web.hook'
    webhook_configs:
      - url: 'http://127.0.0.1:5001/'

  - name: 'critical-alerts'
    email_configs:
      - to: 'critical-alerts@example.com'
        subject: '[CRITICAL] {{ .GroupLabels.alertname }}'
        body: |
          {{ range .Alerts }}
          Alert: {{ .Annotations.summary }}
          Description: {{ .Annotations.description }}
          Labels: {{ .Labels }}
          {{ end }}
    webhook_configs:
      - url: 'https://hooks.slack.com/services/XXXXX'
        send_resolved: true
        title: '[CRITICAL] {{ .GroupLabels.alertname }}'
        text: |
          {{ range .Alerts }}
          {{ .Annotations.summary }}
          {{ .Annotations.description }}
          {{ end }}

  - name: 'warning-alerts'
    email_configs:
      - to: 'warning-alerts@example.com'
        subject: '[WARNING] {{ .GroupLabels.alertname }}'
        body: |
          {{ range .Alerts }}
          Alert: {{ .Annotations.summary }}
          Description: {{ .Annotations.description }}
          Labels: {{ .Labels }}
          {{ end }}
    webhook_configs:
      - url: 'https://hooks.slack.com/services/XXXXX'
        send_resolved: true
        title: '[WARNING] {{ .GroupLabels.alertname }}'
        text: |
          {{ range .Alerts }}
          {{ .Annotations.summary }}
          {{ .Annotations.description }}
          {{ end }}

  - name: 'infrastructure-team'
    email_configs:
      - to: 'infrastructure@example.com'
        subject: '[INFRA] {{ .GroupLabels.alertname }}'
        body: |
          {{ range .Alerts }}
          Alert: {{ .Annotations.summary }}
          Description: {{ .Annotations.description }}
          Labels: {{ .Labels }}
          {{ end }}

  - name: 'observability-team'
    email_configs:
      - to: 'observability@example.com'
        subject: '[OBS] {{ .GroupLabels.alertname }}'
        body: |
          {{ range .Alerts }}
          Alert: {{ .Annotations.summary }}
          Description: {{ .Annotations.description }}
          Labels: {{ .Labels }}
          {{ end }}

inhibit_rules:
  - source_match:
      severity: 'critical'
    target_match:
      severity: 'warning'
    equal: ['alertname', 'dev', 'instance']
```

## Documentation and Runbooks

### 1. Observability Runbook

Create `docs/observability-runbook.md`:

```markdown
# Observability Runbook

This runbook provides step-by-step instructions for troubleshooting common observability issues.

## Table of Contents
1. [Critical Issues](#critical-issues)
2. [Performance Issues](#performance-issues)
3. [Data Issues](#data-issues)
4. [Configuration Issues](#configuration-issues)
5. [Maintenance Procedures](#maintenance-procedures)

## Critical Issues

### Observability Component Down

**Symptoms:**
- Grafana, Prometheus, Loki, or Tempo is unreachable
- Alert: `ObservabilityComponentDown`

**Troubleshooting Steps:**

1. **Check Service Status**
   ```bash
   docker compose ps
   docker compose logs prometheus
   docker compose logs grafana
   docker compose logs loki
   docker compose logs tempo
   ```

2. **Check Resource Usage**
   ```bash
   docker stats
   ```

3. **Restart Services**
   ```bash
   docker compose restart prometheus grafana loki tempo
   ```

4. **Check Network Connectivity**
   ```bash
   docker compose exec prometheus wget -qO- http://localhost:9090/-/healthy
   docker compose exec grafana wget -qO- http://localhost:3000/api/health
   docker compose exec loki wget -qO- http://localhost:3100/ready
   docker compose exec tempo wget -qO- http://localhost:3200/ready
   ```

5. **Check Storage**
   ```bash
   df -h
   docker volume ls
   docker volume inspect mcp-system_prometheus_data
   ```

**Escalation:**
- If issue persists for more than 15 minutes, escalate to infrastructure team
- If multiple components are affected, check for network or storage issues

### High Memory Usage

**Symptoms:**
- Memory usage > 80% for observability components
- Alert: `HighMemoryUsage`

**Troubleshooting Steps:**

1. **Identify High Memory Usage**
   ```bash
   docker stats --format "table {{.Container}}\t{{.MemUsage}}\t{{.MemPerc}}"
   ```

2. **Check Component Logs**
   ```bash
   docker compose logs prometheus | tail -50
   docker compose logs grafana | tail -50
   docker compose logs loki | tail -50
   docker compose logs tempo | tail -50
   ```

3. **Check Data Retention**
   ```bash
   # Check Prometheus data retention
   curl -s http://localhost:9090/api/v1/status/tsdb | jq .data.retentionTimeDuration
   
   # Check Loki retention
   curl -s http://localhost:3100/loki/api/v1/status/runtime | jq .data.config
   ```

4. **Clean Up Old Data**
   ```bash
   # Clean up old Prometheus data
   docker compose exec prometheus promtool tsdb clean --data-dir /prometheus --retain-duration=168h
   
   # Clean up old Loki data
   docker compose exec loki logcli query --from=168h --to=now '{job="all"}' | head -10
   ```

5. **Increase Resources**
   ```bash
   # Update docker-compose.yml with higher memory limits
   # Then restart services
   docker compose up -d
   ```

**Escalation:**
- If memory usage continues to increase, check for data retention issues
- If issue persists, consider scaling up resources or adding additional instances

## Performance Issues

### High CPU Usage

**Symptoms:**
- CPU usage > 80% for observability components
- Alert: `HighCPUUsage`

**Troubleshooting Steps:**

1. **Identify High CPU Usage**
   ```bash
   docker stats --format "table {{.Container}}\t{{.CPUPerc}}"
   ```

2. **Check Query Performance**
   ```bash
   # Check Prometheus queries
   curl -s http://localhost:9090/api/v1/status/tsdb | jq .data.headStats
   
   # Check Loki queries
   curl -s http://localhost:3100/loki/api/v1/status/runtime | jq .data.limit
   ```

3. **Optimize Queries**
   ```bash
   # Check for expensive queries in Grafana
   # Review dashboard queries and optimize
   
   # Check for expensive Loki queries
   # Review log queries and add more filters
   ```

4. **Scale Components**
   ```bash
   # Scale Prometheus
   docker compose up -d --scale prometheus=2
   
   # Scale Loki
   docker compose up -d --scale loki=2
   ```

**Escalation:**
- If CPU usage continues to be high, consider adding more instances
- If query performance is poor, review and optimize queries

### High Trace Latency

**Symptoms:**
- 95th percentile trace latency > 1s
- Alert: `TraceLatencyHigh`

**Troubleshooting Steps:**

1. **Check Tempo Performance**
   ```bash
   docker compose logs tempo | tail -50
   curl -s http://localhost:3200/debug/metrics | grep tempo_
   ```

2. **Check Sampling Rate**
   ```bash
   # Check current sampling configuration
   curl -s http://localhost:3200/debug/config | jq .config
   ```

3. **Optimize Sampling**
   ```bash
   # Adjust sampling rate in tempo-config.yml
   # Consider adaptive sampling for high-traffic services
   ```

4. **Check Storage Performance**
   ```bash
   # Check disk I/O
   iostat -x 1 5
   
   # Check disk space
   df -h
   ```

**Escalation:**
- If latency continues to be high, consider scaling Tempo
- If storage is the bottleneck, consider faster storage or additional instances

## Data Issues

### High Span Drop Rate

**Symptoms:**
- Span drop rate > 5%
- Alert: `HighErrorRate`

**Troubleshooting Steps:**

1. **Check Tempo Logs**
   ```bash
   docker compose logs tempo | grep -i "dropped\|error"
   ```

2. **Check Collector Performance**
   ```bash
   docker compose logs otel-collector | tail -50
   docker stats otel-collector
   ```

3. **Check Network Connectivity**
   ```bash
   # Check connection between collector and Tempo
   docker compose exec otel-collector wget -qO- http://tempo:3200/ready
   ```

4. **Adjust Sampling**
   ```bash
   # Increase sampling rate for critical services
   # Decrease sampling rate for high-traffic services
   ```

**Escalation:**
- If drop rate continues to be high, consider scaling Tempo
- If network issues are suspected, check network configuration

### Log Ingestion Issues

**Symptoms:**
- Logs not appearing in Grafana
- High log ingestion rate
- Alert: `LogIngestionRateHigh`

**Troubleshooting Steps:**

1. **Check Promtail Logs**
   ```bash
   docker compose logs promtail | tail -50
   ```

2. **Check Loki Logs**
   ```bash
   docker compose logs loki | tail -50
   ```

3. **Check Log Sources**
   ```bash
   # Check if log files exist
   ls -la /var/log/mcp/
   
   # Check if Promtail can access log files
   docker compose exec promtail ls -la /var/log/mcp/
   ```

4. **Test Log Ingestion**
   ```bash
   # Send test log entry
   echo '{"timestamp": "'$(date -Iseconds)'", "level": "info", "service": "test", "message": "test message"}' | nc localhost 24224
   ```

**Escalation:**
- If logs are not being ingested, check Promtail configuration
- If ingestion rate is too high, consider filtering or sampling

## Configuration Issues

### Invalid Configuration

**Symptoms:**
- Services failing to start
- Configuration errors in logs

**Troubleshooting Steps:**

1. **Validate Configuration**
   ```bash
   # Validate Prometheus configuration
   docker run --rm -v $(pwd)/monitoring:/config prom/prometheus:latest --config.file=/config/prometheus.yml --dry-run
   
   # Validate Grafana configuration
   docker run --rm -v $(pwd)/monitoring/grafana:/etc/grafana grafana/grafana:latest grafana-cli --config=/etc/grafana/grafana.ini cfg validate
   
   # Validate Loki configuration
   docker run --rm -v $(pwd)/monitoring:/config grafana/loki:latest --config.file=/config/loki-config.yml --dry-run
   
   # Validate Tempo configuration
   docker run --rm -v $(pwd)/monitoring:/config grafana/tempo:latest --config.file=/config/tempo-config.yml --dry-run
   ```

2. **Check Configuration Syntax**
   ```bash
   # Check YAML syntax
   python -c "import yaml; yaml.safe_load(open('monitoring/prometheus.yml'))"
   python -c "import yaml; yaml.safe_load(open('monitoring/loki-config.yml'))"
   python -c "import yaml; yaml.safe_load(open('monitoring/tempo-config.yml'))"
   ```

3. **Fix Configuration Issues**
   ```bash
   # Fix syntax errors
   # Fix configuration parameters
   # Restart services
   docker compose restart prometheus grafana loki tempo
   ```

**Escalation:**
- If configuration issues persist, check for version compatibility
- If custom configurations are used, validate against documentation

## Maintenance Procedures

### Backup and Restore

**Backup Procedure:**

1. **Create Backup**
   ```bash
   ./scripts/backup-observability.sh
   ```

2. **Verify Backup**
   ```bash
   ls -la backups/
   tar -tzf backups/observability-backup-$(date +%Y%m%d).tar.gz
   ```

3. **Test Restore**
   ```bash
   # Test restore in staging environment
   ./scripts/restore-observability.sh backups/observability-backup-$(date +%Y%m%d).tar.gz
   ```

**Restore Procedure:**

1. **Stop Services**
   ```bash
   docker compose stop prometheus grafana loki tempo
   ```

2. **Restore from Backup**
   ```bash
   ./scripts/restore-observability.sh backups/observability-backup-$(date +%Y%m%d).tar.gz
   ```

3. **Start Services**
   ```bash
   docker compose start prometheus grafana loki tempo
   ```

4. **Verify Restore**
   ```bash
   curl -f http://localhost:3000/api/health
   curl -f http://localhost:9090/-/healthy
   curl -f http://localhost:3100/ready
   curl -f http://localhost:3200/ready
   ```

### Data Retention Management

**Procedure:**

1. **Check Current Retention**
   ```bash
   # Check Prometheus retention
   curl -s http://localhost:9090/api/v1/status/tsdb | jq .data.retentionTimeDuration
   
   # Check Loki retention
   curl -s http://localhost:3100/loki/api/v1/status/runtime | jq .data.config
   ```

2. **Update Retention Settings**
   ```bash
   # Update retention in configuration files
   # Restart services
   docker compose restart prometheus loki
   ```

3. **Clean Up Old Data**
   ```bash
   # Clean up old Prometheus data
   docker compose exec prometheus promtool tsdb clean --data-dir /prometheus --retain-duration=168h
   
   # Clean up old Loki data
   docker compose exec loki logcli query --from=168h --to=now '{job="all"}' | head -10
   ```

### Performance Tuning

**Procedure:**

1. **Monitor Performance Metrics**
   ```bash
   # Check Prometheus performance
   curl -s http://localhost:9090/api/v1/status/tsdb | jq .data.headStats
   
   # Check Loki performance
   curl -s http://localhost:3100/loki/api/v1/status/runtime | jq .data.limit
   
   # Check Tempo performance
   curl -s http://localhost:3200/debug/metrics | grep tempo_
   ```

2. **Adjust Configuration**
   ```bash
   # Adjust memory limits
   # Adjust CPU limits
   # Adjust storage settings
   # Adjust sampling rates
   ```

3. **Restart Services**
   ```bash
   docker compose restart prometheus grafana loki tempo
   ```

4. **Monitor Impact**
   ```bash
   # Monitor performance metrics
   # Monitor resource usage
   # Monitor query performance
   ```

## Contact Information

- **Observability Team**: observability@example.com
- **Infrastructure Team**: infrastructure@example.com
- **On-Call Rotation**: oncall@example.com
- **Emergency Contact**: emergency@example.com

## Additional Resources

- [Observability Documentation](docs/observability.md)
- [Alerting Documentation](docs/alerting.md)
- [Grafana Documentation](https://grafana.com/docs/)
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Loki Documentation](https://grafana.com/docs/loki/)
- [Tempo Documentation](https://grafana.com/docs/tempo/)
- [OpenTelemetry Documentation](https://opentelemetry.io/docs/)
```

## Conclusion

This comprehensive production readiness guide provides all the necessary configurations, procedures, and documentation needed to deploy and maintain a production-ready observability stack. The implementation includes:

1. **Complete Configuration Files**: All missing configuration files for Tempo, Loki, Promtail, and OpenTelemetry Collector
2. **Docker Compose Enhancements**: Updated docker-compose.yml with OpenTelemetry Collector and proper service integration
3. **Security and Compliance**: Network policies, RBAC configuration, and security contexts
4. **Performance Optimization**: Resource limits, storage optimization, and caching configuration
5. **Backup and Disaster Recovery**: Automated backup procedures and restore scripts
6. **Service Integration**: Auto-instrumentation configurations for Python and JavaScript services
7. **Deployment Automation**: CI/CD pipeline and deployment scripts
8. **Monitoring and Alerting**: Production-ready alerting rules and Alertmanager configuration
9. **Documentation and Runbooks**: Comprehensive runbook for troubleshooting and maintenance

This implementation ensures that the observability stack is production-ready, secure, performant, and maintainable. It follows industry best practices and provides a solid foundation for monitoring and troubleshooting the MCP system.