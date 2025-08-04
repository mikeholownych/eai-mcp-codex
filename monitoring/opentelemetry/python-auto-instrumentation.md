# OpenTelemetry Auto-Instrumentation for Python Services

This document provides a comprehensive guide for implementing OpenTelemetry auto-instrumentation for Python services in the MCP system.

---

## 1. Overview

### 1.1 Supported Python Frameworks

The MCP system uses several Python frameworks that can be auto-instrumented with OpenTelemetry:

- **FastAPI** - Modern web framework for building APIs
- **SQLAlchemy** - SQL toolkit and Object-Relational Mapping (ORM)
- **Redis** - In-memory data structure store
- **Requests** - HTTP library for Python
- **HTTPX** - HTTP client for Python
- **Celery** - Distributed task queue
- **Flask** - Web framework (if used)
- **Django** - Web framework (if used)

### 1.2 Auto-Instrumentation Benefits

- **Zero-code instrumentation**: Automatic tracing of supported libraries
- **Consistent tracing**: Standardized span naming and attributes
- **Performance monitoring**: Built-in metrics for instrumented operations
- **Error tracking**: Automatic error reporting and status codes
- **Context propagation**: Automatic trace context propagation across services

---

## 2. Installation and Setup

### 2.1 Core Dependencies

```python
# requirements.txt - OpenTelemetry dependencies
opentelemetry-distro==0.43b0
opentelemetry-instrumentation==0.43b0
opentelemetry-sdk==1.21.0
opentelemetry-api==1.21.0
opentelemetry-exporter-otlp==1.21.0
opentelemetry-exporter-otlp-proto-grpc==1.21.0
opentelemetry-exporter-otlp-proto-http==1.21.0
opentelemetry-instrumentation-requests==0.43b0
opentelemetry-instrumentation-sqlalchemy==0.43b0
opentelemetry-instrumentation-redis==0.43b0
opentelemetry-instrumentation-fastapi==0.43b0
opentelemetry-instrumentation-httpx==0.43b0
opentelemetry-instrumentation-celery==0.43b0
opentelemetry-instrumentation-logging==0.43b0
opentelemetry-instrumentation-system-metrics==0.43b0
opentelemetry-instrumentation-pymysql==0.43b0
opentelemetry-instrumentation-psycopg2==0.43b0
opentelemetry-instrumentation-pymongo==0.43b0
opentelemetry-instrumentation-aiopg==0.43b0
opentelemetry-instrumentation-asyncpg==0.43b0
opentelemetry-instrumentation-tornado==0.43b0
opentelemetry-instrumentation-aiohttp-client==0.43b0
opentelemetry-instrumentation-botocore==0.43b0
opentelemetry-instrumentation-boto3sqs==0.43b0
opentelemetry-instrumentation-confluent-kafka==0.43b0
opentelemetry-instrumentation-pika==0.43b0
opentelemetry-instrumentation-elasticsearch==0.43b0
opentelemetry-instrumentation-pymemcache==0.43b0
opentelemetry-instrumentation-pyramid==0.43b0
opentelemetry-instrumentation-django==0.43b0
opentelemetry-instrumentation-flask==0.43b0
opentelemetry-instrumentation-starlette==0.43b0
opentelemetry-instrumentation-urllib3==0.43b0
opentelemetry-instrumentation-urllib==0.43b0
opentelemetry-instrumentation-wsgi==0.43b0
opentelemetry-instrumentation-grpc==0.43b0
```

### 2.2 Dockerfile Configuration

```dockerfile
# Dockerfile for Python services with OpenTelemetry auto-instrumentation
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create logs directory
RUN mkdir -p /app/logs

# Set environment variables for OpenTelemetry
ENV OTEL_PYTHON_LOG_CORRELATION=true
ENV OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED=true
ENV OTEL_PYTHON_DISABLED_INSTRUMENTATIONS=""
ENV OTEL_RESOURCE_ATTRIBUTES=service.name=${SERVICE_NAME},service.version=${SERVICE_VERSION},service.namespace=mcp-system,deployment.environment=${ENVIRONMENT}
ENV OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector-gateway:4317
ENV OTEL_EXPORTER_OTLP_PROTOCOL=grpc
ENV OTEL_EXPORTER_OTLP_INSECURE=true
ENV OTEL_TRACES_SAMPLER=parentbased_traceidratio
ENV OTEL_TRACES_SAMPLER_ARG=0.1
ENV OTEL_METRICS_EXPORTER=otlp
ENV OTEL_LOGS_EXPORTER=otlp
ENV OTEL_PYTHON_EXCLUDED_URLS="localhost,127.0.0.1"
ENV OTEL_PROPAGATORS=tracecontext,baggage
ENV OTEL_SERVICE_NAME=${SERVICE_NAME}

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Auto-instrument the application
CMD ["opentelemetry-instrument", "python", "app.py"]
```

### 2.3 Environment Variables Configuration

```yaml
# environment-variables.yaml
environment:
  # OpenTelemetry Configuration
  OTEL_SERVICE_NAME: "model-router"
  OTEL_SERVICE_VERSION: "1.0.0"
  OTEL_RESOURCE_ATTRIBUTES: "service.namespace=mcp-system,deployment.environment=production,service.instance.id=${HOSTNAME}"
  OTEL_EXPORTER_OTLP_ENDPOINT: "http://otel-collector-gateway:4317"
  OTEL_EXPORTER_OTLP_PROTOCOL: "grpc"
  OTEL_EXPORTER_OTLP_INSECURE: "true"
  OTEL_EXPORTER_OTLP_TIMEOUT: "30s"
  OTEL_EXPORTER_OTLP_COMPRESSION: "gzip"
  
  # Tracing Configuration
  OTEL_TRACES_SAMPLER: "parentbased_traceidratio"
  OTEL_TRACES_SAMPLER_ARG: "0.1"
  OTEL_TRACES_EXPORTER: "otlp"
  OTEL_PROPAGATORS: "tracecontext,baggage"
  OTEL_IMR_EXPORT_INTERVAL: "5000"
  OTEL_IMR_MAX_EXPORT_BATCH_SIZE: "512"
  
  # Metrics Configuration
  OTEL_METRICS_EXPORTER: "otlp"
  OTEL_METRICS_EXPORT_INTERVAL: "30000"
  OTEL_METRICS_EXPORT_TIMEOUT: "30000"
  
  # Logs Configuration
  OTEL_LOGS_EXPORTER: "otlp"
  OTEL_PYTHON_LOG_CORRELATION: "true"
  OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED: "true"
  OTEL_PYTHON_LOG_LEVEL: "INFO"
  
  # Instrumentation Configuration
  OTEL_PYTHON_DISABLED_INSTRUMENTATIONS: ""
  OTEL_PYTHON_EXCLUDED_URLS: "localhost,127.0.0.1"
  OTEL_PYTHON_INSTRUMENTATION_HTTP_CAPTURE_HEADERS_SERVER_REQUEST: "content-type,authorization,x-request-id"
  OTEL_PYTHON_INSTRUMENTATION_HTTP_CAPTURE_HEADERS_SERVER_RESPONSE: "content-type,content-length"
  OTEL_PYTHON_INSTRUMENTATION_HTTP_CAPTURE_HEADERS_CLIENT_REQUEST: "content-type,authorization"
  OTEL_PYTHON_INSTRUMENTATION_HTTP_CAPTURE_HEADERS_CLIENT_RESPONSE: "content-type,content-length"
  
  # Resource Detection
  OTEL_RESOURCE_DETECTORS: "env,host,os,process"
  OTEL_NODE_RESOURCE_DETECTORS: "env,host,os"
  
  # Batch Processing Configuration
  OTEL_BSP_SCHEDULE_DELAY: "5000"
  OTEL_BSP_EXPORT_TIMEOUT: "30000"
  OTEL_BSP_MAX_EXPORT_BATCH_SIZE: "512"
  OTEL_BSP_MAX_QUEUE_SIZE: "2048"
  
  # Experimental Features
  OTEL_EXPERIMENTAL_RESOURCE_DETECTORS: "container"
```

---

## 3. Application Integration

### 3.1 FastAPI Application Example

```python
# app.py - FastAPI application with OpenTelemetry
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import structlog
import logging
from contextlib import asynccontextmanager

# Configure structured logging with OpenTelemetry correlation
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    logger.info("Starting Model Router service")
    yield
    logger.info("Shutting down Model Router service")

# Create FastAPI application
app = FastAPI(
    title="MCP Model Router Service",
    description="Service for routing requests to appropriate AI models",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests with OpenTelemetry correlation"""
    start_time = time.time()
    
    # Log request details
    logger.info(
        "Incoming request",
        method=request.method,
        url=str(request.url),
        client_host=request.client.host,
        user_agent=request.headers.get("user-agent"),
    )
    
    response = await call_next(request)
    
    # Log response details
    process_time = time.time() - start_time
    logger.info(
        "Request processed",
        method=request.method,
        url=str(request.url),
        status_code=response.status_code,
        process_time=process_time,
    )
    
    return response

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "model-router"}

# Model routing endpoint
@app.post("/route")
async def route_model(request: Request):
    """Route request to appropriate model"""
    try:
        # Parse request body
        body = await request.json()
        model_type = body.get("model_type")
        prompt = body.get("prompt")
        
        if not model_type or not prompt:
            raise HTTPException(status_code=400, detail="model_type and prompt are required")
        
        logger.info(
            "Routing model request",
            model_type=model_type,
            prompt_length=len(prompt),
        )
        
        # Route to appropriate model (mock implementation)
        result = await route_to_model(model_type, prompt)
        
        logger.info(
            "Model routing completed",
            model_type=model_type,
            response_length=len(result.get("response", "")),
            tokens_used=result.get("tokens_used", 0),
        )
        
        return result
        
    except Exception as e:
        logger.error(
            "Model routing failed",
            error=str(e),
            error_type=type(e).__name__,
        )
        raise HTTPException(status_code=500, detail=str(e))

async def route_to_model(model_type: str, prompt: str) -> dict:
    """Route request to appropriate model"""
    # Mock implementation - replace with actual model routing logic
    await asyncio.sleep(0.1)  # Simulate processing time
    
    return {
        "model_type": model_type,
        "response": f"Mock response for {model_type} model",
        "tokens_used": 100,
        "processing_time_ms": 100,
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### 3.2 SQLAlchemy Integration Example

```python
# database.py - SQLAlchemy with OpenTelemetry
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
import structlog

logger = structlog.get_logger(__name__)

Base = declarative_base()

class ModelRequest(Base):
    """Database model for tracking model requests"""
    __tablename__ = "model_requests"
    
    id = Column(Integer, primary_key=True)
    model_type = Column(String(50), nullable=False)
    prompt = Column(Text, nullable=False)
    response = Column(Text)
    tokens_used = Column(Integer, default=0)
    processing_time_ms = Column(Integer, default=0)
    status = Column(String(20), default="pending")
    created_at = Column(DateTime, server_default="now()")
    updated_at = Column(DateTime, server_default="now()", onupdate="now")

class DatabaseManager:
    """Database manager with OpenTelemetry instrumentation"""
    
    def __init__(self, database_url: str):
        self.engine = create_engine(
            database_url,
            poolclass=QueuePool,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
            pool_recycle=3600,
        )
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        logger.info("Database manager initialized", database_url=database_url)
    
    def create_tables(self):
        """Create database tables"""
        Base.metadata.create_all(bind=self.engine)
        logger.info("Database tables created")
    
    def get_session(self):
        """Get database session"""
        return self.SessionLocal()
    
    def save_model_request(self, model_type: str, prompt: str, response: str = None, 
                          tokens_used: int = 0, processing_time_ms: int = 0, 
                          status: str = "pending") -> ModelRequest:
        """Save model request to database"""
        session = self.get_session()
        try:
            model_request = ModelRequest(
                model_type=model_type,
                prompt=prompt,
                response=response,
                tokens_used=tokens_used,
                processing_time_ms=processing_time_ms,
                status=status,
            )
            
            session.add(model_request)
            session.commit()
            session.refresh(model_request)
            
            logger.info(
                "Model request saved to database",
                request_id=model_request.id,
                model_type=model_type,
                status=status,
            )
            
            return model_request
            
        except Exception as e:
            session.rollback()
            logger.error(
                "Failed to save model request to database",
                error=str(e),
                error_type=type(e).__name__,
            )
            raise
        finally:
            session.close()
    
    def get_model_request(self, request_id: int) -> ModelRequest:
        """Get model request by ID"""
        session = self.get_session()
        try:
            model_request = session.query(ModelRequest).filter(ModelRequest.id == request_id).first()
            
            if model_request:
                logger.info(
                    "Model request retrieved from database",
                    request_id=request_id,
                    model_type=model_request.model_type,
                    status=model_request.status,
                )
            else:
                logger.warning(
                    "Model request not found in database",
                    request_id=request_id,
                )
            
            return model_request
            
        except Exception as e:
            logger.error(
                "Failed to get model request from database",
                request_id=request_id,
                error=str(e),
                error_type=type(e).__name__,
            )
            raise
        finally:
            session.close()
```

### 3.3 Redis Integration Example

```python
# redis_client.py - Redis with OpenTelemetry
import redis
import json
import structlog
from typing import Optional, Any

logger = structlog.get_logger(__name__)

class RedisManager:
    """Redis manager with OpenTelemetry instrumentation"""
    
    def __init__(self, host: str, port: int, db: int = 0, password: str = None):
        self.client = redis.Redis(
            host=host,
            port=port,
            db=db,
            password=password,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True,
        )
        
        logger.info(
            "Redis manager initialized",
            host=host,
            port=port,
            db=db,
        )
    
    def ping(self) -> bool:
        """Ping Redis server"""
        try:
            result = self.client.ping()
            logger.info("Redis ping successful", result=result)
            return result
        except Exception as e:
            logger.error(
                "Redis ping failed",
                error=str(e),
                error_type=type(e).__name__,
            )
            return False
    
    def set_cache(self, key: str, value: Any, expiration: int = 3600) -> bool:
        """Set value in cache with expiration"""
        try:
            serialized_value = json.dumps(value)
            result = self.client.setex(key, expiration, serialized_value)
            
            logger.info(
                "Cache value set",
                key=key,
                expiration=expiration,
                success=result,
            )
            
            return result
            
        except Exception as e:
            logger.error(
                "Failed to set cache value",
                key=key,
                error=str(e),
                error_type=type(e).__name__,
            )
            return False
    
    def get_cache(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            serialized_value = self.client.get(key)
            
            if serialized_value:
                value = json.loads(serialized_value)
                logger.info(
                    "Cache value retrieved",
                    key=key,
                    found=True,
                )
                return value
            else:
                logger.info(
                    "Cache value not found",
                    key=key,
                    found=False,
                )
                return None
                
        except Exception as e:
            logger.error(
                "Failed to get cache value",
                key=key,
                error=str(e),
                error_type=type(e).__name__,
            )
            return None
    
    def delete_cache(self, key: str) -> bool:
        """Delete value from cache"""
        try:
            result = self.client.delete(key)
            
            logger.info(
                "Cache value deleted",
                key=key,
                success=result,
            )
            
            return result
            
        except Exception as e:
            logger.error(
                "Failed to delete cache value",
                key=key,
                error=str(e),
                error_type=type(e).__name__,
            )
            return False
    
    def increment_counter(self, key: str, amount: int = 1) -> int:
        """Increment counter"""
        try:
            result = self.client.incr(key, amount)
            
            logger.info(
                "Counter incremented",
                key=key,
                amount=amount,
                result=result,
            )
            
            return result
            
        except Exception as e:
            logger.error(
                "Failed to increment counter",
                key=key,
                amount=amount,
                error=str(e),
                error_type=type(e).__name__,
            )
            return 0
```

---

## 4. Custom Instrumentation

### 4.1 Custom Tracing for Business Logic

```python
# custom_tracing.py - Custom OpenTelemetry instrumentation
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode
from opentelemetry.context import attach, detach
from typing import Dict, Any, Optional, List
import structlog

logger = structlog.get_logger(__name__)

class ModelRouterTracer:
    """Custom tracer for model router operations"""
    
    def __init__(self):
        self.tracer = trace.get_tracer(__name__)
    
    def trace_model_inference(self, model_type: str, prompt: str, 
                             inference_func: callable) -> Dict[str, Any]:
        """Trace model inference operation"""
        with self.tracer.start_as_current_span(
            "model_inference",
            attributes={
                "mcp.model_type": model_type,
                "mcp.prompt_length": len(prompt),
                "mcp.operation": "model_inference",
                "mcp.service": "model-router",
            }
        ) as span:
            try:
                # Set span attributes
                span.set_attribute("mcp.model_type", model_type)
                span.set_attribute("mcp.prompt_length", len(prompt))
                
                # Execute model inference
                result = inference_func(model_type, prompt)
                
                # Set success attributes
                span.set_attribute("mcp.inference_success", True)
                span.set_attribute("mcp.response_length", len(result.get("response", "")))
                span.set_attribute("mcp.tokens_used", result.get("tokens_used", 0))
                span.set_attribute("mcp.processing_time_ms", result.get("processing_time_ms", 0))
                
                # Add events
                span.add_event("Model inference completed", {
                    "mcp.tokens_used": result.get("tokens_used", 0),
                    "mcp.processing_time_ms": result.get("processing_time_ms", 0),
                })
                
                logger.info(
                    "Model inference completed",
                    model_type=model_type,
                    tokens_used=result.get("tokens_used", 0),
                    processing_time_ms=result.get("processing_time_ms", 0),
                )
                
                return result
                
            except Exception as e:
                # Set error status
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.set_attribute("mcp.inference_success", False)
                span.set_attribute("mcp.error_type", type(e).__name__)
                
                # Record exception
                span.record_exception(e)
                
                # Add error event
                span.add_event("Model inference failed", {
                    "mcp.error": str(e),
                    "mcp.error_type": type(e).__name__,
                })
                
                logger.error(
                    "Model inference failed",
                    model_type=model_type,
                    error=str(e),
                    error_type=type(e).__name__,
                )
                
                raise
    
    def trace_model_selection(self, available_models: List[str], 
                            selection_func: callable) -> str:
        """Trace model selection operation"""
        with self.tracer.start_as_current_span(
            "model_selection",
            attributes={
                "mcp.available_models": len(available_models),
                "mcp.operation": "model_selection",
                "mcp.service": "model-router",
            }
        ) as span:
            try:
                # Execute model selection
                selected_model = selection_func(available_models)
                
                # Set attributes
                span.set_attribute("mcp.selected_model", selected_model)
                span.set_attribute("mcp.selection_success", True)
                
                logger.info(
                    "Model selection completed",
                    selected_model=selected_model,
                    available_count=len(available_models),
                )
                
                return selected_model
                
            except Exception as e:
                # Set error status
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.set_attribute("mcp.selection_success", False)
                span.set_attribute("mcp.error_type", type(e).__name__)
                
                # Record exception
                span.record_exception(e)
                
                logger.error(
                    "Model selection failed",
                    error=str(e),
                    error_type=type(e).__name__,
                )
                
                raise

class WorkflowTracer:
    """Custom tracer for workflow operations"""
    
    def __init__(self):
        self.tracer = trace.get_tracer(__name__)
    
    def trace_workflow_execution(self, workflow_id: str, workflow_type: str, 
                               steps: List[str], execution_func: callable) -> Dict[str, Any]:
        """Trace workflow execution"""
        with self.tracer.start_as_current_span(
            "workflow_execution",
            attributes={
                "mcp.workflow_id": workflow_id,
                "mcp.workflow_type": workflow_type,
                "mcp.workflow_steps": len(steps),
                "mcp.operation": "workflow_execution",
                "mcp.service": "workflow-orchestrator",
            }
        ) as workflow_span:
            try:
                # Execute workflow
                result = execution_func(workflow_id, workflow_type, steps)
                
                # Set attributes
                workflow_span.set_attribute("mcp.workflow_success", True)
                workflow_span.set_attribute("mcp.workflow_duration_ms", result.get("duration_ms", 0))
                workflow_span.set_attribute("mcp.completed_steps", result.get("completed_steps", 0))
                
                logger.info(
                    "Workflow execution completed",
                    workflow_id=workflow_id,
                    workflow_type=workflow_type,
                    duration_ms=result.get("duration_ms", 0),
                    completed_steps=result.get("completed_steps", 0),
                )
                
                return result
                
            except Exception as e:
                # Set error status
                workflow_span.set_status(Status(StatusCode.ERROR, str(e)))
                workflow_span.set_attribute("mcp.workflow_success", False)
                workflow_span.set_attribute("mcp.error_type", type(e).__name__)
                
                # Record exception
                workflow_span.record_exception(e)
                
                logger.error(
                    "Workflow execution failed",
                    workflow_id=workflow_id,
                    workflow_type=workflow_type,
                    error=str(e),
                    error_type=type(e).__name__,
                )
                
                raise
    
    def trace_workflow_step(self, workflow_id: str, step_name: str, 
                           step_func: callable, *args, **kwargs) -> Any:
        """Trace individual workflow step"""
        with self.tracer.start_as_current_span(
            f"workflow_step_{step_name}",
            attributes={
                "mcp.workflow_id": workflow_id,
                "mcp.step_name": step_name,
                "mcp.operation": "workflow_step",
                "mcp.service": "workflow-orchestrator",
            }
        ) as step_span:
            try:
                # Execute step
                result = step_func(*args, **kwargs)
                
                # Set attributes
                step_span.set_attribute("mcp.step_success", True)
                step_span.set_attribute("mcp.step_duration_ms", getattr(result, 'duration_ms', 0))
                
                logger.info(
                    "Workflow step completed",
                    workflow_id=workflow_id,
                    step_name=step_name,
                    duration_ms=getattr(result, 'duration_ms', 0),
                )
                
                return result
                
            except Exception as e:
                # Set error status
                step_span.set_status(Status(StatusCode.ERROR, str(e)))
                step_span.set_attribute("mcp.step_success", False)
                step_span.set_attribute("mcp.error_type", type(e).__name__)
                
                # Record exception
                step_span.record_exception(e)
                
                logger.error(
                    "Workflow step failed",
                    workflow_id=workflow_id,
                    step_name=step_name,
                    error=str(e),
                    error_type=type(e).__name__,
                )
                
                raise
```

### 4.2 Custom Metrics

```python
# custom_metrics.py - Custom OpenTelemetry metrics
from opentelemetry import metrics
from opentelemetry.metrics import Counter, Histogram, Gauge, UpDownCounter
from typing import Dict, Any
import structlog

logger = structlog.get_logger(__name__)

class ModelRouterMetrics:
    """Custom metrics for model router operations"""
    
    def __init__(self):
        self.meter = metrics.get_meter(__name__)
        
        # Define metrics
        self.model_inference_counter = self.meter.create_counter(
            "mcp_model_inference_total",
            description="Total number of model inference requests",
        )
        
        self.model_inference_duration = self.meter.create_histogram(
            "mcp_model_inference_duration_seconds",
            description="Model inference duration in seconds",
        )
        
        self.model_token_usage = self.meter.create_counter(
            "mcp_model_token_usage_total",
            description="Total number of tokens used by models",
        )
        
        self.model_error_counter = self.meter.create_counter(
            "mcp_model_inference_errors_total",
            description="Total number of model inference errors",
        )
        
        self.active_inferences = self.meter.create_up_down_counter(
            "mcp_active_inferences",
            description="Number of active model inferences",
        )
        
        self.model_cache_hits = self.meter.create_counter(
            "mcp_model_cache_hits_total",
            description="Total number of model cache hits",
        )
        
        self.model_cache_misses = self.meter.create_counter(
            "mcp_model_cache_misses_total",
            description="Total number of model cache misses",
        )
    
    def record_inference_start(self, model_type: str):
        """Record start of model inference"""
        self.active_inferences.add(1, {
            "mcp.model_type": model_type,
            "mcp.service": "model-router",
        })
    
    def record_inference_complete(self, model_type: str, duration: float, 
                               tokens_used: int, cache_hit: bool = False):
        """Record completion of model inference"""
        self.model_inference_counter.add(1, {
            "mcp.model_type": model_type,
            "mcp.service": "model-router",
        })
        
        self.model_inference_duration.record(duration, {
            "mcp.model_type": model_type,
            "mcp.service": "model-router",
        })
        
        self.model_token_usage.add(tokens_used, {
            "mcp.model_type": model_type,
            "mcp.service": "model-router",
        })
        
        self.active_inferences.add(-1, {
            "mcp.model_type": model_type,
            "mcp.service": "model-router",
        })
        
        if cache_hit:
            self.model_cache_hits.add(1, {
                "mcp.model_type": model_type,
                "mcp.service": "model-router",
            })
        else:
            self.model_cache_misses.add(1, {
                "mcp.model_type": model_type,
                "mcp.service": "model-router",
            })
    
    def record_inference_error(self, model_type: str, error_type: str):
        """Record model inference error"""
        self.model_error_counter.add(1, {
            "mcp.model_type": model_type,
            "mcp.error_type": error_type,
            "mcp.service": "model-router",
        })

class WorkflowMetrics:
    """Custom metrics for workflow operations"""
    
    def __init__(self):
        self.meter = metrics.get_meter(__name__)
        
        # Define metrics
        self.workflow_execution_counter = self.meter.create_counter(
            "mcp_workflow_execution_total",
            description="Total number of workflow executions",
        )
        
        self.workflow_duration = self.meter.create_histogram(
            "mcp_workflow_execution_duration_seconds",
            description="Workflow execution duration in seconds",
        )
        
        self.workflow_step_counter = self.meter.create_counter(
            "mcp_workflow_step_total",
            description="Total number of workflow steps executed",
        )
        
        self.workflow_error_counter = self.meter.create_counter(
            "mcp_workflow_errors_total",
            description="Total number of workflow errors",
        )
        
        self.active_workflows = self.meter.create_up_down_counter(
            "mcp_active_workflows",
            description="Number of active workflows",
        )
    
    def record_workflow_start(self, workflow_type: str):
        """Record start of workflow execution"""
        self.active_workflows.add(1, {
            "mcp.workflow_type": workflow_type,
            "mcp.service": "workflow-orchestrator",
        })
    
    def record_workflow_complete(self, workflow_type: str, duration: float, 
                              steps_completed: int):
        """Record completion of workflow execution"""
        self.workflow_execution_counter.add(1, {
            "mcp.workflow_type": workflow_type,
            "mcp.service": "workflow-orchestrator",
        })
        
        self.workflow_duration.record(duration, {
            "mcp.workflow_type": workflow_type,
            "mcp.service": "workflow-orchestrator",
        })
        
        self.workflow_step_counter.add(steps_completed, {
            "mcp.workflow_type": workflow_type,
            "mcp.service": "workflow-orchestrator",
        })
        
        self.active_workflows.add(-1, {
            "mcp.workflow_type": workflow_type,
            "mcp.service": "workflow-orchestrator",
        })
    
    def record_workflow_error(self, workflow_type: str, error_type: str):
        """Record workflow error"""
        self.workflow_error_counter.add(1, {
            "mcp.workflow_type": workflow_type,
            "mcp.error_type": error_type,
            "mcp.service": "workflow-orchestrator",
        })
```

---

## 5. Kubernetes Deployment

### 5.1 Deployment Manifest

```yaml
# model-router-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: model-router
  namespace: mcp-system
  labels:
    app: model-router
    component: mcp-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: model-router
  template:
    metadata:
      labels:
        app: model-router
        component: mcp-service
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8000"
        prometheus.io/path: "/metrics"
        # OpenTelemetry injection annotation
        instrumentation.opentelemetry.io/inject-python: "true"
    spec:
      containers:
      - name: model-router
        image: mcp-system/model-router:1.0.0
        ports:
        - containerPort: 8000
          name: http
          protocol: TCP
        env:
        - name: SERVICE_NAME
          value: "model-router"
        - name: SERVICE_VERSION
          value: "1.0.0"
        - name: ENVIRONMENT
          value: "production"
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: database-secret
              key: url
        - name: REDIS_HOST
          value: "redis"
        - name: REDIS_PORT
          value: "6379"
        - name: REDIS_PASSWORD
          valueFrom:
            secretKeyRef:
              name: redis-secret
              key: password
        # OpenTelemetry environment variables
        - name: OTEL_SERVICE_NAME
          value: "model-router"
        - name: OTEL_SERVICE_VERSION
          value: "1.0.0"
        - name: OTEL_RESOURCE_ATTRIBUTES
          value: "service.namespace=mcp-system,deployment.environment=production,service.instance.id=$(HOSTNAME)"
        - name: OTEL_EXPORTER_OTLP_ENDPOINT
          value: "http://otel-collector-gateway:4317"
        - name: OTEL_EXPORTER_OTLP_PROTOCOL
          value: "grpc"
        - name: OTEL_EXPORTER_OTLP_INSECURE
          value: "true"
        - name: OTEL_TRACES_SAMPLER
          value: "parentbased_traceidratio"
        - name: OTEL_TRACES_SAMPLER_ARG
          value: "0.1"
        - name: OTEL_PYTHON_LOG_CORRELATION
          value: "true"
        - name: OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED
          value: "true"
        - name: OTEL_PYTHON_DISABLED_INSTRUMENTATIONS
          value: ""
        - name: OTEL_PYTHON_EXCLUDED_URLS
          value: "localhost,127.0.0.1"
        - name: OTEL_PROPAGATORS
          value: "tracecontext,baggage"
        resources:
          limits:
            cpu: "500m"
            memory: "512Mi"
          requests:
            cpu: "100m"
            memory: "128Mi"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 10
        volumeMounts:
        - name: logs
          mountPath: /app/logs
      volumes:
      - name: logs
        emptyDir: {}
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
                  - model-router
              topologyKey: "kubernetes.io/hostname"
```

### 5.2 Service Manifest

```yaml
# model-router-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: model-router
  namespace: mcp-system
  labels:
    app: model-router
    component: mcp-service
  annotations:
    prometheus.io/scrape: "true"
    prometheus.io/port: "8000"
    prometheus.io/path: "/metrics"
spec:
  type: ClusterIP
  ports:
  - name: http
    port: 8000
    targetPort: 8000
    protocol: TCP
  selector:
    app: model-router
```

---

## 6. Testing and Validation

### 6.1 Instrumentation Testing

```python
# test_instrumentation.py - Test OpenTelemetry instrumentation
import pytest
import requests
import time
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, ConsoleSpanExporter

# Set up tracer for testing
trace.set_tracer_provider(TracerProvider())
trace.get_tracer_provider().add_span_processor(
    SimpleSpanProcessor(ConsoleSpanExporter())
)

def test_model_router_tracing():
    """Test that model router operations are properly traced"""
    tracer = trace.get_tracer(__name__)
    
    with tracer.start_as_current_span("test_model_router") as span:
        # Simulate model router operation
        time.sleep(0.1)
        
        # Add attributes
        span.set_attribute("test.model_type", "gpt-3.5")
        span.set_attribute("test.prompt_length", 100)
        
        # Add event
        span.add_event("Model inference started")
        
        # Simulate processing
        time.sleep(0.2)
        
        # Add completion event
        span.add_event("Model inference completed")
        
        # Set success status
        span.set_status(trace.Status(trace.StatusCode.OK))

def test_workflow_tracing():
    """Test that workflow operations are properly traced"""
    tracer = trace.get_tracer(__name__)
    
    with tracer.start_as_current_span("test_workflow") as workflow_span:
        # Simulate workflow execution
        time.sleep(0.1)
        
        # Add attributes
        workflow_span.set_attribute("test.workflow_type", "content_processing")
        workflow_span.set_attribute("test.steps", 3)
        
        # Execute workflow steps
        for i in range(3):
            with tracer.start_as_current_span(f"step_{i}", parent=workflow_span.context) as step_span:
                time.sleep(0.05)
                step_span.set_attribute("test.step_number", i)
                step_span.add_event(f"Step {i} completed")
        
        # Set success status
        workflow_span.set_status(trace.Status(trace.StatusCode.OK))

def test_error_tracing():
    """Test that errors are properly traced"""
    tracer = trace.get_tracer(__name__)
    
    with tracer.start_as_current_span("test_error") as span:
        try:
            # Simulate error
            raise ValueError("Test error")
        except Exception as e:
            # Record exception
            span.record_exception(e)
            
            # Set error status
            span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
            
            # Add error attributes
            span.set_attribute("test.error_type", type(e).__name__)

def test_metrics_collection():
    """Test that metrics are properly collected"""
    from opentelemetry import metrics
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.metrics.export import ConsoleMetricExporter, PeriodicExportingMetricReader
    
    # Set up meter for testing
    metrics.set_meter_provider(MeterProvider())
    meter = metrics.get_meter(__name__)
    
    # Create test metrics
    counter = meter.create_counter("test_counter")
    histogram = meter.create_histogram("test_histogram")
    
    # Record metrics
    counter.add(1, {"test.attribute": "value"})
    histogram.record(1.5, {"test.attribute": "value"})
    
    # Allow time for metrics to be exported
    time.sleep(1)

if __name__ == "__main__":
    print("Running instrumentation tests...")
    
    test_model_router_tracing()
    print("✓ Model router tracing test completed")
    
    test_workflow_tracing()
    print("✓ Workflow tracing test completed")
    
    test_error_tracing()
    print("✓ Error tracing test completed")
    
    test_metrics_collection()
    print("✓ Metrics collection test completed")
    
    print("All instrumentation tests completed successfully!")
```

### 6.2 Integration Testing

```python
# test_integration.py - Integration tests for OpenTelemetry
import pytest
import requests
import json
import time
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, ConsoleSpanExporter

# Set up tracer for testing
trace.set_tracer_provider(TracerProvider())
trace.get_tracer_provider().add_span_processor(
    SimpleSpanProcessor(ConsoleSpanExporter())
)

class TestModelRouterIntegration:
    """Integration tests for model router with OpenTelemetry"""
    
    def test_health_endpoint(self):
        """Test health endpoint with tracing"""
        tracer = trace.get_tracer(__name__)
        
        with tracer.start_as_current_span("test_health_endpoint") as span:
            response = requests.get("http://localhost:8000/health")
            
            assert response.status_code == 200
            assert response.json()["status"] == "healthy"
            
            span.set_attribute("test.response_status", response.status_code)
            span.set_attribute("test.response_time", response.elapsed.total_seconds())
    
    def test_model_routing_endpoint(self):
        """Test model routing endpoint with tracing"""
        tracer = trace.get_tracer(__name__)
        
        with tracer.start_as_current_span("test_model_routing") as span:
            payload = {
                "model_type": "gpt-3.5",
                "prompt": "What is the capital of France?"
            }
            
            response = requests.post(
                "http://localhost:8000/route",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            assert response.status_code == 200
            result = response.json()
            
            assert "model_type" in result
            assert "response" in result
            assert "tokens_used" in result
            
            span.set_attribute("test.response_status", response.status_code)
            span.set_attribute("test.response_time", response.elapsed.total_seconds())
            span.set_attribute("test.model_type", payload["model_type"])
            span.set_attribute("test.prompt_length", len(payload["prompt"]))
    
    def test_error_handling(self):
        """Test error handling with tracing"""
        tracer = trace.get_tracer(__name__)
        
        with tracer.start_as_current_span("test_error_handling") as span:
            # Test with missing required fields
            payload = {
                "model_type": "gpt-3.5"
                # Missing "prompt" field
            }
            
            try:
                response = requests.post(
                    "http://localhost:8000/route",
                    json=payload,
                    headers={"Content-Type":