# OpenTelemetry Auto-Instrumentation for JavaScript/Node.js Services

This document provides a comprehensive guide for implementing OpenTelemetry auto-instrumentation for JavaScript/Node.js services in the MCP system.

---

## 1. Overview

### 1.1 Supported JavaScript Frameworks

The MCP system uses several JavaScript/Node.js frameworks that can be auto-instrumented with OpenTelemetry:

- **Express.js** - Web application framework
- **Fastify** - Fast and low-overhead web framework
- **Koa** - Next-generation web framework
- **HTTP/HTTPS** - Node.js built-in HTTP modules
- **Axios** - HTTP client for browser and Node.js
- **Redis** - Redis client for Node.js
- **PostgreSQL** - PostgreSQL client
- **MongoDB** - MongoDB client
- **GraphQL** - GraphQL server and client
- **gRPC** - gRPC framework
- **Socket.IO** - Real-time bidirectional event-based communication
- **AWS SDK** - AWS SDK for JavaScript

### 1.2 Auto-Instrumentation Benefits

- **Zero-code instrumentation**: Automatic tracing of supported libraries
- **Consistent tracing**: Standardized span naming and attributes
- **Performance monitoring**: Built-in metrics for instrumented operations
- **Error tracking**: Automatic error reporting and status codes
- **Context propagation**: Automatic trace context propagation across services

---

## 2. Installation and Setup

### 2.1 Core Dependencies

```json
// package.json - OpenTelemetry dependencies
{
  "name": "mcp-frontend",
  "version": "1.0.0",
  "dependencies": {
    "@opentelemetry/api": "^1.7.0",
    "@opentelemetry/sdk-node": "^0.48.0",
    "@opentelemetry/auto-instrumentations-node": "^0.48.0",
    "@opentelemetry/exporter-trace-otlp-grpc": "^0.48.0",
    "@opentelemetry/exporter-trace-otlp-http": "^0.48.0",
    "@opentelemetry/exporter-metrics-otlp-grpc": "^0.48.0",
    "@opentelemetry/exporter-metrics-otlp-http": "^0.48.0",
    "@opentelemetry/exporter-logs-otlp-grpc": "^0.48.0",
    "@opentelemetry/exporter-logs-otlp-http": "^0.48.0",
    "@opentelemetry/instrumentation": "^0.48.0",
    "@opentelemetry/instrumentation-http": "^0.48.0",
    "@opentelemetry/instrumentation-express": "^0.36.0",
    "@opentelemetry/instrumentation-fastify": "^0.35.0",
    "@opentelemetry/instrumentation-koa": "^0.39.0",
    "@opentelemetry/instrumentation-axios": "^0.36.0",
    "@opentelemetry/instrumentation-redis": "^0.39.0",
    "@opentelemetry/instrumentation-pg": "^0.39.0",
    "@opentelemetry/instrumentation-mongodb": "^0.41.0",
    "@opentelemetry/instrumentation-graphql": "^0.39.0",
    "@opentelemetry/instrumentation-grpc": "^0.48.0",
    "@opentelemetry/instrumentation-socket.io": "^0.39.0",
    "@opentelemetry/instrumentation-aws-sdk": "^0.39.0",
    "@opentelemetry/instrumentation-dns": "^0.35.0",
    "@opentelemetry/instrumentation-net": "^0.35.0",
    "@opentelemetry/instrumentation-tls": "^0.35.0",
    "@opentelemetry/instrumentation-child-process": "^0.35.0",
    "@opentelemetry/instrumentation-fs": "^0.35.0",
    "@opentelemetry/resource-detector-container": "^0.3.0",
    "@opentelemetry/resource-detector-alibaba-cloud": "^0.28.0",
    "@opentelemetry/resource-detector-aws": "^1.3.0",
    "@opentelemetry/resource-detector-gcp": "^0.29.0",
    "@opentelemetry/semantic-conventions": "^1.21.0",
    "@opentelemetry/sdk-logs": "^0.48.0",
    "@opentelemetry/sdk-metrics": "^1.21.0",
    "winston": "^3.11.0",
    "pino": "^8.16.0",
    "express": "^4.18.2",
    "fastify": "^4.24.3",
    "axios": "^1.6.0",
    "redis": "^4.6.10",
    "pg": "^8.11.3",
    "mongodb": "^6.3.0",
    "graphql": "^16.8.1",
    "@grpc/grpc-js": "^1.9.0",
    "socket.io": "^4.7.4",
    "aws-sdk": "^2.1490.0"
  },
  "scripts": {
    "start": "node -r ./tracing.js app.js",
    "start:prod": "node -r ./tracing.js app.js",
    "dev": "nodemon -r ./tracing.js app.js"
  }
}
```

### 2.2 Dockerfile Configuration

```dockerfile
# Dockerfile for Node.js services with OpenTelemetry auto-instrumentation
FROM node:18-alpine

# Install system dependencies
RUN apk add --no-cache \
    dumb-init \
    && addgroup -g 1001 -S nodejs \
    && adduser -S nodejs -u 1001

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy application code
COPY . .

# Create logs directory
RUN mkdir -p /app/logs && chown -R nodejs:nodejs /app/logs

# Switch to non-root user
USER nodejs

# Set environment variables for OpenTelemetry
ENV NODE_OPTIONS="--require ./tracing.js"
ENV OTEL_NODE_RESOURCE_DETECTORS="env,host,os,container"
ENV OTEL_SERVICE_NAME="frontend"
ENV OTEL_SERVICE_VERSION="1.0.0"
ENV OTEL_RESOURCE_ATTRIBUTES="service.namespace=mcp-system,deployment.environment=production,service.instance.id=$(HOSTNAME)"
ENV OTEL_EXPORTER_OTLP_ENDPOINT="http://otel-collector-gateway:4317"
ENV OTEL_EXPORTER_OTLP_PROTOCOL="grpc"
ENV OTEL_EXPORTER_OTLP_INSECURE="true"
ENV OTEL_TRACES_SAMPLER="parentbased_traceidratio"
ENV OTEL_TRACES_SAMPLER_ARG="0.1"
ENV OTEL_METRICS_EXPORTER="otlp"
ENV OTEL_LOGS_EXPORTER="otlp"
ENV OTEL_NODE_DISABLED_INSTRUMENTATIONS=""
ENV OTEL_PROPAGATORS="tracecontext,baggage"
ENV OTEL_IMR_EXPORT_INTERVAL="5000"
ENV OTEL_IMR_MAX_EXPORT_BATCH_SIZE="512"
ENV OTEL_BSP_SCHEDULE_DELAY="5000"
ENV OTEL_BSP_EXPORT_TIMEOUT="30000"
ENV OTEL_BSP_MAX_EXPORT_BATCH_SIZE="512"
ENV OTEL_BSP_MAX_QUEUE_SIZE="2048"
ENV OTEL_LOG_LEVEL="INFO"
ENV NODE_ENV="production"

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD node healthcheck.js

# Expose port
EXPOSE 3000

# Start application with dumb-init
ENTRYPOINT ["dumb-init", "--"]
CMD ["node", "app.js"]
```

### 2.3 Tracing Configuration File

```javascript
// tracing.js - OpenTelemetry configuration
const { NodeSDK } = require('@opentelemetry/sdk-node');
const { getNodeAutoInstrumentations } = require('@opentelemetry/auto-instrumentations-node');
const { OTLPTraceExporter } = require('@opentelemetry/exporter-trace-otlp-grpc');
const { OTLPMetricExporter } = require('@opentelemetry/exporter-metrics-otlp-grpc');
const { OTLPLogExporter } = require('@opentelemetry/exporter-logs-otlp-grpc');
const { PeriodicExportingMetricReader } = require('@opentelemetry/sdk-metrics');
const { ConsoleSpanExporter, ConsoleMetricExporter } = require('@opentelemetry/sdk-trace-base');
const { Resource } = require('@opentelemetry/resources');
const { SemanticResourceAttributes } = require('@opentelemetry/semantic-conventions');
const { containerDetector } = require('@opentelemetry/resource-detector-container');
const { envDetector, hostDetector, osDetector, processDetector } = require('@opentelemetry/resources');

// Configure OpenTelemetry SDK
const sdk = new NodeSDK({
  // Resource configuration
  resource: new Resource({
    [SemanticResourceAttributes.SERVICE_NAME]: process.env.OTEL_SERVICE_NAME || 'unknown-service',
    [SemanticResourceAttributes.SERVICE_VERSION]: process.env.OTEL_SERVICE_VERSION || 'unknown-version',
    [SemanticResourceAttributes.SERVICE_NAMESPACE]: process.env.OTEL_RESOURCE_ATTRIBUTES?.match(/service\.namespace=([^,]+)/)?.[1] || 'unknown-namespace',
    [SemanticResourceAttributes.DEPLOYMENT_ENVIRONMENT]: process.env.OTEL_RESOURCE_ATTRIBUTES?.match(/deployment\.environment=([^,]+)/)?.[1] || 'unknown-environment',
    [SemanticResourceAttributes.HOST_NAME]: require('os').hostname(),
  }),
  
  // Auto-instrumentations
  instrumentations: [
    getNodeAutoInstrumentations({
      // Custom configuration for specific instrumentations
      '@opentelemetry/instrumentation-express': {
        enabled: true,
        ignoreLayers: [
          // Ignore specific middleware layers
          (layer) => layer.name === 'middleware',
        ],
      },
      '@opentelemetry/instrumentation-http': {
        enabled: true,
        ignoreIncomingPaths: [
          // Health check endpoints
          '/health',
          '/metrics',
          '/ready',
          '/live',
        ],
        ignoreOutgoingUrls: [
          // Internal services
          'localhost',
          '127.0.0.1',
        ],
        applyCustomAttributesOnSpan: (span, request, response) => {
          // Add custom attributes to HTTP spans
          span.setAttribute('custom.user_agent', request.headers['user-agent']);
          span.setAttribute('custom.request_size', request.headers['content-length']);
          span.setAttribute('custom.response_size', response.headers['content-length']);
        },
      },
      '@opentelemetry/instrumentation-axios': {
        enabled: true,
        ignoreRequestHook: (request) => {
          // Ignore requests to specific URLs
          return request.url.includes('localhost') || request.url.includes('127.0.0.1');
        },
      },
      '@opentelemetry/instrumentation-redis': {
        enabled: true,
        dbStatementSerializer: (cmdName, cmdArgs) => {
          // Serialize Redis commands for better observability
          return `${cmdName} ${cmdArgs.map(arg => 
            typeof arg === 'string' && arg.length > 50 ? arg.substring(0, 50) + '...' : arg
          ).join(' ')}`;
        },
      },
      '@opentelemetry/instrumentation-pg': {
        enabled: true,
        enhancedDatabaseReporting: true,
      },
      '@opentelemetry/instrumentation-mongodb': {
        enabled: true,
        enhancedDatabaseReporting: true,
      },
    }),
  ],
  
  // Trace exporter
  traceExporter: new OTLPTraceExporter({
    url: process.env.OTEL_EXPORTER_OTLP_ENDPOINT || 'http://localhost:4317',
    headers: {},
    concurrencyLimit: 10,
  }),
  
  // Metric exporter
  metricReader: new PeriodicExportingMetricReader({
    exporter: new OTLPMetricExporter({
      url: process.env.OTEL_EXPORTER_OTLP_ENDPOINT || 'http://localhost:4317',
      headers: {},
      concurrencyLimit: 10,
    }),
    exportIntervalMillis: 30000,
  }),
  
  // Log exporter
  logRecordProcessor: new SimpleLogRecordProcessor(new OTLPLogExporter({
    url: process.env.OTEL_EXPORTER_OTLP_ENDPOINT || 'http://localhost:4317',
    headers: {},
    concurrencyLimit: 10,
  })),
  
  // Sampling configuration
  sampler: process.env.OTEL_TRACES_SAMPLER === 'always_on' 
    ? new AlwaysOnSampler()
    : process.env.OTEL_TRACES_SAMPLER === 'always_off'
    ? new AlwaysOffSampler()
    : new ParentBasedSampler({
        root: new TraceIdRatioBasedSampler(parseFloat(process.env.OTEL_TRACES_SAMPLER_ARG) || 0.1),
        remoteParentSampled: new AlwaysOnSampler(),
        remoteParentNotSampled: new AlwaysOffSampler(),
        localParentSampled: new AlwaysOnSampler(),
        localParentNotSampled: new AlwaysOffSampler(),
      }),
  
  // Context manager
  contextManager: process.env.NODE_ENV === 'test' 
    ? new AsyncHooksContextManager() 
    : new AsyncLocalStorageContextManager(),
  
  // Auto-detect resources
  resourceDetectors: [
    containerDetector,
    envDetector,
    hostDetector,
    osDetector,
    processDetector,
  ],
  
  // View configuration for metrics
  views: [
    // Custom views for specific metrics
    new View({
      name: 'http.server.duration',
      description: 'Measures the duration of inbound HTTP requests',
      aggregation: new ExplicitBucketHistogramAggregation([
        0, 5, 10, 25, 50, 75, 100, 250, 500, 750, 1000, 2500, 5000, 7500, 10000
      ]),
      instrumentType: InstrumentType.HISTOGRAM,
    }),
    new View({
      name: 'http.client.duration',
      description: 'Measures the duration of outbound HTTP requests',
      aggregation: new ExplicitBucketHistogramAggregation([
        0, 5, 10, 25, 50, 75, 100, 250, 500, 750, 1000, 2500, 5000, 7500, 10000
      ]),
      instrumentType: InstrumentType.HISTOGRAM,
    }),
  ],
  
  // Disable specific instrumentations if needed
  disabledInstrumentations: process.env.OTEL_NODE_DISABLED_INSTRUMENTATIONS 
    ? process.env.OTEL_NODE_DISABLED_INSTRUMENTATIONS.split(',')
    : [],
});

// Start the SDK
sdk.start()
  .then(() => {
    console.log('OpenTelemetry SDK started successfully');
  })
  .catch((error) => {
    console.error('Error starting OpenTelemetry SDK:', error);
  });

// Graceful shutdown
process.on('SIGTERM', () => {
  sdk.shutdown()
    .then(() => {
      console.log('OpenTelemetry SDK shut down successfully');
      process.exit(0);
    })
    .catch((error) => {
      console.error('Error shutting down OpenTelemetry SDK:', error);
      process.exit(1);
    });
});

process.on('SIGINT', () => {
  sdk.shutdown()
    .then(() => {
      console.log('OpenTelemetry SDK shut down successfully');
      process.exit(0);
    })
    .catch((error) => {
      console.error('Error shutting down OpenTelemetry SDK:', error);
      process.exit(1);
    });
});

// Handle uncaught exceptions
process.on('uncaughtException', (error) => {
  console.error('Uncaught Exception:', error);
  sdk.shutdown()
    .then(() => {
      process.exit(1);
    })
    .catch(() => {
      process.exit(1);
    });
});

process.on('unhandledRejection', (reason, promise) => {
  console.error('Unhandled Rejection at:', promise, 'reason:', reason);
  sdk.shutdown()
    .then(() => {
      process.exit(1);
    })
    .catch(() => {
      process.exit(1);
    });
});
```

---

## 3. Application Integration

### 3.1 Express.js Application Example

```javascript
// app.js - Express.js application with OpenTelemetry
const express = require('express');
const axios = require('axios');
const redis = require('redis');
const { Pool } = require('pg');
const { trace, context, SpanStatusCode } = require('@opentelemetry/api');
const pino = require('pino');
const { default: pinoPretty } = require('pino-pretty');

// Configure logger with OpenTelemetry correlation
const logger = pino({
  level: process.env.LOG_LEVEL || 'info',
  mixin() {
    const span = trace.getSpan(context.active());
    if (span) {
      const spanContext = span.spanContext();
      return {
        trace_id: spanContext.traceId,
        span_id: spanContext.spanId,
        trace_flags: spanContext.traceFlags,
      };
    }
    return {};
  },
}, pinoPretty());

// Initialize Express app
const app = express();
app.use(express.json());

// Initialize Redis client
const redisClient = redis.createClient({
  host: process.env.REDIS_HOST || 'localhost',
  port: process.env.REDIS_PORT || 6379,
  password: process.env.REDIS_PASSWORD,
});

redisClient.on('error', (err) => {
  logger.error('Redis client error', { error: err.message });
});

redisClient.on('connect', () => {
  logger.info('Connected to Redis');
});

// Initialize PostgreSQL pool
const pool = new Pool({
  host: process.env.DB_HOST || 'localhost',
  port: process.env.DB_PORT || 5432,
  database: process.env.DB_NAME || 'mcp',
  user: process.env.DB_USER || 'postgres',
  password: process.env.DB_PASSWORD,
  max: 20,
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 2000,
});

// Request logging middleware
app.use((req, res, next) => {
  const start = Date.now();
  
  logger.info('Incoming request', {
    method: req.method,
    url: req.url,
    userAgent: req.get('User-Agent'),
    ip: req.ip,
  });
  
  res.on('finish', () => {
    const duration = Date.now() - start;
    logger.info('Request completed', {
      method: req.method,
      url: req.url,
      statusCode: res.statusCode,
      duration,
    });
  });
  
  next();
});

// Health check endpoint
app.get('/health', async (req, res) => {
  const tracer = trace.getTracer('health-check');
  
  try {
    const span = tracer.startSpan('health-check');
    
    // Check Redis connection
    await redisClient.ping();
    
    // Check database connection
    await pool.query('SELECT 1');
    
    span.setStatus({ code: SpanStatusCode.OK });
    span.end();
    
    res.json({
      status: 'healthy',
      timestamp: new Date().toISOString(),
      service: process.env.OTEL_SERVICE_NAME || 'frontend',
      version: process.env.OTEL_SERVICE_VERSION || '1.0.0',
    });
  } catch (error) {
    const span = tracer.startSpan('health-check');
    span.setStatus({ code: SpanStatusCode.ERROR, message: error.message });
    span.recordException(error);
    span.end();
    
    logger.error('Health check failed', { error: error.message });
    res.status(500).json({
      status: 'unhealthy',
      error: error.message,
      timestamp: new Date().toISOString(),
    });
  }
});

// Model routing endpoint
app.post('/api/route', async (req, res) => {
  const tracer = trace.getTracer('model-router');
  const span = tracer.startSpan('model-routing', {
    attributes: {
      'mcp.model_type': req.body.model_type,
      'mcp.prompt_length': req.body.prompt?.length || 0,
      'mcp.operation': 'model_routing',
    },
  });
  
  try {
    const { model_type, prompt } = req.body;
    
    if (!model_type || !prompt) {
      span.setStatus({
        code: SpanStatusCode.ERROR,
        message: 'Missing required fields: model_type and prompt',
      });
      span.end();
      return res.status(400).json({
        error: 'Missing required fields: model_type and prompt',
      });
    }
    
    logger.info('Routing model request', { model_type, promptLength: prompt.length });
    
    // Check cache first
    const cacheKey = `model:${model_type}:${prompt.hashCode()}`;
    const cachedResult = await redisClient.get(cacheKey);
    
    if (cachedResult) {
      const result = JSON.parse(cachedResult);
      span.setAttribute('mcp.cache_hit', true);
      span.setAttribute('mcp.response_length', result.response.length);
      span.setAttribute('mcp.tokens_used', result.tokens_used);
      
      logger.info('Model request served from cache', { model_type, tokens_used: result.tokens_used });
      
      span.setStatus({ code: SpanStatusCode.OK });
      span.end();
      
      return res.json(result);
    }
    
    span.setAttribute('mcp.cache_hit', false);
    
    // Route to model service
    const modelResponse = await axios.post('http://model-router:8000/route', {
      model_type,
      prompt,
    }, {
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
        'X-Trace-ID': span.spanContext().traceId,
      },
    });
    
    const result = {
      model_type,
      response: modelResponse.data.response,
      tokens_used: modelResponse.data.tokens_used,
      processing_time_ms: modelResponse.data.processing_time_ms,
      timestamp: new Date().toISOString(),
    };
    
    // Cache the result
    await redisClient.setex(cacheKey, 3600, JSON.stringify(result));
    
    span.setAttribute('mcp.response_length', result.response.length);
    span.setAttribute('mcp.tokens_used', result.tokens_used);
    span.setAttribute('mcp.processing_time_ms', result.processing_time_ms);
    
    logger.info('Model routing completed', {
      model_type,
      tokens_used: result.tokens_used,
      processing_time_ms: result.processing_time_ms,
    });
    
    span.setStatus({ code: SpanStatusCode.OK });
    span.end();
    
    res.json(result);
  } catch (error) {
    span.setStatus({
      code: SpanStatusCode.ERROR,
      message: error.message,
    });
    span.recordException(error);
    span.end();
    
    logger.error('Model routing failed', {
      error: error.message,
      model_type: req.body.model_type,
    });
    
    res.status(500).json({
      error: 'Model routing failed',
      message: error.message,
    });
  }
});

// Workflow execution endpoint
app.post('/api/workflow/execute', async (req, res) => {
  const tracer = trace.getTracer('workflow-executor');
  const span = tracer.startSpan('workflow-execution', {
    attributes: {
      'mcp.workflow_type': req.body.workflow_type,
      'mcp.workflow_steps': req.body.steps?.length || 0,
      'mcp.operation': 'workflow_execution',
    },
  });
  
  try {
    const { workflow_type, steps, input_data } = req.body;
    
    if (!workflow_type || !steps || !Array.isArray(steps)) {
      span.setStatus({
        code: SpanStatusCode.ERROR,
        message: 'Missing required fields: workflow_type and steps',
      });
      span.end();
      return res.status(400).json({
        error: 'Missing required fields: workflow_type and steps',
      });
    }
    
    logger.info('Starting workflow execution', { workflow_type, stepsCount: steps.length });
    
    const results = [];
    let totalDuration = 0;
    
    for (let i = 0; i < steps.length; i++) {
      const step = steps[i];
      const stepSpan = tracer.startSpan(`workflow-step-${step.name}`, {
        parent: span,
        attributes: {
          'mcp.step_name': step.name,
          'mcp.step_type': step.type,
          'mcp.step_index': i,
        },
      });
      
      try {
        const stepStart = Date.now();
        
        // Execute step based on type
        let stepResult;
        switch (step.type) {
          case 'model_inference':
            stepResult = await executeModelInference(step, input_data);
            break;
          case 'data_processing':
            stepResult = await executeDataProcessing(step, input_data);
            break;
          case 'external_api':
            stepResult = await executeExternalApiCall(step, input_data);
            break;
          default:
            throw new Error(`Unknown step type: ${step.type}`);
        }
        
        const stepDuration = Date.now() - stepStart;
        totalDuration += stepDuration;
        
        stepSpan.setAttribute('mcp.step_duration_ms', stepDuration);
        stepSpan.setAttribute('mcp.step_success', true);
        
        results.push({
          step_name: step.name,
          result: stepResult,
          duration_ms: stepDuration,
        });
        
        logger.info('Workflow step completed', {
          step_name: step.name,
          duration_ms: stepDuration,
        });
        
        stepSpan.setStatus({ code: SpanStatusCode.OK });
        stepSpan.end();
        
        // Update input_data for next step
        input_data = { ...input_data, ...stepResult };
      } catch (error) {
        const stepDuration = Date.now() - stepStart;
        totalDuration += stepDuration;
        
        stepSpan.setAttribute('mcp.step_duration_ms', stepDuration);
        stepSpan.setAttribute('mcp.step_success', false);
        stepSpan.setStatus({
          code: SpanStatusCode.ERROR,
          message: error.message,
        });
        stepSpan.recordException(error);
        stepSpan.end();
        
        logger.error('Workflow step failed', {
          step_name: step.name,
          error: error.message,
          duration_ms: stepDuration,
        });
        
        throw error;
      }
    }
    
    span.setAttribute('mcp.workflow_duration_ms', totalDuration);
    span.setAttribute('mcp.completed_steps', results.length);
    span.setAttribute('mcp.workflow_success', true);
    
    logger.info('Workflow execution completed', {
      workflow_type,
      total_duration_ms: totalDuration,
      completed_steps: results.length,
    });
    
    span.setStatus({ code: SpanStatusCode.OK });
    span.end();
    
    res.json({
      workflow_type,
      results,
      total_duration_ms: totalDuration,
      completed_steps: results.length,
      timestamp: new Date().toISOString(),
    });
  } catch (error) {
    span.setAttribute('mcp.workflow_success', false);
    span.setStatus({
      code: SpanStatusCode.ERROR,
      message: error.message,
    });
    span.recordException(error);
    span.end();
    
    logger.error('Workflow execution failed', {
      workflow_type: req.body.workflow_type,
      error: error.message,
    });
    
    res.status(500).json({
      error: 'Workflow execution failed',
      message: error.message,
    });
  }
});

// Helper functions
async function executeModelInference(step, input_data) {
  const response = await axios.post('http://model-router:8000/route', {
    model_type: step.model_type,
    prompt: step.prompt_template.replace(/\{(\w+)\}/g, (match, key) => input_data[key] || match),
  });
  
  return response.data;
}

async function executeDataProcessing(step, input_data) {
  // Simulate data processing
  await new Promise(resolve => setTimeout(resolve, 100));
  
  return {
    processed_data: input_data,
    processing_timestamp: new Date().toISOString(),
  };
}

async function executeExternalApiCall(step, input_data) {
  const response = await axios({
    method: step.method || 'GET',
    url: step.url,
    data: step.data || input_data,
    headers: step.headers || {},
    timeout: step.timeout || 10000,
  });
  
  return response.data;
}

// Error handling middleware
app.use((error, req, res, next) => {
  logger.error('Unhandled error', {
    error: error.message,
    stack: error.stack,
    url: req.url,
    method: req.method,
  });
  
  res.status(500).json({
    error: 'Internal server error',
    message: process.env.NODE_ENV === 'development' ? error.message : 'Something went wrong',
  });
});

// Start server
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  logger.info(`Server started on port ${PORT}`);
});

// Graceful shutdown
process.on('SIGTERM', () => {
  logger.info('SIGTERM received, shutting down gracefully');
  server.close(() => {
    logger.info('Server closed');
    pool.end();
    redisClient.quit();
    process.exit(0);
  });
});

process.on('SIGINT', () => {
  logger.info('SIGINT received, shutting down gracefully');
  server.close(() => {
    logger.info('Server closed');
    pool.end();
    redisClient.quit();
    process.exit(0);
  });
});
```

### 3.2 Fastify Application Example

```javascript
// fastify-app.js - Fastify application with OpenTelemetry
const fastify = require('fastify')({ logger: true });
const axios = require('axios');
const redis = require('redis');
const { trace, context, SpanStatusCode } = require('@opentelemetry/api');

// Initialize Redis client
const redisClient = redis.createClient({
  host: process.env.REDIS_HOST || 'localhost',
  port: process.env.REDIS_PORT || 6379,
  password: process.env.REDIS_PASSWORD,
});

// Register plugins
fastify.register(require('@fastify/cors'), {
  origin: true,
});

fastify.register(require('@fastify/helmet'), {
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      styleSrc: ["'self'", "'unsafe-inline'"],
      scriptSrc: ["'self'"],
      imgSrc: ["'self'", "data:", "https:"],
    },
  },
});

// Health check route
fastify.get('/health', async (request, reply) => {
  const tracer = trace.getTracer('health-check');
  
  try {
    const span = tracer.startSpan('health-check');
    
    // Check Redis connection
    await redisClient.ping();
    
    span.setStatus({ code: SpanStatusCode.OK });
    span.end();
    
    return {
      status: 'healthy',
      timestamp: new Date().toISOString(),
      service: process.env.OTEL_SERVICE_NAME || 'frontend',
      version: process.env.OTEL_SERVICE_VERSION || '1.0.0',
    };
  } catch (error) {
    const span = tracer.startSpan('health-check');
    span.setStatus({ code: SpanStatusCode.ERROR, message: error.message });
    span.recordException(error);
    span.end();
    
    request.log.error('Health check failed', { error: error.message });
    return reply.code(500).send({
      status: 'unhealthy',
      error: error.message,
      timestamp: new Date().toISOString(),
    });
  }
});

// Model routing route
fastify.post('/api/route', async (request, reply) => {
  const tracer = trace.getTracer('model-router');
  const span = tracer.startSpan('model-routing', {
    attributes: {
      'mcp.model_type': request.body.model_type,
      'mcp.prompt_length': request.body.prompt?.length || 0,
      'mcp.operation': 'model_routing',
    },
  });
  
  try {
    const { model_type, prompt } = request.body;
    
    if (!model_type || !prompt) {
      span.setStatus({
        code: SpanStatusCode.ERROR,
        message: 'Missing required fields: model_type and prompt',
      });
      span.end();
      return reply.code(400).send({
        error: 'Missing required fields: model_type and prompt',
      });
    }
    
    request.log.info('Routing model request', { model_type, promptLength: prompt.length });
    
    // Check cache first
    const cacheKey = `model:${model_type}:${prompt.hashCode()}`;
    const cachedResult = await redisClient.get(cacheKey);
    
    if (cachedResult) {
      const result = JSON.parse(cachedResult);
      span.setAttribute('mcp.cache_hit', true);
      span.setAttribute('mcp.response_length', result.response.length);
      span.setAttribute('mcp.tokens_used', result.tokens_used);
      
      request.log.info('Model request served from cache', { model_type, tokens_used: result.tokens_used });
      
      span.setStatus({ code: SpanStatusCode.OK });
      span.end();
      
      return result;
    }
    
    span.setAttribute('mcp.cache_hit', false);
    
    // Route to model service
    const modelResponse = await axios.post('http://model-router:8000/route', {
      model_type,
      prompt,
    }, {
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
        'X-Trace-ID': span.spanContext().traceId,
      },
    });
    
    const result = {
      model_type,
      response: modelResponse.data.response,
      tokens_used: modelResponse.data.tokens_used,
      processing_time_ms: modelResponse.data.processing_time_ms,
      timestamp: new Date().toISOString(),
    };
    
    // Cache the result
    await redisClient.setex(cacheKey, 3600, JSON.stringify(result));
    
    span.setAttribute('mcp.response_length', result.response.length);
    span.setAttribute('mcp.tokens_used', result.tokens_used);
    span.setAttribute('mcp.processing_time_ms', result.processing_time_ms);
    
    request.log.info('Model routing completed', {
      model_type,
      tokens_used: result.tokens_used,
      processing_time_ms: result.processing_time_ms,
    });
    
    span.setStatus({ code: SpanStatusCode.OK });
    span.end();
    
    return result;
  } catch (error) {
    span.setStatus({
      code: SpanStatusCode.ERROR,
      message: error.message,
    });
    span.recordException(error);
    span.end();
    
    request.log.error('Model routing failed', {
      error: error.message,
      model_type: request.body.model_type,
    });
    
    return reply.code(500).send({
      error: 'Model routing failed',
      message: error.message,
    });
  }
});

// Start server
const start = async () => {
  try {
    await fastify.listen({ port: process.env.PORT || 3000, host: '0.0.0.0' });
  } catch (err) {
    fastify.log.error(err);
    process.exit(1);
  }
};

start();
```

---

## 4. Custom Instrumentation

### 4.1 Custom Tracing for Business Logic

```javascript
// custom-tracing.js - Custom OpenTelemetry instrumentation
const { trace, context, SpanStatusCode, SpanKind } = require('@opentelemetry/api');
const { Histogram, Counter, UpDownCounter } = require('@opentelemetry/api');

class ModelRouterTracer {
  constructor() {
    this.tracer = trace.getTracer('model-router', '1.0.0');
    
    // Custom metrics
    this.modelInferenceCounter = new Counter('mcp_model_inference_total', {
      description: 'Total number of model inference requests',
    });
    
    this.modelInferenceDuration = new Histogram('mcp_model_inference_duration_seconds', {
      description: 'Model inference duration in seconds',
      unit: 's',
    });
    
    this.modelTokenUsage = new Counter('mcp_model_token_usage_total', {
      description: 'Total number of tokens used by models',
    });
    
    this.modelErrorCounter = new Counter('mcp_model_inference_errors_total', {
      description: 'Total number of model inference errors',
    });
    
    this.activeInferences = new UpDownCounter('mcp_active_inferences', {
      description: 'Number of active model inferences',
    });
    
    this.modelCacheHits = new Counter('mcp_model_cache_hits_total', {
      description: 'Total number of model cache hits',
    });
    
    this.modelCacheMisses = new Counter('mcp_model_cache_misses_total', {
      description: 'Total number of model cache misses',
    });
  }
  
  async traceModelInference(modelType, prompt, inferenceFunc) {
    const span = this.tracer.startSpan('model_inference', {
      kind: SpanKind.SERVER,
      attributes: {
        'mcp.model_type': modelType,
        'mcp.prompt_length': prompt.length,
        'mcp.operation': 'model_inference',
        'mcp.service': 'model-router',
      },
    });
    
    const startTime = Date.now();
    this.activeInferences.add(1, {
      'mcp.model_type': modelType,
      'mcp.service': 'model-router',
    });
    
    try {
      // Execute model inference
      const result = await inferenceFunc(modelType, prompt);
      
      const duration = (Date.now() - startTime) / 1000;
      
      // Record metrics
      this.modelInferenceCounter.add(1, {
        'mcp.model_type': modelType,
        'mcp.service': 'model-router',
      });
      
      this.modelInferenceDuration.record(duration, {
        'mcp.model_type': modelType,
        'mcp.service': 'model-router',
      });
      
      this.modelTokenUsage.add(result.tokens_used || 0, {
        'mcp.model_type': modelType,
        'mcp.service': 'model-router',
      });
      
      // Set span attributes
      span.setAttribute('mcp.inference_success', true);
      span.setAttribute('mcp.response_length', result.response?.length || 0);
      span.setAttribute('mcp.tokens_used', result.tokens_used || 0);
      span.setAttribute('mcp.processing_time_ms', result.processing_time_ms || 0);
      
      // Add events
      span.addEvent('Model inference completed', {
        'mcp.tokens_used': result.tokens_used || 0,
        'mcp.processing_time_ms': result.processing_time_ms || 0,
      });
      
      span.setStatus({ code: SpanStatusCode.OK });
      
      return result;
    } catch (error) {
      const duration = (Date.now() - startTime) / 1000;
      
      // Record error metrics
      this.modelErrorCounter.add(1, {
        'mcp.model_type': modelType,
        'mcp.error_type': error.constructor.name,
        'mcp.service': 'model-router',
      });
      
      // Set error status
      span.setStatus({
        code: SpanStatusCode.ERROR,
        message: error.message,
      });
      
      span.recordException(error);
      
      // Add error event
      span.addEvent('Model inference failed', {
        'mcp.error': error.message,
        'mcp.error_type': error.constructor.name,
      });
      
      throw error;
    } finally {
      this.activeInferences.add(-1, {
        'mcp.model_type': modelType,
        'mcp.service': 'model-router',
      });
      
      span.end();
    }
  }
  
  recordCacheHit(modelType) {
    this.modelCacheHits.add(1, {
      'mcp.model_type': modelType,
      'mcp.service': 'model-router',
    });
  }
  
  recordCacheMiss(modelType) {
    this.modelCacheMisses.add(1, {
      'mcp.model_type': modelType,
      'mcp.service': 'model-router',
    });
  }
}

class WorkflowTracer {
  constructor() {
    this.tracer = trace.getTracer('workflow-executor', '1.0.0');
    
    // Custom metrics
    this.workflowExecutionCounter = new Counter('mcp_workflow_execution_total', {
      description: 'Total number of workflow executions',
    });
    
    this.workflowDuration = new Histogram('mcp_workflow_execution_duration_seconds', {
      description: 'Workflow execution duration in seconds',
      unit: 's',
    });
    
    this.workflowStepCounter = new Counter('mcp_workflow_step_total', {
      description: 'Total number of workflow steps executed',
    });
    
    this.workflowErrorCounter = new Counter('mcp_workflow_errors_total', {
      description: 'Total number of workflow errors',
    });
    
    this.activeWorkflows = new UpDownCounter('mcp_active_workflows', {
      description: 'Number of active workflows',
    });
  }
  
  async traceWorkflowExecution(workflowId, workflowType, steps, executionFunc) {
    const span = this.tracer.startSpan('workflow_execution', {
      kind: SpanKind.SERVER,
      attributes: {
        'mcp.workflow_id': workflowId,
        'mcp.workflow_type': workflowType,
        'mcp.workflow_steps': steps.length,
        'mcp.operation': 'workflow_execution',
        'mcp.service': 'workflow-orchestrator',
      },
    });
    
    const startTime = Date.now();
    this.activeWorkflows.add(1, {
      'mcp.workflow_type': workflowType,
      'mcp.service': 'workflow-orchestrator',
    });
    
    try {
      // Execute workflow
      const result = await executionFunc(workflowId, workflowType, steps);
      
      const duration = (Date.now() - startTime) / 1000;
      
      // Record metrics
      this.workflowExecutionCounter.add(1, {
        'mcp.workflow_type': workflowType,
        'mcp.service': 'workflow-orchestrator',
      });
      
      this.workflowDuration.record(duration, {
        'mcp.workflow_type': workflowType,
        'mcp.service': 'workflow-orchestrator',
      });
      
      this.workflowStepCounter.add(result.completed_steps || 0, {
        'mcp.workflow_type': workflowType,
        'mcp.service': 'workflow-orchestrator',
      });
      
      // Set span attributes
      span.setAttribute('mcp.workflow_success', true);
      span.setAttribute('mcp.workflow_duration_ms', duration * 1000);
      span.setAttribute('mcp.completed_steps', result.completed_steps || 0);
      
      span.setStatus({ code: SpanStatusCode.OK });
      
      return result;
    } catch (error) {
      const duration = (Date.now() - startTime) / 1000;
      
      // Record error metrics
      this.workflowErrorCounter.add(1, {
        'mcp.workflow_type': workflowType,
        'mcp.error_type': error.constructor.name,
        'mcp.service': 'workflow-orchestrator',
      });
      
      // Set error status
      span.setStatus({
        code: SpanStatusCode.ERROR,
        message: error.message,
      });
      
      span.recordException(error);
      
      throw error;
    } finally {
      this.activeWorkflows.add(-1, {
        'mcp.workflow_type': workflowType,
        'mcp.service': 'workflow-orchestrator',
      });
      
      span.end();
    }
  }
  
  async traceWorkflowStep(workflowId, stepName, stepFunc, ...args) {
    const span = this.tracer.startSpan(`workflow_step_${stepName}`, {
      kind: SpanKind.INTERNAL,
      attributes: {
        'mcp.workflow_id': workflowId,
        'mcp.step_name': stepName,
        'mcp.operation': 'workflow_step',
        'mcp.service': 'workflow-orchestrator',
      },
    });
    
    const startTime = Date.now();
    
    try {
      // Execute step
      const result = await stepFunc(...args);
      
      const duration = (Date.now() - startTime) / 1000;
      
      // Record metrics
      this.workflowStepCounter.add(1, {
        'mcp.step_name': stepName,
        'mcp.service': 'workflow-orchestrator',
      });
      
      // Set span attributes
      span.setAttribute('mcp.step_success', true);
      span.setAttribute('mcp.step_duration_ms', duration * 1000);
      
      span.setStatus({ code: SpanStatusCode.OK });
      
      return result;
    } catch (error) {
      const duration = (Date.now() - startTime) / 1000;
      
      // Record error metrics
      this.workflowErrorCounter.add(1, {
        'mcp.step_name': stepName,
        'mcp.error_type': error.constructor.name,
        'mcp.service': 'workflow-orchestrator',
      });
      
      // Set error status
      span.setStatus({
        code: SpanStatusCode.ERROR,
        message: error.message,
      });
      
      span.recordException(error);
      
      throw error;
    } finally {
      span.end();
    }
  }
}

// Export tracer instances
module.exports = {
  ModelRouterTracer,
  WorkflowTracer,
};
```

### 4.2 Custom Metrics

```javascript
// custom-metrics.js - Custom OpenTelemetry metrics
const { metrics } = require('@opentelemetry/api');

class BusinessMetrics {
  constructor() {
    this.meter = metrics.getMeter('mcp-business-metrics', '1.0.0');
    
    // User engagement metrics
    this.userSessionCounter = this.meter.createCounter('mcp_user_sessions_total', {
      description: 'Total number of user sessions',
    });
    
    this.userSessionDuration = this.meter.createHistogram('mcp_user_session_duration_seconds', {
      description: 'User session duration in seconds',
      unit: 's',
    });
    
    this.activeUserSessions = this.meter.createUpDownCounter('mcp_active_user_sessions', {
      description: 'Number of active user sessions',
    });
    
    // Content generation metrics
    this.contentGenerationCounter = this.meter.createCounter('mcp_content_generation_total', {
      description: 'Total number of content generation requests',
    });
    
    this.contentGenerationDuration = this.meter.createHistogram('mcp_content_generation_duration_seconds', {
      description: 'Content generation duration in seconds',
      unit: 's',
    });
    
    this.contentLengthGenerated = this.meter.createCounter('mcp_content_length_generated_total', {
      description: 'Total length of generated content in characters',
    });
    
    // Collaboration metrics
    this.collaborationSessionCounter = this.meter.createCounter('mcp_collaboration_sessions_total', {
      description: 'Total number of collaboration sessions',
    });
    
    this.collaborationParticipants = this.meter.createHistogram('mcp_collaboration_participants', {
      description: 'Number of participants in collaboration sessions',
    });
    
    this.collaborationDuration = this.meter.createHistogram('mcp_collaboration_duration_seconds', {
      description: 'Collaboration session duration in seconds',
      unit: 's',
    });
    
    // Cost metrics
    this.costIncurred = this.meter.createCounter('mcp_cost_incurred_total', {
      description: 'Total cost incurred in USD',
    });
    
    this.costByModel = this.meter.createCounter('mcp_cost_by_model_total', {
      description: 'Total cost incurred by model type in USD',
    });
    
    this.costByUser = this.meter.createCounter('mcp_cost_by_user_total', {
      description: 'Total cost incurred by user in USD',
    });
  }
  
  // User engagement methods
  recordUserStart(userId, userType) {
    this.activeUserSessions.add(1, {
      'mcp.user_id': userId,
      'mcp.user_type': userType,
    });
  }
  
  recordUserEnd(userId, userType, duration) {
    this.activeUserSessions.add(-1, {
      'mcp.user_id': userId,
      'mcp.user_type': userType,
    });
    
    this.userSessionCounter.add(1, {
      'mcp.user_type': userType,
    });
    
    this.userSessionDuration.record(duration, {
      'mcp.user_type': userType,
    });
  }
  
  // Content generation methods
  recordContentGeneration(modelType, duration, contentLength, cost) {
    this.contentGenerationCounter.add(1, {
      'mcp.model_type': modelType,
    });
    
    this.contentGenerationDuration.record(duration, {
      'mcp.model_type': modelType,
    });
    
    this.contentLengthGenerated.add(contentLength, {
      'mcp.model_type': modelType,
    });
    
    this.costIncurred.add(cost, {
      'mcp.model_type': modelType,
    });
    
    this.costByModel.add(cost, {
      'mcp.model_type': modelType,
    });
  }
  
  // Collaboration methods
  recordCollaborationStart(sessionId, participantCount) {
    this.collaborationSessionCounter.add(1);
    this.collaborationParticipants.record(participantCount);
  }
  
  recordCollaborationEnd(sessionId, duration) {
    this.collaborationDuration.record(duration);
  }
  
  // Cost tracking methods
  recordUserCost(userId, cost, modelType) {
    this.costIncurred.add(cost, {
      'mcp.user_id': userId,
      'mcp.model_type': modelType,
    });
    
    this.costByUser.add(cost, {
      'mcp.user_id': userId,
    });
    
    this.costByModel.add(cost, {
      'mcp.model_type': modelType,
    });
  }
}

// Export metrics instance
module.exports = BusinessMetrics;
```

---

## 5. Kubernetes Deployment

### 5.1 Deployment Manifest

```yaml
# frontend-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend
  namespace: mcp-system
  labels:
    app: frontend
    component: mcp-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: frontend
  template:
    metadata:
      labels:
        app: frontend
        component: mcp-service
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "3000"
        prometheus.io/path: "/metrics"
        # OpenTelemetry injection annotation
        instrumentation.opentelemetry.io/inject-nodejs: "true"
    spec:
      containers:
      - name: frontend
        image: mcp-system/frontend:1.0.0
        ports:
        - containerPort: 3000
          name: http
          protocol: TCP
        env:
        - name: NODE_ENV
          value: "production"
        - name: PORT
          value: "3000"
        - name: SERVICE_NAME
          value: "frontend"
        - name: SERVICE_VERSION
          value: "1.0.0"
        - name: ENVIRONMENT
          value: "production"
        - name: REDIS_HOST
          value: "redis"
        - name: REDIS_PORT
          value: "6379"
        - name: REDIS_PASSWORD
          valueFrom:
            secretKeyRef:
              name: redis-secret
              key: password
        - name: DB_HOST
          value: "postgres"
        - name: DB_PORT
          value: "5432"
        - name: DB_NAME
          value: "mcp"
        - name: DB_USER
          valueFrom:
            secretKeyRef:
              name: database-secret
              key: username
        - name: DB_PASSWORD
          valueFrom:
            secretKeyRef:
              name: database-secret
              key: password
        # OpenTelemetry environment variables
        - name: NODE_OPTIONS
          value: "--require ./tracing.js"
        - name: OTEL_SERVICE_NAME
          value: "frontend"
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
        - name: OTEL_METRICS_EXPORTER
          value: "otlp"
        - name: OTEL_LOGS_EXPORTER
          value: "otlp"
        - name: OTEL_NODE_RESOURCE_DETECTORS
          value