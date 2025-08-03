# Distributed Tracing Implementation Guide

This document provides a comprehensive guide to the distributed tracing implementation for the EAI-MCP platform. The implementation uses OpenTelemetry to provide complete request flow visibility across all MCP services.

## Overview

The distributed tracing system provides:

- **End-to-end visibility**: Track requests as they flow through multiple services
- **Performance monitoring**: Identify bottlenecks and latency issues
- **Error tracking**: Correlate errors across service boundaries
- **Dependency mapping**: Understand service interactions and dependencies
- **Resource utilization**: Monitor resource usage across the system

## Architecture

The tracing system consists of the following components:

1. **Tracing Configuration** (`src/common/tracing.py`): Core configuration and utilities
2. **Trace Propagation** (`src/common/trace_propagation.py`): Context propagation between services
3. **Service Instrumentation**: Service-specific tracing implementations
4. **Message Queue Tracing** (`src/common/message_queue_tracing.py`): RabbitMQ tracing
5. **Database Tracing** (`src/common/database_tracing.py`): Database operation tracing
6. **LLM Tracing** (`src/common/llm_tracing.py`): LLM operation tracing
7. **Sampling and Filtering** (`src/common/trace_sampling.py`): Adaptive sampling and privacy filtering
8. **Exporters** (`src/common/trace_exporters.py`): Jaeger and OTLP exporters
9. **Validation** (`src/common/trace_validation.py`): Trace validation and health checks
10. **Integration** (`src/common/tracing_integration.py`): Main integration interface

## Quick Start

### 1. Basic Initialization

```python
from src.common.tracing_integration import initialize_tracing, trace_operation

# Initialize tracing for your service
tracing = initialize_tracing(
    service_name="your-service",
    service_version="1.0.0",
    environment="development"
)

# Use the context manager for tracing operations
with trace_operation("user_login", {"user_id": "123"}) as span:
    # Your business logic here
    span.set_attribute("login_method", "oauth")
    result = perform_login()
    return result
```

### 2. Service-Specific Initialization

```python
# For model-router service
from src.common.tracing_integration import initialize_model_router_tracing

tracing = initialize_model_router_tracing()

# For plan-management service
from src.common.tracing_integration import initialize_plan_management_tracing

tracing = initialize_plan_management_tracing()
```

### 3. Async Operations

```python
from src.common.tracing_integration import trace_async_operation

async def process_request(request):
    async with trace_async_operation("process_request", {"request_id": request.id}) as span:
        # Your async business logic here
        result = await async_process(request)
        return result
```

## Detailed Usage

### HTTP Request Tracing

```python
from src.common.tracing_integration import trace_http_request

# Trace HTTP requests
trace_http_request(
    method="POST",
    url="/api/users",
    status_code=201,
    duration=0.245
)
```

### Database Operation Tracing

```python
from src.common.tracing_integration import trace_database_operation

# Trace database operations
trace_database_operation(
    operation="SELECT",
    table="users",
    duration=0.012,
    error=None  # Set error message if operation failed
)
```

### LLM Call Tracing

```python
from src.common.tracing_integration import trace_llm_call

# Trace LLM calls
trace_llm_call(
    model="claude-3-sonnet",
    prompt_length=150,
    response_length=500,
    duration=2.3,
    token_usage={
        "prompt_tokens": 150,
        "completion_tokens": 500,
        "total_tokens": 650
    }
)
```

### Message Queue Tracing

```python
from src.common.tracing_integration import trace_message_queue_operation

# Trace message queue operations
trace_message_queue_operation(
    operation="publish",
    queue="user_events",
    message_count=1,
    duration=0.005
)
```

## Advanced Features

### 1. Custom Spans

```python
from src.common.tracing_integration import get_tracer

tracer = get_tracer()

with tracer.start_as_current_span("custom_operation") as span:
    span.set_attribute("custom.attribute", "value")
    span.set_attribute("operation.complexity", "high")
    
    # Your custom logic here
    result = perform_custom_operation()
    
    span.set_status(Status(StatusCode.OK))
    return result
```

### 2. Trace Context Propagation

```python
from src.common.tracing_integration import get_propagation_utils

# Get propagation utilities
propagation_utils = get_propagation_utils()

# Inject trace context into HTTP headers
headers = {}
propagation_utils.inject_trace_context(headers)

# Extract trace context from HTTP headers
context = propagation_utils.extract_trace_context(headers)
```

### 3. Message Queue Tracing

```python
from src.common.tracing_integration import get_message_queue_tracing

# Get message queue tracing utilities
mq_tracing = get_message_queue_tracing()

# Trace message publishing
await mq_tracing.trace_message_publish(
    queue_name="task_queue",
    message={"task": "process_data"},
    headers={}
)

# Trace message consumption
await mq_tracing.trace_message_consume(
    queue_name="task_queue",
    message={"task": "process_data"},
    headers={}
)
```

### 4. Database Tracing

```python
from src.common.tracing_integration import get_database_tracing

# Get database tracing utilities
db_tracing = get_database_tracing()

# Trace database query
with db_tracing.trace_database_query("SELECT * FROM users") as span:
    results = execute_query("SELECT * FROM users")
    return results

# Trace database transaction
async with db_tracing.trace_database_transaction() as span:
    await execute_transaction()
```

### 5. LLM Tracing

```python
from src.common.tracing_integration import get_llm_tracing

# Get LLM tracing utilities
llm_tracing = get_llm_tracing()

# Trace LLM request
async with llm_tracing.trace_llm_request(
    model_name="claude-3-sonnet",
    request_type="completion",
    prompt="What is distributed tracing?"
) as span:
    response = await call_llm("What is distributed tracing?")
    return response

# Trace LLM response
async with llm_tracing.trace_llm_response(
    model_name="claude-3-sonnet",
    response_text="Distributed tracing is...",
    token_usage={"total_tokens": 100}
) as span:
    # Process response
    return processed_response
```

## Configuration

### Environment Variables

The tracing system can be configured using environment variables:

```bash
# General configuration
SERVICE_NAME=your-service
SERVICE_VERSION=1.0.0
ENVIRONMENT=development

# Jaeger exporter
JAEGER_ENABLED=true
JAEGER_ENDPOINT=http://jaeger-collector:14268/api/traces
JAEGER_TIMEOUT=30
JAEGER_COMPRESSION=gzip

# OTLP exporter
OTLP_ENABLED=false
OTLP_ENDPOINT=http://otel-collector:4317
OTLP_TIMEOUT=30
OTLP_COMPRESSION=gzip

# Zipkin exporter
ZIPKIN_ENABLED=false
ZIPKIN_ENDPOINT=http://zipkin:9411/api/v2/spans

# Console exporter (for development)
CONSOLE_EXPORTER_ENABLED=false

# Logging exporter
LOGGING_EXPORTER_ENABLED=false

# Prometheus metrics
PROMETHEUS_ENABLED=true
```

### Configuration File

You can also configure tracing using a YAML file:

```yaml
# config/tracing.yml
tracing:
  enabled: true
  service_name: "${SERVICE_NAME:-eai-mcp-platform}"
  service_version: "${SERVICE_VERSION:-1.0.0}"
  environment: "${ENVIRONMENT:-development}"
  
  otel:
    sampling:
      ratio: "${TRACE_SAMPLE_RATIO:-1.0}"
      adaptive:
        enabled: true
        target_tps: 10
        max_tps: 100
    
    exporters:
      jaeger:
        enabled: true
        endpoint: "http://jaeger:14268/api/traces"
      
      otlp:
        enabled: false
        endpoint: "http://otel-collector:4317"
```

## Sampling and Filtering

### Adaptive Sampling

The system implements adaptive sampling based on service load:

```python
from src.common.tracing_integration import get_sampling_manager

# Get sampling manager
sampling_manager = get_sampling_manager()

# Configure sampling parameters
sampling_manager.configure_sampler(
    base_sample_rate=0.1,
    max_sample_rate=1.0,
    target_tps=10,
    max_tps=100
)

# Get sampling statistics
stats = sampling_manager.get_sampling_stats()
print(f"Current TPS: {stats['current_tps']}")
```

### Privacy Filtering

The system includes privacy-conscious filtering for sensitive data:

```python
from src.common.tracing_integration import get_privacy_filter

# Get privacy filter
privacy_filter = get_privacy_filter()

# Filter sensitive data from attributes
filtered_attributes = privacy_filter.filter_attributes({
    "user_id": "123",
    "password": "secret123",
    "email": "user@example.com"
})

# Result: {"user_id": "123", "password": "***", "email": "***"}
```

## Health Checks and Validation

### Health Checks

```python
from src.common.tracing_integration import get_tracing_health

# Get tracing health status
health_status = get_tracing_health()
print(f"Overall status: {health_status['overall_status']}")
```

### Trace Validation

```python
from src.common.tracing_integration import get_validator

# Get trace validator
validator = get_validator()

# Validate a trace
validation_report = validator.validate_trace(spans)
print(f"Validation status: {validation_report.overall_status}")
```

### Integration Tests

```python
from src.common.tracing_integration import run_tracing_integration_tests

# Run integration tests
test_results = await run_tracing_integration_tests()
print(f"Test status: {test_results['overall_status']}")
```

## Service-Specific Implementation

### Model Router Service

```python
# src/model_router/main.py
from src.common.tracing_integration import (
    initialize_model_router_tracing,
    trace_llm_call,
    trace_http_request
)

# Initialize tracing
tracing = initialize_model_router_tracing()

async def route_request(request):
    with trace_operation("model_routing", {"request_id": request.id}) as span:
        # Route to appropriate model
        selected_model = select_model(request)
        
        # Trace LLM call
        trace_llm_call(
            model=selected_model,
            prompt_length=len(request.prompt),
            response_length=len(response),
            duration=response_time,
            token_usage=response.token_usage
        )
        
        return response
```

### Plan Management Service

```python
# src/plan_management/main.py
from src.common.tracing_integration import (
    initialize_plan_management_tracing,
    trace_database_operation,
    trace_async_operation
)

# Initialize tracing
tracing = initialize_plan_management_tracing()

async def create_plan(plan_request):
    async with trace_async_operation("create_plan", {"plan_id": plan_request.id}) as span:
        # Trace database operation
        trace_database_operation(
            operation="INSERT",
            table="plans",
            duration=0.025
        )
        
        # Create plan
        plan = await create_plan_in_database(plan_request)
        return plan
```

### Git Worktree Manager Service

```python
# src/git_worktree/main.py
from src.common.tracing_integration import (
    initialize_git_worktree_tracing,
    trace_operation,
    trace_database_operation
)

# Initialize tracing
tracing = initialize_git_worktree_tracing()

def create_worktree(request):
    with trace_operation("create_worktree", {"repo": request.repo_name}) as span:
        # Trace git operation
        span.set_attribute("git.operation", "worktree_create")
        span.set_attribute("git.branch", request.branch)
        
        # Create worktree
        worktree = create_git_worktree(request)
        
        # Trace database operation
        trace_database_operation(
            operation="INSERT",
            table="worktrees",
            duration=0.015
        )
        
        return worktree
```

### Workflow Orchestrator Service

```python
# src/workflow_orchestrator/main.py
from src.common.tracing_integration import (
    initialize_workflow_orchestrator_tracing,
    trace_async_operation,
    trace_message_queue_operation
)

# Initialize tracing
tracing = initialize_workflow_orchestrator_tracing()

async def execute_workflow(workflow):
    async with trace_async_operation("execute_workflow", {"workflow_id": workflow.id}) as span:
        # Trace message queue operation
        trace_message_queue_operation(
            operation="publish",
            queue="workflow_tasks",
            message_count=len(workflow.tasks),
            duration=0.003
        )
        
        # Execute workflow
        result = await execute_workflow_steps(workflow)
        return result
```

### Verification Feedback Service

```python
# src/verification_feedback/main.py
from src.common.tracing_integration import (
    initialize_verification_feedback_tracing,
    trace_operation,
    trace_database_operation
)

# Initialize tracing
tracing = initialize_verification_feedback_tracing()

def verify_code(code):
    with trace_operation("verify_code", {"code_id": code.id}) as span:
        # Trace verification operation
        span.set_attribute("verification.type", "security")
        span.set_attribute("verification.complexity", "high")
        
        # Perform verification
        result = perform_verification(code)
        
        # Trace database operation
        trace_database_operation(
            operation="INSERT",
            table="verification_results",
            duration=0.045
        )
        
        return result
```

## Monitoring and Observability

### Jaeger UI

Access the Jaeger UI at `http://localhost:16686` to view and analyze traces:

1. **Service Map**: Visualize service dependencies
2. **Search**: Find traces by service, operation, or tags
3. **Trace Details**: View detailed trace information
4. **Compare**: Compare multiple traces
5. **Dependencies**: Analyze service dependencies

### Prometheus Metrics

The system exports metrics to Prometheus:

- `spans_created_total`: Total number of spans created
- `spans_exported_total`: Total number of spans exported
- `trace_errors_total`: Total number of trace errors
- `llm_requests_total`: Total number of LLM requests
- `llm_tokens_total`: Total number of tokens processed
- `exporter_up`: Exporter health status

### Grafana Dashboards

Import the provided Grafana dashboards for visualization:

1. **Trace Overview**: General tracing metrics
2. **LLM Tracing**: LLM-specific metrics
3. **Agent Collaboration**: Collaboration workflow metrics

## Best Practices

### 1. Span Naming

- Use clear, descriptive names
- Follow naming conventions: `service.operation`
- Include relevant context in the name

```python
# Good
"model_router.select_model"
"plan_management.create_plan"
"git_worktree.create_worktree"

# Avoid
"operation1"
"do_stuff"
"process"
```

### 2. Attributes

- Add relevant attributes to spans
- Use semantic conventions when possible
- Avoid adding sensitive information

```python
# Good
span.set_attribute("http.method", "POST")
span.set_attribute("http.status_code", 201)
span.set_attribute("user.id", "123")  # Non-sensitive identifier

# Avoid
span.set_attribute("password", "secret123")  # Sensitive data
span.set_attribute("raw_request", large_json_string)  # Too large
```

### 3. Error Handling

- Always set span status for errors
- Record exceptions when they occur
- Include error context in attributes

```python
try:
    result = perform_operation()
    span.set_status(Status(StatusCode.OK))
except Exception as e:
    span.set_status(Status(StatusCode.ERROR, str(e)))
    span.record_exception(e)
    span.set_attribute("error.type", type(e).__name__)
    raise
```

### 4. Performance Considerations

- Use sampling for high-volume operations
- Avoid creating too many spans for simple operations
- Consider the impact on system performance

```python
# Good - Use sampling for high-volume operations
with trace_operation("high_volume_operation") as span:
    # Operation logic here
    pass

# Avoid - Creating too many spans
for item in large_list:
    with trace_operation("process_item"):  # Too many spans
        process_item(item)
```

## Troubleshooting

### Common Issues

1. **Traces not appearing in Jaeger**
   - Check if Jaeger is running
   - Verify exporter configuration
   - Check network connectivity

2. **High memory usage**
   - Adjust sampling rates
   - Reduce span attributes
   - Check for span leaks

3. **Missing trace context**
   - Verify context propagation
   - Check middleware configuration
   - Ensure proper header handling

### Debug Mode

Enable debug mode for detailed logging:

```python
import os
os.environ['DEBUG_TRACING'] = 'true'

# Or in configuration
tracing:
  development:
    debug:
      enabled: true
      log_level: "debug"
      console_exporter: true
```

### Health Checks

Run health checks to diagnose issues:

```python
from src.common.tracing_integration import get_tracing_health

health = get_tracing_health()
print(health)
```

## Integration with Existing Systems

### FastAPI Integration

```python
from fastapi import FastAPI, Request
from src.common.tracing_integration import trace_http_request

app = FastAPI()

@app.middleware("http")
async def tracing_middleware(request: Request, call_next):
    start_time = time.time()
    
    response = await call_next(request)
    
    # Trace the HTTP request
    trace_http_request(
        method=request.method,
        str(request.url),
        response.status_code,
        time.time() - start_time
    )
    
    return response
```

### Database Integration

```python
import asyncpg
from src.common.tracing_integration import get_database_tracing

db_tracing = get_database_tracing()

async def execute_query(query: str):
    with db_tracing.trace_database_query(query) as span:
        conn = await asyncpg.connect(DATABASE_URL)
        try:
            result = await conn.fetch(query)
            span.set_attribute("db.rows_affected", len(result))
            return result
        finally:
            await conn.close()
```

### Message Queue Integration

```python
import aio_pika
from src.common.tracing_integration import get_message_queue_tracing

mq_tracing = get_message_queue_tracing()

async def publish_message(queue_name: str, message: dict):
    await mq_tracing.trace_message_publish(queue_name, message, {})
    
    connection = await aio_pika.connect_robust(RABBITMQ_URL)
    async with connection:
        channel = await connection.channel()
        await channel.default_exchange.publish(
            aio_pika.Message(body=json.dumps(message).encode()),
            routing_key=queue_name
        )
```

## Performance Optimization

### Sampling Strategies

1. **Fixed Rate Sampling**: Simple, predictable sampling
2. **Adaptive Sampling**: Adjusts based on system load
3. **Probability Sampling**: Random sampling with fixed probability
4. **Rule-based Sampling**: Sample based on specific conditions

### Batch Processing

Configure batch processing for better performance:

```python
# In configuration
tracing:
  processing:
    batch:
      enabled: true
      timeout: 5s
      max_queue_size: 2048
      max_export_batch_size: 512
```

### Memory Management

Monitor and manage memory usage:

```python
# In configuration
tracing:
  performance:
    memory:
      max_spans_in_memory: 10000
      cleanup_interval: 30s
```

## Security Considerations

### Data Privacy

- Never include sensitive data in spans
- Use privacy filtering for all attributes
- Configure appropriate sampling rates

### Access Control

- Secure trace data access
- Implement authentication for trace queries
- Use appropriate network security measures

### Compliance

- Ensure compliance with data protection regulations
- Implement data retention policies
- Audit trace data access

## Conclusion

This distributed tracing implementation provides comprehensive observability for the EAI-MCP platform. By following this guide, you can effectively monitor, debug, and optimize your distributed system performance.

For additional information or support, please refer to the individual component documentation or contact the observability team.