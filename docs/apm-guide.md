# Application Performance Monitoring (APM) Guide

This guide provides comprehensive documentation for the Application Performance Monitoring (APM) system implemented for the MCP (Multimodal Content Processor) platform.

## Overview

The MCP APM system provides end-to-end performance monitoring for all services, offering deep insights into application performance, resource usage, and operational metrics. The system is built on OpenTelemetry standards and integrates seamlessly with the existing observability stack.

## Architecture

### Core Components

1. **APM Framework** (`src/common/apm.py`)
   - Central APM instrumentation framework
   - Resource monitoring and performance baselines
   - Anomaly detection and alerting
   - OpenTelemetry integration

2. **Service-Specific APM** (Each service has its own APM module)
   - Model Router APM (`src/model_router/apm.py`)
   - Plan Management APM (`src/plan_management/apm.py`)
   - Git Worktree APM (`src/git_worktree/apm.py`)
   - Workflow Orchestrator APM (`src/workflow_orchestrator/apm.py`)
   - Verification Feedback APM (`src/verification_feedback/apm.py`)

3. **Performance Profiling** (`src/common/performance_profiling.py`)
   - CPU and memory profiling
   - Database query performance
   - External API call tracking

4. **Performance Baselines** (`src/common/performance_baselines.py`)
   - Automatic baseline calculation
   - Performance trend analysis
   - Anomaly detection

### Data Flow

```
Application Code → APM Instrumentation → OpenTelemetry → Prometheus/Grafana
                ↓
        Performance Metrics → Resource Monitoring → Anomaly Detection
                ↓
        Performance Insights → Alerting → Dashboards
```

## Key Features

### 1. Comprehensive Performance Monitoring

- **Operation Tracking**: Monitor all business operations with detailed timing and resource usage
- **Resource Monitoring**: Real-time CPU, memory, disk I/O, and network I/O monitoring
- **Custom Metrics**: Service-specific metrics for business logic and performance
- **Async Support**: Full support for both synchronous and asynchronous operations

### 2. Performance Baselines and Anomaly Detection

- **Automatic Baselines**: Automatically calculate performance baselines from historical data
- **Anomaly Detection**: Detect performance anomalies using statistical analysis
- **Trend Analysis**: Track performance trends over time
- **Threshold Alerting**: Configurable thresholds for performance metrics

### 3. Service-Specific Monitoring

Each MCP service has tailored APM implementation:

#### Model Router APM
- Model selection performance
- Request routing metrics
- Token usage tracking
- Cache performance monitoring
- Ensemble routing analysis

#### Plan Management APM
- Task decomposition performance
- Consensus building metrics
- Storage operation tracking
- Plan generation analysis

#### Git Worktree APM
- Repository operation performance
- Worktree management metrics
- Merge operation tracking
- File system performance

#### Workflow Orchestrator APM
- Workflow execution performance
- Agent coordination metrics
- Step processing analysis
- Workflow state tracking

#### Verification Feedback APM
- Code analysis performance
- Security scanning metrics
- Quality assessment tracking
- Verification pipeline analysis

### 4. Integration with Observability Stack

- **Distributed Tracing**: Full integration with OpenTelemetry tracing
- **Metrics Collection**: Prometheus-compatible metrics export
- **Logging**: Correlated logging with performance data
- **Dashboards**: Grafana dashboards for performance visualization

## Getting Started

### 1. Basic Usage

```python
from src.common.apm import get_apm, APMOperationType

# Get APM instance
apm = get_apm()

# Trace an operation
with apm.trace_operation("user_login", APMOperationType.HTTP_REQUEST, {"user_id": "123"}):
    # Your business logic here
    result = perform_login()
    return result
```

### 2. Async Operations

```python
import asyncio
from src.common.apm import get_apm, APMOperationType

async def async_operation():
    apm = get_apm()
    
    async with apm.trace_async_operation("async_task", APMOperationType.CUSTOM_OPERATION):
        # Your async business logic here
        result = await perform_async_task()
        return result
```

### 3. Service-Specific APM

```python
from src.model_router.apm import get_model_router_apm

async def model_request():
    apm = get_model_router_apm()
    
    async with apm.trace_model_request("claude-3-sonnet", "generate", input_text="Hello"):
        # Model request logic
        result = await call_model()
        return result
```

### 4. Decorators for Easy Integration

```python
from src.common.apm import apm_traced, APMOperationType

@apm_traced(operation_type=APMOperationType.BUSINESS_TRANSACTION)
def business_function():
    # Your business logic here
    return result
```

## Configuration

### APM Configuration

```python
from src.common.apm import APMConfig

config = APMConfig(
    enabled=True,
    profiling_enabled=True,
    memory_profiling_enabled=True,
    cpu_profiling_enabled=True,
    database_monitoring_enabled=True,
    external_api_monitoring_enabled=True,
    business_transaction_monitoring_enabled=True,
    anomaly_detection_enabled=True,
    baseline_estimation_enabled=True,
    
    # Performance thresholds
    slow_request_threshold=1.0,  # seconds
    memory_usage_threshold=0.8,  # 80%
    cpu_usage_threshold=0.8,  # 80%
    database_query_threshold=0.5,  # seconds
    external_api_threshold=2.0,  # seconds
    
    # Sampling configuration
    profiling_sample_rate=0.1,  # 10%
    memory_sample_rate=0.05,  # 5%
    
    # Baseline configuration
    baseline_window_size=100,  # number of samples
    baseline_update_interval=300,  # seconds
    
    # Anomaly detection configuration
    anomaly_detection_sensitivity=2.0,  # standard deviations
    anomaly_window_size=20  # number of recent samples
)
```

### Environment Variables

```bash
# Enable/disable APM
APM_ENABLED=true

# Profiling settings
APM_PROFILING_ENABLED=true
APM_MEMORY_PROFILING_ENABLED=true
APM_CPU_PROFILING_ENABLED=true

# Monitoring settings
APM_DATABASE_MONITORING_ENABLED=true
APM_EXTERNAL_API_MONITORING_ENABLED=true
APM_BUSINESS_TRANSACTION_MONITORING_ENABLED=true

# Thresholds
APM_SLOW_REQUEST_THRESHOLD=1.0
APM_MEMORY_USAGE_THRESHOLD=0.8
APM_CPU_USAGE_THRESHOLD=0.8

# Sampling rates
APM_PROFILING_SAMPLE_RATE=0.1
APM_MEMORY_SAMPLE_RATE=0.05
```

## Performance Metrics

### Standard Metrics

The APM system automatically collects the following metrics:

#### Counters
- `apm_operations_total`: Total number of operations monitored
- `apm_errors_total`: Total number of operation errors
- `apm_slow_operations_total`: Total number of slow operations

#### Histograms
- `apm_operation_duration_seconds`: Duration of operations
- `apm_memory_usage_bytes`: Memory usage during operations
- `apm_cpu_usage_percent`: CPU usage during operations

#### Gauges
- `apm_active_operations`: Number of currently active operations
- `apm_resource_usage`: Current resource usage

### Service-Specific Metrics

#### Model Router Metrics
- `model_router_model_requests_total`: Total model requests
- `model_router_routing_decisions_total`: Total routing decisions
- `model_router_token_usage_total`: Total token usage
- `model_router_request_duration_seconds`: Model request duration
- `model_router_confidence_score`: Routing confidence scores

#### Plan Management Metrics
- `plan_management_tasks_created_total`: Total tasks created
- `plan_management_consensus_duration_seconds`: Consensus building duration
- `plan_management_plan_generation_duration_seconds`: Plan generation duration

#### Git Worktree Metrics
- `git_worktree_operations_total`: Total git operations
- `git_worktree_operation_duration_seconds`: Git operation duration
- `git_worktree_worktree_size_bytes`: Worktree size metrics

#### Workflow Orchestrator Metrics
- `workflow_orchestrator_workflows_executed_total`: Total workflows executed
- `workflow_orchestrator_step_duration_seconds`: Step execution duration
- `workflow_orchestrator_agent_coordination_duration_seconds`: Agent coordination duration

#### Verification Feedback Metrics
- `verification_feedback_analyses_total`: Total analyses performed
- `verification_feedback_analysis_duration_seconds`: Analysis duration
- `verification_feedback_quality_score`: Quality assessment scores

## Performance Baselines

### Automatic Baseline Calculation

The APM system automatically calculates performance baselines for all operations:

```python
from src.common.apm import get_apm

apm = get_apm()

# Get performance baseline for an operation
baseline = apm.get_baselines().get("user_login")

if baseline:
    print(f"Mean duration: {baseline.mean_duration:.3f}s")
    print(f"P95 duration: {baseline.p95_duration:.3f}s")
    print(f"P99 duration: {baseline.p99_duration:.3f}s")
```

### Baseline Configuration

Baselines are calculated using a sliding window of historical data:

- **Window Size**: Number of samples to consider (default: 100)
- **Update Interval**: How often to update baselines (default: 300 seconds)
- **Statistical Measures**: Mean, median, P95, P99, standard deviation

## Anomaly Detection

### Statistical Anomaly Detection

The system uses statistical analysis to detect performance anomalies:

```python
from src.common.apm import get_apm

apm = get_apm()

# Get recent anomalies
anomalies = apm.get_recent_anomalies(count=10)

for anomaly in anomalies:
    print(f"Anomaly detected: {anomaly['operation_name']}")
    print(f"Duration: {anomaly['duration']:.3f}s")
    print(f"Baseline: {anomaly['baseline_mean']:.3f}s")
    print(f"Z-score: {anomaly['z_score']:.2f}")
    print(f"Severity: {anomaly['severity']}")
```

### Anomaly Configuration

- **Sensitivity**: Number of standard deviations for anomaly detection (default: 2.0)
- **Window Size**: Number of recent samples to consider (default: 20)
- **Severity Levels**: INFO, WARNING, ERROR, CRITICAL

## Performance Profiling

### CPU Profiling

```python
from src.common.performance_profiling import profile_cpu, get_cpu_profiler

# Get CPU profiler
profiler = get_cpu_profiler()

# Profile a function
@profile_cpu()
def cpu_intensive_function():
    # CPU-intensive logic here
    return result
```

### Memory Profiling

```python
from src.common.performance_profiling import profile_memory, get_memory_profiler

# Get memory profiler
profiler = get_memory_profiler()

# Profile a function
@profile_memory()
def memory_intensive_function():
    # Memory-intensive logic here
    return result
```

### Database Query Profiling

```python
from src.common.performance_profiling import profile_database_query

# Profile database query
with profile_database_query("SELECT * FROM users"):
    result = execute_query("SELECT * FROM users")
    return result
```

## Dashboards and Visualization

### Available Dashboards

The APM system provides several Grafana dashboards:

1. **Performance Dashboard** (`monitoring/grafana/dashboards/performance-dashboard.json`)
   - Overall system performance metrics
   - Resource usage trends
   - Operation duration analysis
   - Error rate monitoring

2. **Service-Specific Dashboards**
   - Model Router Dashboard
   - Plan Management Dashboard
   - Git Worktree Dashboard
   - Workflow Orchestrator Dashboard
   - Verification Feedback Dashboard

3. **Resource Usage Dashboard**
   - CPU usage monitoring
   - Memory usage tracking
   - Disk I/O analysis
   - Network I/O monitoring

### Dashboard Features

- **Real-time Metrics**: Live performance data
- **Historical Trends**: Performance trends over time
- **Anomaly Detection**: Visual indication of anomalies
- **Performance Baselines**: Comparison with historical baselines
- **Resource Utilization**: System resource usage monitoring

## Alerting and Notifications

### Performance Alerting

The APM system includes comprehensive alerting:

```python
from src.common.apm import get_apm

apm = get_apm()

# Check for performance issues
insights = apm.get_performance_insights()

for insight in insights:
    print(f"Type: {insight['type']}")
    print(f"Severity: {insight['severity']}")
    print(f"Message: {insight['message']}")
    print(f"Recommendation: {insight['recommendation']}")
```

### Alert Types

1. **Slow Operation Alerts**: Operations exceeding duration thresholds
2. **High Error Rate Alerts**: Services with high error rates
3. **Resource Usage Alerts**: High CPU or memory usage
4. **Anomaly Detection Alerts**: Statistical performance anomalies
5. **Baseline Deviation Alerts**: Operations deviating from baselines

### Alert Configuration

Alerts are configured through Prometheus alerting rules:

```yaml
groups:
  - name: apm_alerts
    rules:
      - alert: SlowOperationDetected
        expr: apm_operation_duration_seconds{quantile="0.95"} > 1.0
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Slow operation detected"
          description: "Operation {{ $labels.operation_name }} is slow ({{ $value }}s)"
```

## Testing and Validation

### APM Testing

```python
import pytest
from src.common.apm import get_apm

def test_apm_operation_tracing():
    apm = get_apm()
    
    with apm.trace_operation("test_operation", APMOperationType.CUSTOM_OPERATION):
        # Test operation
        result = test_function()
        assert result is not None
    
    # Verify metrics were recorded
    summary = apm.get_performance_summary("test_operation")
    assert summary["total_operations"] > 0
```

### Performance Testing

```python
from src.common.performance_profiling import profile_cpu, profile_memory

@profile_cpu()
@profile_memory()
def performance_test_function():
    # Performance-intensive test
    return result
```

### Integration Testing

```python
async def test_service_apm_integration():
    from src.model_router.apm import get_model_router_apm
    
    apm = get_model_router_apm()
    
    async with apm.trace_model_request("test-model", "generate", "test input"):
        # Test model request
        result = await test_model_request()
        return result
```

## Best Practices

### 1. Instrumentation Strategy

- **Strategic Instrumentation**: Focus on critical business operations
- **Consistent Naming**: Use consistent operation names and types
- **Context Enrichment**: Add relevant context to operations
- **Error Handling**: Ensure proper error handling in instrumented code

### 2. Performance Optimization

- **Sampling Rates**: Use appropriate sampling rates for high-volume operations
- **Resource Monitoring**: Monitor resource usage for performance-intensive operations
- **Baseline Management**: Regularly review and update performance baselines
- **Anomaly Detection**: Configure appropriate sensitivity levels

### 3. Monitoring and Alerting

- **Threshold Configuration**: Set appropriate thresholds for alerts
- **Alert Fatigue**: Avoid excessive alerting with proper threshold configuration
- **Alert Response**: Establish procedures for responding to performance alerts
- **Continuous Improvement**: Regularly review and improve monitoring strategies

### 4. Documentation and Maintenance

- **Operation Documentation**: Document instrumented operations and their purpose
- **Configuration Management**: Maintain APM configuration in version control
- **Regular Review**: Regularly review APM data and adjust configurations
- **Performance Reviews**: Conduct regular performance reviews using APM data

## Troubleshooting

### Common Issues

#### 1. High Memory Usage
```python
# Check memory usage
from src.common.apm import get_apm

apm = get_apm()
resource_usage = apm.get_current_resource_usage()
print(f"Memory usage: {resource_usage.memory_percent}%")
```

#### 2. Slow Operations
```python
# Get slow operations
from src.common.apm import get_apm

apm = get_apm()
summary = apm.get_performance_summary()

for operation, metrics in summary.items():
    if metrics["mean_duration"] > 1.0:
        print(f"Slow operation: {operation} ({metrics['mean_duration']:.3f}s)")
```

#### 3. High Error Rates
```python
# Check error rates
from src.common.apm import get_apm

apm = get_apm()
summary = apm.get_performance_summary()

for operation, metrics in summary.items():
    if metrics["success_rate"] < 0.95:
        print(f"High error rate: {operation} ({metrics['success_rate']:.2%})")
```

### Debug Mode

Enable debug logging for troubleshooting:

```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

# Use APM with debug enabled
from src.common.apm import APMConfig

config = APMConfig(
    enabled=True,
    debug_mode=True
)
```

## Integration Examples

### 1. Web Framework Integration

```python
from fastapi import FastAPI, Request
from src.common.apm import get_apm, APMOperationType

app = FastAPI()
apm = get_apm()

@app.middleware("http")
async def apm_middleware(request: Request, call_next):
    operation_name = f"{request.method} {request.url.path}"
    
    with apm.trace_operation(operation_name, APMOperationType.HTTP_REQUEST, {
        "http.method": request.method,
        "http.url": str(request.url),
        "http.user_agent": request.headers.get("user-agent")
    }):
        response = await call_next(request)
        return response
```

### 2. Database Integration

```python
from src.common.apm import get_apm, APMOperationType
from src.common.performance_profiling import profile_database_query

apm = get_apm()

def execute_query(query: str, params: dict = None):
    with apm.trace_operation("database_query", APMOperationType.DATABASE_QUERY, {
        "db.query": query,
        "db.has_params": params is not None
    }):
        with profile_database_query(query):
            # Execute database query
            result = database.execute(query, params)
            return result
```

### 3. External API Integration

```python
import httpx
from src.common.apm import get_apm, APMOperationType

apm = get_apm()

async def call_external_api(url: str, method: str = "GET", data: dict = None):
    with apm.trace_operation(f"{method} {url}", APMOperationType.EXTERNAL_API, {
        "external_api.url": url,
        "external_api.method": method,
        "external_api.has_data": data is not None
    }):
        async with httpx.AsyncClient() as client:
            if method == "GET":
                response = await client.get(url)
            elif method == "POST":
                response = await client.post(url, json=data)
            return response
```

## API Reference

### Core Classes

#### APMInstrumentation

Main APM instrumentation class.

```python
class APMInstrumentation:
    def __init__(self, config: APMConfig = None)
    def start() -> None
    def stop() -> None
    def trace_operation(operation_name: str, operation_type: APMOperationType, attributes: Dict[str, Any] = None) -> ContextManager
    def trace_async_operation(operation_name: str, operation_type: APMOperationType, attributes: Dict[str, Any] = None) -> AsyncContextManager
    def get_performance_summary(operation_name: str = None) -> Dict[str, Any]
    def get_current_resource_usage() -> ResourceUsage
    def get_baselines() -> Dict[str, PerformanceBaseline]
    def get_recent_anomalies(count: int = 10) -> List[Dict[str, Any]]
```

#### APMConfig

APM configuration class.

```python
@dataclass
class APMConfig:
    enabled: bool = True
    profiling_enabled: bool = True
    memory_profiling_enabled: bool = True
    cpu_profiling_enabled: bool = True
    database_monitoring_enabled: bool = True
    external_api_monitoring_enabled: bool = True
    business_transaction_monitoring_enabled: bool = True
    anomaly_detection_enabled: bool = True
    baseline_estimation_enabled: bool = True
    slow_request_threshold: float = 1.0
    memory_usage_threshold: float = 0.8
    cpu_usage_threshold: float = 0.8
    database_query_threshold: float = 0.5
    external_api_threshold: float = 2.0
    profiling_sample_rate: float = 0.1
    memory_sample_rate: float = 0.05
    baseline_window_size: int = 100
    baseline_update_interval: int = 300
    anomaly_detection_sensitivity: float = 2.0
    anomaly_window_size: int = 20
```

#### PerformanceMetrics

Performance metrics data structure.

```python
@dataclass
class PerformanceMetrics:
    operation_name: str
    operation_type: APMOperationType
    start_time: float
    end_time: float
    duration: float
    success: bool
    error_message: Optional[str] = None
    attributes: Dict[str, Any] = field(default_factory=dict)
    resource_usage: Dict[str, float] = field(default_factory=dict)
    custom_metrics: Dict[str, Union[int, float]] = field(default_factory=dict)
```

### Utility Functions

#### Global APM Instance

```python
def get_apm() -> APMInstrumentation
def initialize_apm(config: APMConfig = None) -> APMInstrumentation
```

#### Decorators

```python
def apm_traced(operation_name: str = None, operation_type: APMOperationType = APMOperationType.CUSTOM_OPERATION, attributes: Dict[str, Any] = None)
def trace_http_request(method: str, url: str, status_code: int, duration: float)
def trace_database_query(query: str, duration: float, success: bool = True)
def trace_external_api(service: str, endpoint: str, duration: float, success: bool = True)
```

## Conclusion

The MCP APM system provides comprehensive performance monitoring capabilities for all services in the platform. With its rich feature set, including automatic instrumentation, performance baselines, anomaly detection, and seamless integration with the existing observability stack, it enables teams to monitor, analyze, and optimize application performance effectively.

By following the guidelines and best practices outlined in this document, teams can leverage the APM system to gain deep insights into their application performance, identify and resolve performance issues quickly, and ensure optimal performance for their users.

For additional support or questions about the APM system, please refer to the troubleshooting section or contact the observability team.