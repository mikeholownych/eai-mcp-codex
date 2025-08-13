# OpenTelemetry Collector Configurations and Deployment Manifests

This document contains all the necessary configurations and Kubernetes manifests for deploying OpenTelemetry Collectors in the MCP system.

---

## 1. Gateway Collector Configuration

### 1.1 Collector Gateway ConfigMap

```yaml
# otel-collector-gateway-configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: otel-collector-gateway-config
  namespace: mcp-system
  labels:
    app: otel-collector-gateway
data:
  otel-collector-config.yaml: |
    receivers:
      otlp:
        protocols:
          grpc:
            endpoint: 0.0.0.0:4317
            max_recv_msg_size_mib: 32
            max_concurrent_streams: 1000
          http:
            endpoint: 0.0.0.0:4318
            cors:
              allowed_origins:
                - "http://*"
                - "https://*"
              allowed_headers:
                - "*"
      
      jaeger:
        protocols:
          thrift_compact:
            endpoint: 0.0.0.0:6831
          thrift_binary:
            endpoint: 0.0.0.0:6832
          thrift_http:
            endpoint: 0.0.0.0:14268
      
      zipkin:
        endpoint: 0.0.0.0:9411

    processors:
      batch:
        timeout: 1s
        send_batch_size: 1024
        send_batch_max_size: 1024
        metadata_keys:
          - "service.name"
          - "service.namespace"
          - "deployment.environment"
      
      memory_limiter:
        check_interval: 1s
        limit_mib: 512
        spike_limit_mib: 100
      
      resource:
        attributes:
          - key: environment
            value: production
            from_attribute: ENVIRONMENT
          - key: cluster
            value: mcp-prod
            from_attribute: CLUSTER_NAME
          - key: service.namespace
            value: mcp-system
            action: insert
      
      attributes:
        actions:
          - key: service.instance.id
            from_attribute: "host.name"
            action: upsert
          - key: host.name
            action: delete

    exporters:
      otlp:
        endpoint: otel-collector-processing:4317
        tls:
          insecure: true
        sending_queue:
          enabled: true
          num_consumers: 10
          queue_size: 5000
        retry_on_failure:
          enabled: true
          initial_interval: 5s
          max_interval: 30s
          max_elapsed_time: 300s
      
      debug:
        verbosity: detailed
        sampling_initial: 5
        sampling_thereafter: 100

    service:
      telemetry:
        metrics:
          address: 0.0.0.0:8888
      pipelines:
        traces:
          receivers: [otlp, jaeger, zipkin]
          processors: [memory_limiter, batch, resource, attributes]
          exporters: [otlp, debug]
```

### 1.2 Gateway Deployment Manifest

```yaml
# otel-collector-gateway-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: otel-collector-gateway
  namespace: mcp-system
  labels:
    app: otel-collector-gateway
    component: otel-collector
spec:
  replicas: 3
  selector:
    matchLabels:
      app: otel-collector-gateway
  template:
    metadata:
      labels:
        app: otel-collector-gateway
        component: otel-collector
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8888"
        prometheus.io/path: "/metrics"
    spec:
      containers:
      - name: otel-collector
        image: otel/opentelemetry-collector-contrib:0.87.0
        args:
        - --config=/conf/otel-collector-config.yaml
        - --metrics-addr=0.0.0.0:8888
        ports:
        - containerPort: 4317
          name: otlp-grpc
          protocol: TCP
        - containerPort: 4318
          name: otlp-http
          protocol: TCP
        - containerPort: 6831
          name: jaeger-compact
          protocol: UDP
        - containerPort: 6832
          name: jaeger-binary
          protocol: UDP
        - containerPort: 14268
          name: jaeger-http
          protocol: TCP
        - containerPort: 9411
          name: zipkin
          protocol: TCP
        - containerPort: 8888
          name: metrics
          protocol: TCP
        env:
        - name: POD_NAME
          valueFrom:
            fieldRef:
              fieldPath: metadata.name
        - name: POD_NAMESPACE
          valueFrom:
            fieldRef:
              fieldPath: metadata.namespace
        - name: NODE_NAME
          valueFrom:
            fieldRef:
              fieldPath: spec.nodeName
        - name: ENVIRONMENT
          value: "production"
        - name: CLUSTER_NAME
          value: "mcp-prod"
        volumeMounts:
        - name: config-volume
          mountPath: /conf
        resources:
          limits:
            cpu: "500m"
            memory: "512Mi"
          requests:
            cpu: "100m"
            memory: "128Mi"
        livenessProbe:
          httpGet:
            path: /
            port: 13133
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /
            port: 13133
          initialDelaySeconds: 5
          periodSeconds: 10
      volumes:
      - name: config-volume
        configMap:
          name: otel-collector-gateway-config
      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            podAffinityTerm:
              labelSelector:
                matchExpressions:
                - key: app
                  operator: In
                  values:
                  - otel-collector-gateway
              topologyKey: "kubernetes.io/hostname"
      tolerations:
      - key: "CriticalAddonsOnly"
        operator: "Exists"
      - key: "node-role.kubernetes.io/control-plane"
        operator: "Exists"
        effect: "NoSchedule"
```

### 1.3 Gateway Service Manifest

```yaml
# otel-collector-gateway-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: otel-collector-gateway
  namespace: mcp-system
  labels:
    app: otel-collector-gateway
    component: otel-collector
  annotations:
    prometheus.io/scrape: "true"
    prometheus.io/port: "8888"
    prometheus.io/path: "/metrics"
spec:
  type: ClusterIP
  ports:
  - name: otlp-grpc
    port: 4317
    targetPort: 4317
    protocol: TCP
  - name: otlp-http
    port: 4318
    targetPort: 4318
    protocol: TCP
  - name: jaeger-compact
    port: 6831
    targetPort: 6831
    protocol: UDP
  - name: jaeger-binary
    port: 6832
    targetPort: 6832
    protocol: UDP
  - name: jaeger-http
    port: 14268
    targetPort: 14268
    protocol: TCP
  - name: zipkin
    port: 9411
    targetPort: 9411
    protocol: TCP
  - name: metrics
    port: 8888
    targetPort: 8888
    protocol: TCP
  selector:
    app: otel-collector-gateway
```

---

## 2. Processing Collector Configuration

### 2.1 Processing Collector ConfigMap

```yaml
# otel-collector-processing-configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: otel-collector-processing-config
  namespace: mcp-system
  labels:
    app: otel-collector-processing
data:
  otel-collector-config.yaml: |
    receivers:
      otlp:
        protocols:
          grpc:
            endpoint: 0.0.0.0:4317
            max_recv_msg_size_mib: 64
            max_concurrent_streams: 1000
          http:
            endpoint: 0.0.0.0:4318

    processors:
      batch:
        timeout: 5s
        send_batch_size: 4096
        send_batch_max_size: 4096
        metadata_keys:
          - "service.name"
          - "service.namespace"
          - "deployment.environment"
      
      memory_limiter:
        check_interval: 1s
        limit_mib: 1024
        spike_limit_mib: 200
      
      tail_sampling:
        decision_wait: 10s
        num_traces: 100
        expected_new_traces_per_sec: 100
        policies:
          - name: error-policy
            type: status_code
            status_code:
              status_codes: [ERROR]
          - name: latency-policy
            type: latency
            latency:
              threshold_ms: 1000
          - name: probabilistic-policy
            type: probabilistic
            probabilistic:
              sampling_percentage: 10
          - name: and-policy
            type: and
            and:
              - type: string_attribute
                string_attribute:
                  key: mcp.critical_operation
                  values: ["true"]
              - type: probabilistic
                probabilistic:
                  sampling_percentage: 100
      
      attributes:
        actions:
          - key: service.namespace
            value: mcp-system
            action: upsert
          - key: deployment.environment
            value: production
            action: upsert
          - key: telemetry.sdk.language
            action: delete
          - key: telemetry.sdk.name
            action: delete
      
      resource_detection:
        detectors: [env, system]
        timeout: 10s
      
      spanmetrics:
        metrics_exporter: prometheus
        latency_histogram_buckets: [100us, 1ms, 2ms, 6ms, 10ms, 100ms, 250ms]
        dimensions:
          - name: http.method
          - name: http.status_code
          - name: service.name
          - name: operation

    exporters:
      jaeger:
        endpoint: jaeger-collector:14250
        tls:
          insecure: true
        sending_queue:
          enabled: true
          num_consumers: 10
          queue_size: 5000
        retry_on_failure:
          enabled: true
          initial_interval: 5s
          max_interval: 30s
          max_elapsed_time: 300s
      
      elasticsearch:
        endpoints: [http://elasticsearch:9200]
        index: mcp-traces
        pipeline: mcp-traces-pipeline
        num_shards: 3
        num_replicas: 1
        flush_interval: 5s
        sending_queue:
          enabled: true
          num_consumers: 10
          queue_size: 5000
        retry_on_failure:
          enabled: true
          initial_interval: 5s
          max_interval: 30s
          max_elapsed_time: 300s
      
      prometheus:
        endpoint: 0.0.0.0:9090
        namespace: mcp_traces
        const_labels:
          cluster: mcp-prod
        resource_to_telemetry_conversion:
          enabled: true
        add_metric_suffixes: true
      
      debug:
        verbosity: detailed
        sampling_initial: 5
        sampling_thereafter: 100

    service:
      telemetry:
        metrics:
          address: 0.0.0.0:8888
      pipelines:
        traces:
          receivers: [otlp]
          processors: [memory_limiter, batch, tail_sampling, attributes, resource_detection, spanmetrics]
          exporters: [jaeger, elasticsearch, debug]
        metrics:
          receivers: [otlp]
          processors: [memory_limiter, batch]
          exporters: [prometheus]
```

### 2.2 Processing Collector Deployment Manifest

```yaml
# otel-collector-processing-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: otel-collector-processing
  namespace: mcp-system
  labels:
    app: otel-collector-processing
    component: otel-collector
spec:
  replicas: 2
  selector:
    matchLabels:
      app: otel-collector-processing
  template:
    metadata:
      labels:
        app: otel-collector-processing
        component: otel-collector
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8888"
        prometheus.io/path: "/metrics"
    spec:
      containers:
      - name: otel-collector
        image: otel/opentelemetry-collector-contrib:0.87.0
        args:
        - --config=/conf/otel-collector-config.yaml
        - --metrics-addr=0.0.0.0:8888
        ports:
        - containerPort: 4317
          name: otlp-grpc
          protocol: TCP
        - containerPort: 4318
          name: otlp-http
          protocol: TCP
        - containerPort: 8888
          name: metrics
          protocol: TCP
        - containerPort: 9090
          name: prometheus
          protocol: TCP
        env:
        - name: POD_NAME
          valueFrom:
            fieldRef:
              fieldPath: metadata.name
        - name: POD_NAMESPACE
          valueFrom:
            fieldRef:
              fieldPath: metadata.namespace
        - name: NODE_NAME
          valueFrom:
            fieldRef:
              fieldPath: spec.nodeName
        volumeMounts:
        - name: config-volume
          mountPath: /conf
        resources:
          limits:
            cpu: "1000m"
            memory: "1Gi"
          requests:
            cpu: "200m"
            memory: "256Mi"
        livenessProbe:
          httpGet:
            path: /
            port: 13133
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /
            port: 13133
          initialDelaySeconds: 5
          periodSeconds: 10
      volumes:
      - name: config-volume
        configMap:
          name: otel-collector-processing-config
      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            podAffinityTerm:
              labelSelector:
                matchExpressions:
                - key: app
                  operator: In
                  values:
                  - otel-collector-processing
              topologyKey: "kubernetes.io/hostname"
```

### 2.3 Processing Collector Service Manifest

```yaml
# otel-collector-processing-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: otel-collector-processing
  namespace: mcp-system
  labels:
    app: otel-collector-processing
    component: otel-collector
  annotations:
    prometheus.io/scrape: "true"
    prometheus.io/port: "8888"
    prometheus.io/path: "/metrics"
spec:
  type: ClusterIP
  ports:
  - name: otlp-grpc
    port: 4317
    targetPort: 4317
    protocol: TCP
  - name: otlp-http
    port: 4318
    targetPort: 4318
    protocol: TCP
  - name: metrics
    port: 8888
    targetPort: 8888
    protocol: TCP
  - name: prometheus
    port: 9090
    targetPort: 9090
    protocol: TCP
  selector:
    app: otel-collector-processing
```

---

## 3. Jaeger Backend Configuration

### 3.1 Jaeger Collector Deployment

```yaml
# jaeger-collector-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: jaeger-collector
  namespace: mcp-system
  labels:
    app: jaeger-collector
    component: jaeger
spec:
  replicas: 2
  selector:
    matchLabels:
      app: jaeger-collector
  template:
    metadata:
      labels:
        app: jaeger-collector
        component: jaeger
    spec:
      containers:
      - name: jaeger-collector
        image: jaegertracing/jaeger-collector:1.49
        args:
        - --config-file=/conf/jaeger-collector.yaml
        ports:
        - containerPort: 14250
          name: grpc
          protocol: TCP
        - containerPort: 14267
          name: tchannel
          protocol: TCP
        - containerPort: 14268
          name: http
          protocol: TCP
        - containerPort: 9411
          name: zipkin
          protocol: TCP
        env:
        - name: SPAN_STORAGE_TYPE
          value: elasticsearch
        - name: ES_SERVER_URLS
          value: http://elasticsearch:9200
        - name: ES_INDEX_PREFIX
          value: jaeger
        - name: ES_TAGS_AS_FIELDS_ALL
          value: "true"
        - name: COLLECTOR_ZIPKIN_HTTP_PORT
          value: "9411"
        volumeMounts:
        - name: config-volume
          mountPath: /conf
        resources:
          limits:
            cpu: "500m"
            memory: "512Mi"
          requests:
            cpu: "100m"
            memory: "128Mi"
      volumes:
      - name: config-volume
        configMap:
          name: jaeger-collector-config
```

### 3.2 Jaeger Query Deployment

```yaml
# jaeger-query-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: jaeger-query
  namespace: mcp-system
  labels:
    app: jaeger-query
    component: jaeger
spec:
  replicas: 2
  selector:
    matchLabels:
      app: jaeger-query
  template:
    metadata:
      labels:
        app: jaeger-query
        component: jaeger
    spec:
      containers:
      - name: jaeger-query
        image: jaegertracing/jaeger-query:1.49
        args:
        - --config-file=/conf/jaeger-query.yaml
        ports:
        - containerPort: 16686
          name: query
          protocol: TCP
        - containerPort: 16687
          name: admin
          protocol: TCP
        env:
        - name: SPAN_STORAGE_TYPE
          value: elasticsearch
        - name: ES_SERVER_URLS
          value: http://elasticsearch:9200
        - name: ES_INDEX_PREFIX
          value: jaeger
        - name: QUERY_BASE_PATH
          value: /jaeger
        volumeMounts:
        - name: config-volume
          mountPath: /conf
        resources:
          limits:
            cpu: "200m"
            memory: "256Mi"
          requests:
            cpu: "50m"
            memory: "64Mi"
      volumes:
      - name: config-volume
        configMap:
          name: jaeger-query-config
```

### 3.3 Jaeger Services

```yaml
# jaeger-services.yaml
apiVersion: v1
kind: Service
metadata:
  name: jaeger-collector
  namespace: mcp-system
  labels:
    app: jaeger-collector
    component: jaeger
spec:
  type: ClusterIP
  ports:
  - name: grpc
    port: 14250
    targetPort: 14250
    protocol: TCP
  - name: tchannel
    port: 14267
    targetPort: 14267
    protocol: TCP
  - name: http
    port: 14268
    targetPort: 14268
    protocol: TCP
  - name: zipkin
    port: 9411
    targetPort: 9411
    protocol: TCP
  selector:
    app: jaeger-collector
---
apiVersion: v1
kind: Service
metadata:
  name: jaeger-query
  namespace: mcp-system
  labels:
    app: jaeger-query
    component: jaeger
spec:
  type: ClusterIP
  ports:
  - name: query
    port: 16686
    targetPort: 16686
    protocol: TCP
  - name: admin
    port: 16687
    targetPort: 16687
    protocol: TCP
  selector:
    app: jaeger-query
```

---

## 4. Elasticsearch Configuration for Traces

### 4.1 Elasticsearch Index Template

```yaml
# elasticsearch-traces-template.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: elasticsearch-traces-template
  namespace: mcp-system
data:
  template.json: |
    {
      "index_patterns": ["jaeger-span-*", "mcp-traces-*"],
      "settings": {
        "number_of_shards": 3,
        "number_of_replicas": 1,
        "index.refresh_interval": "5s",
        "index.lifecycle.name": "traces-ilm-policy",
        "index.lifecycle.rollover_alias": "jaeger-span",
        "index.mapping.coerce": true
      },
      "mappings": {
        "dynamic_templates": [
          {
            "strings_as_keyword": {
              "match_mapping_type": "string",
              "mapping": {
                "type": "keyword"
              }
            }
          }
        ],
        "properties": {
          "traceID": {
            "type": "keyword"
          },
          "spanID": {
            "type": "keyword"
          },
          "parentSpanID": {
            "type": "keyword"
          },
          "operationName": {
            "type": "keyword"
          },
          "serviceName": {
            "type": "keyword"
          },
          "serviceTags": {
            "type": "keyword"
          },
          "startTime": {
            "type": "date"
          },
          "duration": {
            "type": "long"
          },
          "tags": {
            "type": "object",
            "dynamic": true
          },
          "logs": {
            "type": "object",
            "properties": {
              "timestamp": {
                "type": "date"
              },
              "fields": {
                "type": "object",
                "dynamic": true
              }
            }
          },
          "process": {
            "type": "object",
            "properties": {
              "serviceName": {
                "type": "keyword"
              },
              "tags": {
                "type": "object",
                "dynamic": true
              }
            }
          },
          "references": {
            "type": "object",
            "properties": {
              "refType": {
                "type": "keyword"
              },
              "traceID": {
                "type": "keyword"
              },
              "spanID": {
                "type": "keyword"
              }
            }
          }
        }
      }
    }
```

### 4.2 Elasticsearch Ingest Pipeline

```yaml
# elasticsearch-traces-pipeline.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: elasticsearch-traces-pipeline
  namespace: mcp-system
data:
  pipeline.json: |
    {
      "description": "Pipeline for processing MCP traces",
      "processors": [
        {
          "set": {
            "field": "@timestamp",
            "value": "{{{startTime}}}"
          }
        },
        {
          "rename": {
            "field": "startTime",
            "target_field": "@timestamp"
          }
        },
        {
          "script": {
            "lang": "painless",
            "source": """
              if (ctx.tags == null) {
                ctx.tags = new HashMap();
              }
              if (ctx.serviceName != null) {
                ctx.tags.put('service.name', ctx.serviceName);
              }
              if (ctx.operationName != null) {
                ctx.tags.put('operation.name', ctx.operationName);
              }
              if (ctx.duration != null) {
                ctx.tags.put('duration_ms', ctx.duration);
              }
            """
          }
        },
        {
          "remove": {
            "field": ["startTime"]
          }
        }
      ]
    }
```

---

## 5. Prometheus ServiceMonitor for Collectors

```yaml
# otel-collector-servicemonitor.yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: otel-collector-gateway
  namespace: mcp-system
  labels:
    app: otel-collector-gateway
    component: otel-collector
spec:
  selector:
    matchLabels:
      app: otel-collector-gateway
  endpoints:
  - port: metrics
    interval: 15s
    path: /metrics
    scheme: http
    metricRelabelings:
    - sourceLabels: [__name__]
      regex: 'otel_collector_.*'
      action: keep
---
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: otel-collector-processing
  namespace: mcp-system
  labels:
    app: otel-collector-processing
    component: otel-collector
spec:
  selector:
    matchLabels:
      app: otel-collector-processing
  endpoints:
  - port: metrics
    interval: 15s
    path: /metrics
    scheme: http
    metricRelabelings:
    - sourceLabels: [__name__]
      regex: 'otel_collector_.*'
      action: keep
  - port: prometheus
    interval: 15s
    path: /metrics
    scheme: http
    metricRelabelings:
    - sourceLabels: [__name__]
      regex: 'traces_span_metrics_.*'
      action: keep
```

---

## 6. Network Policies

```yaml
# otel-collector-network-policy.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: otel-collector-gateway-netpol
  namespace: mcp-system
spec:
  podSelector:
    matchLabels:
      app: otel-collector-gateway
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: mcp-system
    - namespaceSelector:
        matchLabels:
          name: default
    ports:
    - protocol: TCP
      port: 4317
    - protocol: TCP
      port: 4318
    - protocol: UDP
      port: 6831
    - protocol: UDP
      port: 6832
    - protocol: TCP
      port: 14268
    - protocol: TCP
      port: 9411
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          name: mcp-system
    ports:
    - protocol: TCP
      port: 4317
    - protocol: TCP
      port: 8888
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: otel-collector-processing-netpol
  namespace: mcp-system
spec:
  podSelector:
    matchLabels:
      app: otel-collector-processing
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
      port: 4317
    - protocol: TCP
      port: 4318
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          name: mcp-system
    ports:
    - protocol: TCP
      port: 14250
    - protocol: TCP
      port: 9200
    - protocol: TCP
      port: 8888
    - protocol: TCP
      port: 9090
```

---

## 7. Deployment Script

```bash
#!/bin/bash
# deploy-opentelemetry.sh

set -e

NAMESPACE="mcp-system"

echo "Creating namespace if it doesn't exist..."
kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -

echo "Deploying OpenTelemetry Collector configurations..."
kubectl apply -f otel-collector-gateway-configmap.yaml
kubectl apply -f otel-collector-gateway-deployment.yaml
kubectl apply -f otel-collector-gateway-service.yaml

kubectl apply -f otel-collector-processing-configmap.yaml
kubectl apply -f otel-collector-processing-deployment.yaml
kubectl apply -f otel-collector-processing-service.yaml

echo "Deploying Jaeger backend..."
kubectl apply -f jaeger-collector-deployment.yaml
kubectl apply -f jaeger-query-deployment.yaml
kubectl apply -f jaeger-services.yaml

echo "Deploying Elasticsearch configurations..."
kubectl apply -f elasticsearch-traces-template.yaml
kubectl apply -f elasticsearch-traces-pipeline.yaml

echo "Deploying monitoring configurations..."
kubectl apply -f otel-collector-servicemonitor.yaml

echo "Deploying network policies..."
kubectl apply -f otel-collector-network-policy.yaml

echo "Waiting for deployments to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/otel-collector-gateway -n $NAMESPACE
kubectl wait --for=condition=available --timeout=300s deployment/otel-collector-processing -n $NAMESPACE
kubectl wait --for=condition=available --timeout=300s deployment/jaeger-collector -n $NAMESPACE
kubectl wait --for=condition=available --timeout=300s deployment/jaeger-query -n $NAMESPACE

echo "OpenTelemetry distributed tracing deployment completed successfully!"
echo ""
echo "Access points:"
echo "- Jaeger Query: http://localhost:16686 (if port-forwarded)"
echo "- OpenTelemetry Collector Gateway: otel-collector-gateway.$NAMESPACE.svc.cluster.local:4317"
echo "- OpenTelemetry Collector Processing: otel-collector-processing.$NAMESPACE.svc.cluster.local:4317"
```

---

## 8. Verification Commands

```bash
# Check collector status
kubectl get pods -n mcp-system -l component=otel-collector

# Check collector logs
kubectl logs -f deployment/otel-collector-gateway -n mcp-system
kubectl logs -f deployment/otel-collector-processing -n mcp-system

# Check Jaeger status
kubectl get pods -n mcp-system -l component=jaeger

# Port forward to Jaeger UI
kubectl port-forward -n mcp-system svc/jaeger-query 16686:16686

# Check metrics
kubectl port-forward -n mcp-system svc/otel-collector-gateway 8888:8888
curl http://localhost:8888/metrics

# Test trace ingestion
curl -X POST http://localhost:4318/v1/traces -H "Content-Type: application/json" -d '{
  "resourceSpans": [{
    "resource": {
      "attributes": [
        {"key": "service.name", "value": {"stringValue": "test-service"}},
        {"key": "service.namespace", "value": {"stringValue": "mcp-system"}}
      ]
    },
    "scopeSpans": [{
      "scope": {"name": "test-scope"},
      "spans": [{
        "traceId": "0102030405060708090a0b0c0d0e0f10",
        "spanId": "0102030405060708",
        "name": "test-span",
        "startTimeUnixNano": "1634567890000000000",
        "endTimeUnixNano": "1634567891000000000",
        "status": {"code": "STATUS_CODE_OK"}
      }]
    }]
  }]
}'
```

This comprehensive configuration provides a complete OpenTelemetry deployment for the MCP system with proper scaling, monitoring, and security considerations.