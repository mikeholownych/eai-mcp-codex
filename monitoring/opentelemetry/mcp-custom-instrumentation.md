# MCP-Specific Custom Instrumentation Patterns

This document provides custom instrumentation patterns specifically designed for MCP (Multimodal Content Processor) system operations, including agent collaboration, model routing, workflow execution, and other business-specific operations.

---

## 1. Overview

### 1.1 MCP-Specific Operations

The MCP system involves several unique operations that require specialized instrumentation:

- **Agent Collaboration**: Multi-agent consensus and collaboration processes
- **Model Routing**: Intelligent routing of requests to appropriate AI models
- **Workflow Execution**: Complex multi-step workflows with branching logic
- **Plan Management**: Creation, validation, and execution of plans
- **Verification Feedback**: Quality assessment and feedback loops
- **Git Worktree Operations**: Version control operations for content management

### 1.2 Custom Instrumentation Goals

- **Business Context**: Capture business-specific metrics and attributes
- **Performance Analysis**: Measure performance of complex multi-step operations
- **Error Tracking**: Track errors specific to MCP operations
- **Resource Utilization**: Monitor resource usage across different operations
- **User Experience**: Track user-facing performance and success rates

---

## 2. Agent Collaboration Instrumentation

### 2.1 Python Implementation

```python
# mcp_agent_collaboration_tracing.py
from opentelemetry import trace, metrics, context
from opentelemetry.trace import Status, StatusCode, SpanKind
from opentelemetry.metrics import Counter, Histogram, UpDownCounter
from typing import List, Dict, Any, Optional
import structlog
import time
import asyncio

logger = structlog.get_logger(__name__)

class AgentCollaborationTracer:
    """Custom tracer for agent collaboration operations"""
    
    def __init__(self):
        self.tracer = trace.get_tracer("mcp-agent-collaboration", "1.0.0")
        self.meter = metrics.get_meter("mcp-agent-collaboration", "1.0.0")
        
        # Define metrics
        self.collaboration_counter = self.meter.create_counter(
            "mcp_agent_collaboration_total",
            description="Total number of agent collaboration sessions"
        )
        
        self.collaboration_duration = self.meter.create_histogram(
            "mcp_agent_collaboration_duration_seconds",
            description="Agent collaboration session duration in seconds",
            unit="s"
        )
        
        self.collaboration_iterations = self.meter.create_histogram(
            "mcp_agent_collaboration_iterations",
            description="Number of iterations in agent collaboration sessions"
        )
        
        self.collaboration_success_counter = self.meter.create_counter(
            "mcp_agent_collaboration_success_total",
            description="Total number of successful agent collaboration sessions"
        )
        
        self.collaboration_error_counter = self.meter.create_counter(
            "mcp_agent_collaboration_errors_total",
            description="Total number of failed agent collaboration sessions"
        )
        
        self.active_collaborations = self.meter.create_up_down_counter(
            "mcp_active_agent_collaborations",
            description="Number of active agent collaboration sessions"
        )
        
        self.consensus_time = self.meter.create_histogram(
            "mcp_agent_consensus_time_seconds",
            description="Time taken to reach consensus in agent collaboration",
            unit="s"
        )
        
        self.agent_participation_counter = self.meter.create_counter(
            "mcp_agent_participation_total",
            description="Total number of agent participations in collaborations"
        )
        
        self.agent_contribution_score = self.meter.create_histogram(
            "mcp_agent_contribution_score",
            description="Contribution score of agents in collaborations"
        )
    
    async def trace_collaboration_session(
        self,
        collaboration_id: str,
        collaboration_type: str,
        agents: List[str],
        task: str,
        collaboration_func: callable
    ) -> Dict[str, Any]:
        """Trace an agent collaboration session"""
        span = self.tracer.start_span(
            "agent_collaboration_session",
            kind=SpanKind.SERVER,
            attributes={
                "mcp.collaboration_id": collaboration_id,
                "mcp.collaboration_type": collaboration_type,
                "mcp.agents_involved": ",".join(agents),
                "mcp.agent_count": len(agents),
                "mcp.task": task,
                "mcp.operation": "agent_collaboration",
                "mcp.service": "agent-collaboration"
            }
        )
        
        start_time = time.time()
        self.active_collaborations.add(1, {
            "mcp.collaboration_type": collaboration_type,
            "mcp.service": "agent-collaboration"
        })
        
        try:
            # Execute collaboration
            result = await collaboration_func(collaboration_id, collaboration_type, agents, task)
            
            duration = time.time() - start_time
            
            # Record metrics
            self.collaboration_counter.add(1, {
                "mcp.collaboration_type": collaboration_type,
                "mcp.success": "true"
            })
            
            self.collaboration_duration.record(duration, {
                "mcp.collaboration_type": collaboration_type
            })
            
            self.collaboration_iterations.record(result.get("iterations", 0), {
                "mcp.collaboration_type": collaboration_type
            })
            
            self.collaboration_success_counter.add(1, {
                "mcp.collaboration_type": collaboration_type
            })
            
            self.consensus_time.record(result.get("consensus_time", 0), {
                "mcp.collaboration_type": collaboration_type
            })
            
            # Record agent participation
            for agent in agents:
                self.agent_participation_counter.add(1, {
                    "mcp.agent_name": agent,
                    "mcp.collaboration_type": collaboration_type
                })
                
                # Record contribution score if available
                if "contributions" in result and agent in result["contributions"]:
                    contribution_score = result["contributions"][agent].get("score", 0)
                    self.agent_contribution_score.record(contribution_score, {
                        "mcp.agent_name": agent,
                        "mcp.collaboration_type": collaboration_type
                    })
            
            # Set span attributes
            span.set_attribute("mcp.collaboration_success", True)
            span.set_attribute("mcp.collaboration_duration_ms", duration * 1000)
            span.set_attribute("mcp.collaboration_iterations", result.get("iterations", 0))
            span.set_attribute("mcp.consensus_time_ms", result.get("consensus_time", 0) * 1000)
            span.set_attribute("mcp.final_result_quality", result.get("quality_score", 0))
            
            # Add events
            span.add_event("Collaboration started", {
                "mcp.agents_involved": ",".join(agents),
                "mcp.task": task
            })
            
            span.add_event("Collaboration completed", {
                "mcp.duration_ms": duration * 1000,
                "mcp.iterations": result.get("iterations", 0),
                "mcp.consensus_reached": result.get("consensus_reached", False)
            })
            
            logger.info(
                "Agent collaboration session completed",
                collaboration_id=collaboration_id,
                collaboration_type=collaboration_type,
                duration_ms=duration * 1000,
                iterations=result.get("iterations", 0),
                consensus_time_ms=result.get("consensus_time", 0) * 1000
            )
            
            span.set_status(Status(StatusCode.OK))
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            
            # Record error metrics
            self.collaboration_counter.add(1, {
                "mcp.collaboration_type": collaboration_type,
                "mcp.success": "false"
            })
            
            self.collaboration_error_counter.add(1, {
                "mcp.collaboration_type": collaboration_type,
                "mcp.error_type": type(e).__name__
            })
            
            # Set error status
            span.set_status(Status(StatusCode.ERROR, str(e)))
            span.record_exception(e)
            
            # Add error event
            span.add_event("Collaboration failed", {
                "mcp.error": str(e),
                "mcp.error_type": type(e).__name__,
                "mcp.duration_ms": duration * 1000
            })
            
            logger.error(
                "Agent collaboration session failed",
                collaboration_id=collaboration_id,
                collaboration_type=collaboration_type,
                error=str(e),
                error_type=type(e).__name__,
                duration_ms=duration * 1000
            )
            
            raise
            
        finally:
            self.active_collaborations.add(-1, {
                "mcp.collaboration_type": collaboration_type,
                "mcp.service": "agent-collaboration"
            })
            span.end()
    
    async def trace_agent_iteration(
        self,
        collaboration_id: str,
        agent_name: str,
        iteration_number: int,
        iteration_func: callable,
        *args, **kwargs
    ) -> Any:
        """Trace a single agent iteration within a collaboration"""
        span = self.tracer.start_span(
            f"agent_iteration_{agent_name}",
            kind=SpanKind.INTERNAL,
            attributes={
                "mcp.collaboration_id": collaboration_id,
                "mcp.agent_name": agent_name,
                "mcp.iteration_number": iteration_number,
                "mcp.operation": "agent_iteration",
                "mcp.service": "agent-collaboration"
            }
        )
        
        start_time = time.time()
        
        try:
            # Execute agent iteration
            result = await iteration_func(*args, **kwargs)
            
            duration = time.time() - start_time
            
            # Set span attributes
            span.set_attribute("mcp.iteration_success", True)
            span.set_attribute("mcp.iteration_duration_ms", duration * 1000)
            span.set_attribute("mcp.agent_contribution", getattr(result, 'contribution_score', 0))
            
            # Add event
            span.add_event("Agent iteration completed", {
                "mcp.duration_ms": duration * 1000,
                "mcp.contribution_score": getattr(result, 'contribution_score', 0)
            })
            
            logger.debug(
                "Agent iteration completed",
                collaboration_id=collaboration_id,
                agent_name=agent_name,
                iteration_number=iteration_number,
                duration_ms=duration * 1000,
                contribution_score=getattr(result, 'contribution_score', 0)
            )
            
            span.set_status(Status(StatusCode.OK))
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            
            # Set error status
            span.set_status(Status(StatusCode.ERROR, str(e)))
            span.record_exception(e)
            
            # Add error event
            span.add_event("Agent iteration failed", {
                "mcp.error": str(e),
                "mcp.error_type": type(e).__name__,
                "mcp.duration_ms": duration * 1000
            })
            
            logger.error(
                "Agent iteration failed",
                collaboration_id=collaboration_id,
                agent_name=agent_name,
                iteration_number=iteration_number,
                error=str(e),
                error_type=type(e).__name__,
                duration_ms=duration * 1000
            )
            
            raise
            
        finally:
            span.end()
    
    async def trace_consensus_building(
        self,
        collaboration_id: str,
        agents: List[str],
        consensus_func: callable,
        *args, **kwargs
    ) -> Dict[str, Any]:
        """Trace consensus building process"""
        span = self.tracer.start_span(
            "consensus_building",
            kind=SpanKind.INTERNAL,
            attributes={
                "mcp.collaboration_id": collaboration_id,
                "mcp.agents_involved": ",".join(agents),
                "mcp.agent_count": len(agents),
                "mcp.operation": "consensus_building",
                "mcp.service": "agent-collaboration"
            }
        )
        
        start_time = time.time()
        
        try:
            # Execute consensus building
            result = await consensus_func(*args, **kwargs)
            
            duration = time.time() - start_time
            
            # Set span attributes
            span.set_attribute("mcp.consensus_reached", result.get("consensus_reached", False))
            span.set_attribute("mcp.consensus_duration_ms", duration * 1000)
            span.set_attribute("mcp.consensus_iterations", result.get("iterations", 0))
            span.set_attribute("mcp.final_agreement_score", result.get("agreement_score", 0))
            
            # Add events
            span.add_event("Consensus building started", {
                "mcp.agents_involved": ",".join(agents)
            })
            
            span.add_event("Consensus building completed", {
                "mcp.consensus_reached": result.get("consensus_reached", False),
                "mcp.duration_ms": duration * 1000,
                "mcp.iterations": result.get("iterations", 0)
            })
            
            logger.info(
                "Consensus building completed",
                collaboration_id=collaboration_id,
                consensus_reached=result.get("consensus_reached", False),
                duration_ms=duration * 1000,
                iterations=result.get("iterations", 0),
                agreement_score=result.get("agreement_score", 0)
            )
            
            span.set_status(Status(StatusCode.OK))
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            
            # Set error status
            span.set_status(Status(StatusCode.ERROR, str(e)))
            span.record_exception(e)
            
            # Add error event
            span.add_event("Consensus building failed", {
                "mcp.error": str(e),
                "mcp.error_type": type(e).__name__,
                "mcp.duration_ms": duration * 1000
            })
            
            logger.error(
                "Consensus building failed",
                collaboration_id=collaboration_id,
                error=str(e),
                error_type=type(e).__name__,
                duration_ms=duration * 1000
            )
            
            raise
            
        finally:
            span.end()
```

### 2.2 JavaScript/Node.js Implementation

```javascript
// mcp-agent-collaboration-tracing.js
const { trace, metrics, context } = require('@opentelemetry/api');
const { SpanKind, SpanStatusCode } = require('@opentelemetry/api');

class AgentCollaborationTracer {
  constructor() {
    this.tracer = trace.getTracer('mcp-agent-collaboration', '1.0.0');
    this.meter = metrics.getMeter('mcp-agent-collaboration', '1.0.0');
    
    // Define metrics
    this.collaborationCounter = this.meter.createCounter('mcp_agent_collaboration_total', {
      description: 'Total number of agent collaboration sessions'
    });
    
    this.collaborationDuration = this.meter.createHistogram('mcp_agent_collaboration_duration_seconds', {
      description: 'Agent collaboration session duration in seconds',
      unit: 's'
    });
    
    this.collaborationIterations = this.meter.createHistogram('mcp_agent_collaboration_iterations', {
      description: 'Number of iterations in agent collaboration sessions'
    });
    
    this.collaborationSuccessCounter = this.meter.createCounter('mcp_agent_collaboration_success_total', {
      description: 'Total number of successful agent collaboration sessions'
    });
    
    this.collaborationErrorCounter = this.meter.createCounter('mcp_agent_collaboration_errors_total', {
      description: 'Total number of failed agent collaboration sessions'
    });
    
    this.activeCollaborations = this.meter.createUpDownCounter('mcp_active_agent_collaborations', {
      description: 'Number of active agent collaboration sessions'
    });
    
    this.consensusTime = this.meter.createHistogram('mcp_agent_consensus_time_seconds', {
      description: 'Time taken to reach consensus in agent collaboration',
      unit: 's'
    });
    
    this.agentParticipationCounter = this.meter.createCounter('mcp_agent_participation_total', {
      description: 'Total number of agent participations in collaborations'
    });
    
    this.agentContributionScore = this.meter.createHistogram('mcp_agent_contribution_score', {
      description: 'Contribution score of agents in collaborations'
    });
  }
  
  async traceCollaborationSession(collaborationId, collaborationType, agents, task, collaborationFunc) {
    const span = this.tracer.startSpan('agent_collaboration_session', {
      kind: SpanKind.SERVER,
      attributes: {
        'mcp.collaboration_id': collaborationId,
        'mcp.collaboration_type': collaborationType,
        'mcp.agents_involved': agents.join(','),
        'mcp.agent_count': agents.length,
        'mcp.task': task,
        'mcp.operation': 'agent_collaboration',
        'mcp.service': 'agent-collaboration'
      }
    });
    
    const startTime = Date.now();
    this.activeCollaborations.add(1, {
      'mcp.collaboration_type': collaborationType,
      'mcp.service': 'agent-collaboration'
    });
    
    try {
      // Execute collaboration
      const result = await collaborationFunc(collaborationId, collaborationType, agents, task);
      
      const duration = (Date.now() - startTime) / 1000;
      
      // Record metrics
      this.collaborationCounter.add(1, {
        'mcp.collaboration_type': collaborationType,
        'mcp.success': 'true'
      });
      
      this.collaborationDuration.record(duration, {
        'mcp.collaboration_type': collaborationType
      });
      
      this.collaborationIterations.record(result.iterations || 0, {
        'mcp.collaboration_type': collaborationType
      });
      
      this.collaborationSuccessCounter.add(1, {
        'mcp.collaboration_type': collaborationType
      });
      
      this.consensusTime.record(result.consensus_time || 0, {
        'mcp.collaboration_type': collaborationType
      });
      
      // Record agent participation
      for (const agent of agents) {
        this.agentParticipationCounter.add(1, {
          'mcp.agent_name': agent,
          'mcp.collaboration_type': collaborationType
        });
        
        // Record contribution score if available
        if (result.contributions && result.contributions[agent]) {
          const contributionScore = result.contributions[agent].score || 0;
          this.agentContributionScore.record(contributionScore, {
            'mcp.agent_name': agent,
            'mcp.collaboration_type': collaborationType
          });
        }
      }
      
      // Set span attributes
      span.setAttribute('mcp.collaboration_success', true);
      span.setAttribute('mcp.collaboration_duration_ms', duration * 1000);
      span.setAttribute('mcp.collaboration_iterations', result.iterations || 0);
      span.setAttribute('mcp.consensus_time_ms', (result.consensus_time || 0) * 1000);
      span.setAttribute('mcp.final_result_quality', result.quality_score || 0);
      
      // Add events
      span.addEvent('Collaboration started', {
        'mcp.agents_involved': agents.join(','),
        'mcp.task': task
      });
      
      span.addEvent('Collaboration completed', {
        'mcp.duration_ms': duration * 1000,
        'mcp.iterations': result.iterations || 0,
        'mcp.consensus_reached': result.consensus_reached || false
      });
      
      console.log(`Agent collaboration session completed: ${collaborationId}, type: ${collaborationType}, duration: ${duration * 1000}ms`);
      
      span.setStatus({ code: SpanStatusCode.OK });
      return result;
      
    } catch (error) {
      const duration = (Date.now() - startTime) / 1000;
      
      // Record error metrics
      this.collaborationCounter.add(1, {
        'mcp.collaboration_type': collaborationType,
        'mcp.success': 'false'
      });
      
      this.collaborationErrorCounter.add(1, {
        'mcp.collaboration_type': collaborationType,
        'mcp.error_type': error.constructor.name
      });
      
      // Set error status
      span.setStatus({
        code: SpanStatusCode.ERROR,
        message: error.message
      });
      span.recordException(error);
      
      // Add error event
      span.addEvent('Collaboration failed', {
        'mcp.error': error.message,
        'mcp.error_type': error.constructor.name,
        'mcp.duration_ms': duration * 1000
      });
      
      console.error(`Agent collaboration session failed: ${collaborationId}, type: ${collaborationType}, error: ${error.message}`);
      
      throw error;
      
    } finally {
      this.activeCollaborations.add(-1, {
        'mcp.collaboration_type': collaborationType,
        'mcp.service': 'agent-collaboration'
      });
      span.end();
    }
  }
  
  async traceAgentIteration(collaborationId, agentName, iterationNumber, iterationFunc, ...args) {
    const span = this.tracer.startSpan(`agent_iteration_${agentName}`, {
      kind: SpanKind.INTERNAL,
      attributes: {
        'mcp.collaboration_id': collaborationId,
        'mcp.agent_name': agentName,
        'mcp.iteration_number': iterationNumber,
        'mcp.operation': 'agent_iteration',
        'mcp.service': 'agent-collaboration'
      }
    });
    
    const startTime = Date.now();
    
    try {
      // Execute agent iteration
      const result = await iterationFunc(...args);
      
      const duration = (Date.now() - startTime) / 1000;
      
      // Set span attributes
      span.setAttribute('mcp.iteration_success', true);
      span.setAttribute('mcp.iteration_duration_ms', duration * 1000);
      span.setAttribute('mcp.agent_contribution', result.contribution_score || 0);
      
      // Add event
      span.addEvent('Agent iteration completed', {
        'mcp.duration_ms': duration * 1000,
        'mcp.contribution_score': result.contribution_score || 0
      });
      
      console.log(`Agent iteration completed: ${agentName}, iteration: ${iterationNumber}, duration: ${duration * 1000}ms`);
      
      span.setStatus({ code: SpanStatusCode.OK });
      return result;
      
    } catch (error) {
      const duration = (Date.now() - startTime) / 1000;
      
      // Set error status
      span.setStatus({
        code: SpanStatusCode.ERROR,
        message: error.message
      });
      span.recordException(error);
      
      // Add error event
      span.addEvent('Agent iteration failed', {
        'mcp.error': error.message,
        'mcp.error_type': error.constructor.name,
        'mcp.duration_ms': duration * 1000
      });
      
      console.error(`Agent iteration failed: ${agentName}, iteration: ${iterationNumber}, error: ${error.message}`);
      
      throw error;
      
    } finally {
      span.end();
    }
  }
  
  async traceConsensusBuilding(collaborationId, agents, consensusFunc, ...args) {
    const span = this.tracer.startSpan('consensus_building', {
      kind: SpanKind.INTERNAL,
      attributes: {
        'mcp.collaboration_id': collaborationId,
        'mcp.agents_involved': agents.join(','),
        'mcp.agent_count': agents.length,
        'mcp.operation': 'consensus_building',
        'mcp.service': 'agent-collaboration'
      }
    });
    
    const startTime = Date.now();
    
    try {
      // Execute consensus building
      const result = await consensusFunc(...args);
      
      const duration = (Date.now() - startTime) / 1000;
      
      // Set span attributes
      span.setAttribute('mcp.consensus_reached', result.consensus_reached || false);
      span.setAttribute('mcp.consensus_duration_ms', duration * 1000);
      span.setAttribute('mcp.consensus_iterations', result.iterations || 0);
      span.setAttribute('mcp.final_agreement_score', result.agreement_score || 0);
      
      // Add events
      span.addEvent('Consensus building started', {
        'mcp.agents_involved': agents.join(',')
      });
      
      span.addEvent('Consensus building completed', {
        'mcp.consensus_reached': result.consensus_reached || false,
        'mcp.duration_ms': duration * 1000,
        'mcp.iterations': result.iterations || 0
      });
      
      console.log(`Consensus building completed: ${collaborationId}, reached: ${result.consensus_reached}, duration: ${duration * 1000}ms`);
      
      span.setStatus({ code: SpanStatusCode.OK });
      return result;
      
    } catch (error) {
      const duration = (Date.now() - startTime) / 1000;
      
      // Set error status
      span.setStatus({
        code: SpanStatusCode.ERROR,
        message: error.message
      });
      span.recordException(error);
      
      // Add error event
      span.addEvent('Consensus building failed', {
        'mcp.error': error.message,
        'mcp.error_type': error.constructor.name,
        'mcp.duration_ms': duration * 1000
      });
      
      console.error(`Consensus building failed: ${collaborationId}, error: ${error.message}`);
      
      throw error;
      
    } finally {
      span.end();
    }
  }
}

module.exports = AgentCollaborationTracer;
```

---

## 3. Model Routing Instrumentation

### 3.1 Python Implementation

```python
# mcp_model_routing_tracing.py
from opentelemetry import trace, metrics
from opentelemetry.trace import Status, StatusCode, SpanKind
from opentelemetry.metrics import Counter, Histogram, UpDownCounter
from typing import Dict, Any, Optional, List
import structlog
import time
import asyncio

logger = structlog.get_logger(__name__)

class ModelRouterTracer:
    """Custom tracer for model routing operations"""
    
    def __init__(self):
        self.tracer = trace.get_tracer("mcp-model-router", "1.0.0")
        self.meter = metrics.get_meter("mcp-model-router", "1.0.0")
        
        # Define metrics
        self.routing_counter = self.meter.create_counter(
            "mcp_model_routing_total",
            description="Total number of model routing requests"
        )
        
        self.routing_duration = self.meter.create_histogram(
            "mcp_model_routing_duration_seconds",
            description="Model routing duration in seconds",
            unit="s"
        )
        
        self.routing_success_counter = self.meter.create_counter(
            "mcp_model_routing_success_total",
            description="Total number of successful model routing requests"
        )
        
        self.routing_error_counter = self.meter.create_counter(
            "mcp_model_routing_errors_total",
            description="Total number of failed model routing requests"
        )
        
        self.active_routings = self.meter.create_up_down_counter(
            "mcp_active_model_routings",
            description="Number of active model routing requests"
        )
        
        self.model_selection_time = self.meter.create_histogram(
            "mcp_model_selection_time_seconds",
            description="Time taken for model selection",
            unit="s"
        )
        
        self.model_inference_time = self.meter.create_histogram(
            "mcp_model_inference_time_seconds",
            description="Time taken for model inference",
            unit="s"
        )
        
        self.token_usage_counter = self.meter.create_counter(
            "mcp_model_token_usage_total",
            description="Total number of tokens used by models"
        )
        
        self.cost_counter = self.meter.create_counter(
            "mcp_model_cost_total",
            description="Total cost incurred by model usage",
            unit="USD"
        )
        
        self.cache_hit_counter = self.meter.create_counter(
            "mcp_model_cache_hits_total",
            description="Total number of model cache hits"
        )
        
        self.cache_miss_counter = self.meter.create_counter(
            "mcp_model_cache_misses_total",
            description="Total number of model cache misses"
        )
        
        self.model_usage_counter = self.meter.create_counter(
            "mcp_model_usage_total",
            description="Total number of requests per model"
        )
        
        self.model_error_counter = self.meter.create_counter(
            "mcp_model_errors_total",
            description="Total number of errors per model"
        )
    
    async def trace_model_routing(
        self,
        request_id: str,
        model_type: Optional[str],
        prompt: str,
        routing_func: callable
    ) -> Dict[str, Any]:
        """Trace a model routing request"""
        span = self.tracer.start_span(
            "model_routing",
            kind=SpanKind.SERVER,
            attributes={
                "mcp.request_id": request_id,
                "mcp.model_type": model_type or "auto",
                "mcp.prompt_length": len(prompt),
                "mcp.operation": "model_routing",
                "mcp.service": "model-router"
            }
        )
        
        start_time = time.time()
        self.active_routings.add(1, {
            "mcp.model_type": model_type or "auto",
            "mcp.service": "model-router"
        })
        
        try:
            # Execute model routing
            result = await routing_func(request_id, model_type, prompt)
            
            duration = time.time() - start_time
            
            # Record metrics
            self.routing_counter.add(1, {
                "mcp.model_type": result.get("model_type", model_type or "unknown"),
                "mcp.success": "true"
            })
            
            self.routing_duration.record(duration, {
                "mcp.model_type": result.get("model_type", model_type or "unknown")
            })
            
            self.routing_success_counter.add(1, {
                "mcp.model_type": result.get("model_type", model_type or "unknown")
            })
            
            self.token_usage_counter.add(result.get("tokens_used", 0), {
                "mcp.model_type": result.get("model_type", model_type or "unknown")
            })
            
            self.cost_counter.add(result.get("cost", 0), {
                "mcp.model_type": result.get("model_type", model_type or "unknown")
            })
            
            self.model_usage_counter.add(1, {
                "mcp.model_type": result.get("model_type", model_type or "unknown")
            })
            
            # Set span attributes
            span.set_attribute("mcp.routing_success", True)
            span.set_attribute("mcp.routing_duration_ms", duration * 1000)
            span.set_attribute("mcp.selected_model", result.get("model_type", "unknown"))
            span.set_attribute("mcp.tokens_used", result.get("tokens_used", 0))
            span.set_attribute("mcp.cost", result.get("cost", 0))
            span.set_attribute("mcp.cache_hit", result.get("cache_hit", False))
            span.set_attribute("mcp.response_length", len(result.get("response", "")))
            
            # Add events
            span.add_event("Model routing started", {
                "mcp.request_id": request_id,
                "mcp.prompt_length": len(prompt)
            })
            
            span.add_event("Model routing completed", {
                "mcp.selected_model": result.get("model_type", "unknown"),
                "mcp.duration_ms": duration * 1000,
                "mcp.tokens_used": result.get("tokens_used", 0),
                "mcp.cache_hit": result.get("cache_hit", False)
            })
            
            logger.info(
                "Model routing completed",
                request_id=request_id,
                model_type=result.get("model_type", "unknown"),
                duration_ms=duration * 1000,
                tokens_used=result.get("tokens_used", 0),
                cache_hit=result.get("cache_hit", False)
            )
            
            span.set_status(Status(StatusCode.OK))
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            
            # Record error metrics
            self.routing_counter.add(1, {
                "mcp.model_type": model_type or "unknown",
                "mcp.success": "false"
            })
            
            self.routing_error_counter.add(1, {
                "mcp.model_type": model_type or "unknown",
                "mcp.error_type": type(e).__name__
            })
            
            if model_type:
                self.model_error_counter.add(1, {
                    "mcp.model_type": model_type,
                    "mcp.error_type": type(e).__name__
                })
            
            # Set error status
            span.set_status(Status(StatusCode.ERROR, str(e)))
            span.record_exception(e)
            
            # Add error event
            span.add_event("Model routing failed", {
                "mcp.error": str(e),
                "mcp.error_type": type(e).__name__,
                "mcp.duration_ms": duration * 1000
            })
            
            logger.error(
                "Model routing failed",
                request_id=request_id,
                model_type=model_type,
                error=str(e),
                error_type=type(e).__name__,
                duration_ms=duration * 1000
            )
            
            raise
            
        finally:
            self.active_routings.add(-1, {
                "mcp.model_type": model_type or "auto",
                "mcp.service": "model-router"
            })
            span.end()
    
    async def trace_model_selection(
        self,
        request_id: str,
        available_models: List[str],
        selection_func: callable,
        *args, **kwargs
    ) -> str:
        """Trace model selection process"""
        span = self.tracer.start_span(
            "model_selection",
            kind=SpanKind.INTERNAL,
            attributes={
                "mcp.request_id": request_id,
                "mcp.available_models": ",".join(available_models),
                "mcp.available_model_count": len(available_models),
                "mcp.operation": "model_selection",
                "mcp.service": "model-router"
            }
        )
        
        start_time = time.time()
        
        try:
            # Execute model selection
            selected_model = await selection_func(available_models, *args, **kwargs)
            
            duration = time.time() - start_time
            
            # Record metrics
            self.model_selection_time.record(duration, {
                "mcp.selected_model": selected_model
            })
            
            # Set span attributes
            span.set_attribute("mcp.selection_success", True)
            span.set_attribute("mcp.selection_duration_ms", duration * 1000)
            span.set_attribute("mcp.selected_model", selected_model)
            
            # Add events
            span.addEvent("Model selection started", {
                "mcp.available_models": ",".join(available_models)
            })
            
            span.addEvent("Model selection completed", {
                "mcp.selected_model": selected_model,
                "mcp.duration_ms": duration * 1000
            })
            
            logger.debug(
                "Model selection completed",
                request_id=request_id,
                selected_model=selected_model,
                duration_ms=duration * 1000
            )
            
            span.set_status(Status(StatusCode.OK))
            return selected_model
            
        except Exception as e:
            duration = time.time() - start_time
            
            # Set error status
            span.set_status(Status(StatusCode.ERROR, str(e)))
            span.record_exception(e)
            
            # Add error event
            span.addEvent("Model selection failed", {
                "mcp.error": str(e),
                "mcp.error_type": type(e).__name__,
                "mcp.duration_ms": duration * 1000
            })
            
            logger.error(
                "Model selection failed",
                request_id=request_id,
                error=str(e),
                error_type=type(e).__name__,
                duration_ms=duration * 1000
            )
            
            raise
            
        finally:
            span.end()
    
    async def trace_model_inference(
        self,
        request_id: str,
        model_type: str,
        prompt: str,
        inference_func: callable,
        *args, **kwargs
    ) -> Dict[str, Any]:
        """Trace model inference process"""
        span = self.tracer.start_span(
            "model_inference",
            kind=SpanKind.INTERNAL,
            attributes={
                "mcp.request_id": request_id,
                "mcp.model_type": model_type,
                "mcp.prompt_length": len(prompt),
                "mcp.operation": "model_inference",
                "mcp.service": "model-router"
            }
        )
        
        start_time = time.time()
        
        try:
            # Execute model inference
            result = await inference_func(model_type, prompt, *args, **kwargs)
            
            duration = time.time() - start_time
            
            # Record metrics
            self.model_inference_time.record(duration, {
                "mcp.model_type": model_type
            })
            
            self.token_usage_counter.add(result.get("tokens_used", 0), {
                "mcp.model_type": model_type
            })
            
            self.cost_counter.add(result.get("cost", 0), {
                "mcp.model_type": model_type
            })
            
            # Set span attributes
            span.set_attribute("mcp.inference_success", True)
            span.set_attribute("mcp.inference_duration_ms", duration * 1000)
            span.set_attribute("mcp.tokens_used", result.get("tokens_used", 0))
            span.set_attribute("mcp.cost", result.get("cost", 0))
            span.set_attribute("mcp.response_length", len(result.get("response", "")))
            
            # Add events
            span.addEvent("Model inference started", {
                "mcp.model_type": model_type,
                "mcp.prompt_length": len(prompt)
            })
            
            span.addEvent("Model inference completed", {
                "mcp.duration_ms": duration * 1000,
                "mcp.tokens_used": result.get("tokens_used", 0),
                "mcp.cost": result.get("cost", 0)
            })
            
            logger.debug(
                "Model inference completed",
                request_id=request_id,
                model_type=model_type,
                duration_ms=duration * 1000,
                tokens_used=result.get("tokens_used", 0)
            )
            
            span.set_status(Status(StatusCode.OK))
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            
            # Record error metrics
            self.model_error_counter.add(1, {
                "mcp.model_type": model_type,
                "mcp.error_type": type(e).__name__
            })
            
            # Set error status
            span.set_status(Status(StatusCode.ERROR, str(e)))
            span.record_exception(e)
            
            # Add error event
            span.addEvent("Model inference failed", {
                "mcp.error": str(e),
                "mcp.error_type": type(e).__name__,
                "mcp.duration_ms": duration * 1000
            })
            
            logger.error(
                "Model inference failed",
                request_id=request_id,
                model_type=model_type,
                error=str(e),
                error_type=type(e).__name__,
                duration_ms=duration * 1000
            )
            
            raise
            
        finally:
            span.end()
    
    def record_cache_hit(self, model_type: str):
        """Record a cache hit"""
        self.cache_hit_counter.add(1, {
            "mcp.model_type": model_type
        })
    
    def record_cache_miss(self, model_type: str):
        """Record a cache miss"""
        self.cache_miss_counter.add(1, {
            "mcp.model_type": model_type
        })
```

### 3.2 JavaScript/Node.js Implementation

```javascript
// mcp-model-routing-tracing.js
const { trace, metrics } = require('@opentelemetry/api');
const { SpanKind, SpanStatusCode } = require('@opentelemetry/api');

class ModelRouterTracer {
  constructor() {
    this.tracer = trace.getTracer('mcp-model-router', '1.0.0');
    this.meter = metrics.getMeter('mcp-model-router', '1.0.0');
    
    // Define metrics
    this.routingCounter = this.meter.createCounter('mcp_model_routing_total', {
      description: 'Total number of model routing requests'
    });
    
    this.routingDuration = this.meter.createHistogram('mcp_model_routing_duration_seconds', {
      description: 'Model routing duration in seconds',
      unit: 's'
    });
    
    this.routingSuccessCounter = this.meter.createCounter('mcp_model_routing_success_total', {
      description: 'Total number of successful model routing requests'
    });
    
    this.routingErrorCounter = this.meter.createCounter('mcp_model_routing_errors_total', {
      description: 'Total number of failed model routing requests'
    });
    
    this.activeRoutings = this.meter.createUpDownCounter('mcp_active_model_routings', {
      description: 'Number of active model routing requests'
    });
    
    this.modelSelectionTime = this.meter.createHistogram('mcp_model_selection_time_seconds', {
      description: 'Time taken for model selection',
      unit: 's'
    });
    
    this.modelInferenceTime = this.meter.createHistogram('mcp_model_inference_time_seconds', {
      description: 'Time taken for model inference',
      unit: 's'
    });
    
    this.tokenUsageCounter = this.meter.createCounter('mcp_model_token_usage_total', {
      description: 'Total number of tokens used by models'
    });
    
    this.costCounter = this.meter.createCounter('mcp_model_cost_total', {
      description: 'Total cost incurred by model usage',
      unit: 'USD'
    });
    
    this.cacheHitCounter = this.meter.createCounter('mcp_model_cache_hits_total', {
      description: 'Total number of model cache hits'
    });
    
    this.cacheMissCounter = this.meter.createCounter('mcp_model_cache_misses_total', {
      description: 'Total number of model cache misses'
    });
    
    this.modelUsageCounter = this.meter.createCounter('mcp_model_usage_total', {
      description: 'Total number of requests per model'
    });
    
    this.modelErrorCounter = this.meter.createCounter('mcp_model_errors_total', {
      description: 'Total number of errors per model'
    });
  }
  
  async traceModelRouting(requestId, modelType, prompt, routingFunc) {
    const span = this.tracer.startSpan('model_routing', {
      kind: SpanKind.SERVER,
      attributes: {
        'mcp.request_id': requestId,
        'mcp.model_type': modelType || 'auto',
        'mcp.prompt_length': prompt.length,
        'mcp.operation': 'model_routing',
        'mcp.service': 'model-router'
      }
    });
    
    const startTime = Date.now();
    this.activeRoutings.add(1, {
      'mcp.model_type': modelType || 'auto',
      'mcp.service': 'model-router'
    });
    
    try {
      // Execute model routing
      const result = await routingFunc(requestId, modelType, prompt);
      
      const duration = (Date.now() - startTime) / 1000;
      
      // Record metrics
      this.routingCounter.add(1, {
        'mcp.model_type': result.model_type || modelType || 'unknown',
        'mcp.success': 'true'
      });
      
      this.routingDuration.record(duration, {
        'mcp.model_type': result.model_type || modelType || 'unknown'
      });
      
      this.routingSuccessCounter.add(1, {
        'mcp.model_type': result.model_type || modelType || 'unknown'
      });
      
      this.tokenUsageCounter.add(result.tokens_used || 0, {
        'mcp.model_type': result.model_type || modelType || 'unknown'
      });
      
      this.costCounter.add(result.cost || 0, {
        'mcp.model_type': result.model_type || modelType || 'unknown'
      });
      
      this.modelUsageCounter.add(1, {
        'mcp.model_type': result.model_type || modelType || 'unknown'
      });
      
      // Set span attributes
      span.setAttribute('mcp.routing_success', true);
      span.setAttribute('mcp.routing_duration_ms', duration * 1000);
      span.setAttribute('mcp.selected_model', result.model_type || 'unknown');
      span.setAttribute('mcp.tokens_used', result.tokens_used || 0);
      span.setAttribute('mcp.cost', result.cost || 0);
      span.setAttribute('mcp.cache_hit', result.cache_hit || false);
      span.setAttribute('mcp.response_length', (result.response || '').length);
      
      // Add events
      span.addEvent('Model routing started', {
        'mcp.request_id': requestId,
        'mcp.prompt_length': prompt.length
      });
      
      span.addEvent('Model routing completed', {
        'mcp.selected_model': result.model_type || 'unknown',
        'mcp.duration_ms': duration * 1000,
        'mcp.tokens_used': result.tokens_used || 0,
        'mcp.cache_hit': result.cache_hit || false
      });
      
      console.log(`Model routing completed: ${requestId}, model: ${result.model_type || modelType}, duration: ${duration * 1000}ms`);
      
      span.setStatus({ code: SpanStatusCode.OK });
      return result;
      
    } catch (error) {
      const duration = (Date.now() - startTime) / 1000;
      
      // Record error metrics
      this.routingCounter.add(1, {
        'mcp.model_type': modelType || 'unknown',
        'mcp.success': 'false'
      });
      
      this.routingErrorCounter.add(1, {
        'mcp.model_type': modelType || 'unknown',
        'mcp.error_type': error.constructor.name
      });
      
      if (modelType) {
        this.modelErrorCounter.add(1, {
          'mcp.model_type': modelType,
          'mcp.error_type': error.constructor.name
        });
      }
      
      // Set error status
      span.setStatus({
        code: SpanStatusCode.ERROR,
        message: error.message
      });
      span.recordException(error);
      
      // Add error event
      span.addEvent('Model routing failed', {
        'mcp.error': error.message,
        'mcp.error_type': error.constructor.name,
        'mcp.duration_ms': duration * 1000
      });
      
      console.error(`Model routing failed: ${requestId}, model: ${modelType}, error: ${error.message}`);
      
      throw error;
      
    } finally {
      this.activeRoutings.add(-1, {
        'mcp.model_type': modelType || 'auto',
        'mcp.service': 'model-router'
      });
      span.end();
    }
  }
  
  async traceModelSelection(requestId, availableModels, selectionFunc, ...args) {
    const span = this.tracer.startSpan('model_selection', {
      kind: SpanKind.INTERNAL,
      attributes: {
        'mcp.request_id': requestId,
        'mcp.available_models': availableModels.join(','),
        'mcp.available_model_count': availableModels.length,
        'mcp.operation': 'model_selection',
        'mcp.service': 'model-router'
      }
    });
    
    const startTime = Date.now();
    
    try {
      // Execute model selection
      const selectedModel = await selectionFunc(availableModels, ...args);
      
      const duration = (Date.now() - startTime) / 1000;
      
      // Record metrics
      this.modelSelectionTime.record(duration, {
        'mcp.selected_model': selectedModel
      });
      
      // Set span attributes
      span.setAttribute('mcp.selection_success', true);
      span.setAttribute('mcp.selection_duration_ms', duration * 1000);
      span.setAttribute('mcp.selected_model', selectedModel);
      
      // Add events
      span.addEvent('Model selection started', {
        'mcp.available_models': availableModels.join(',')
      });
      
      span.addEvent('Model selection completed', {
        'mcp.selected_model': selectedModel,
        'mcp.duration_ms': duration * 1000
      });
      
      console.log(`Model selection completed: ${requestId}, model: ${selectedModel}, duration: ${duration * 1000}ms`);
      
      span.setStatus({ code: SpanStatusCode.OK });
      return selectedModel;
      
    } catch (error) {
      const duration = (Date.now() - startTime) / 1000;
      
      // Set error status
      span.setStatus({
        code: SpanStatusCode.ERROR,
        message: error.message
      });
      span.recordException(error);
      
      // Add error event
      span.addEvent('Model selection failed', {
        'mcp.error': error.message,
        'mcp.error_type': error.constructor.name,
        'mcp.duration_ms': duration * 1000
      });
      
      console.error(`Model selection failed: ${requestId}, error: ${error.message}`);
      
      throw error;
      
    } finally {
      span.end();
    }
  }
  
  async traceModelInference(requestId, modelType, prompt, inferenceFunc, ...args) {
    const span = this.tracer.startSpan('model_inference', {
      kind: SpanKind.INTERNAL,
      attributes: {
        'mcp.request_id': requestId,
        'mcp.model_type': modelType,
        'mcp.prompt_length': prompt.length,
        'mcp.operation': 'model_inference',
        'mcp.service': 'model-router'
      }
    });
    
    const startTime = Date.now();
    
    try {
      // Execute model inference
      const result = await inferenceFunc(modelType, prompt, ...args);
      
      const duration = (Date.now() - startTime) / 1000;
      
      // Record metrics
      this.modelInferenceTime.record(duration, {
        'mcp.model_type': modelType
      });
      
      this.tokenUsageCounter.add(result.tokens_used || 0, {
        'mcp.model_type': modelType
      });
      
      this.costCounter.add(result.cost || 0, {
        'mcp.model_type': modelType
      });
      
      // Set span attributes
      span.setAttribute('mcp.inference_success', true);
      span.setAttribute('mcp.inference_duration_ms', duration * 1000);
      span.setAttribute('mcp.tokens_used', result.tokens_used || 0);
      span.setAttribute('mcp.cost', result.cost || 0);
      span.setAttribute('mcp.response_length', (result.response || '').length);
      
      // Add events
      span.addEvent('Model inference started', {
        'mcp.model_type': modelType,
        'mcp.prompt_length': prompt.length
      });
      
      span.addEvent('Model inference completed', {
        'mcp.duration_ms': duration * 1000,
        'mcp.tokens_used': result.tokens_used || 0,
        'mcp.cost': result.cost || 0
      });
      
      console.log(`Model inference completed: ${requestId}, model: ${modelType}, duration: ${duration * 1000}ms`);
      
      span.setStatus({ code: SpanStatusCode.OK });
      return result;
      
    } catch (error) {
      const duration = (Date.now() - startTime) / 1000;
      
      // Record error metrics
      this.modelErrorCounter.add(1, {
        'mcp.model_type': modelType,
        'mcp.error_type': error.constructor.name
      });
      
      // Set error status
      span.setStatus({
        code: SpanStatusCode.ERROR,
        message: error.message
      });
      span.recordException(error);
      
      // Add error event
      span.addEvent('Model inference failed', {
        'mcp.error': error.message,
        'mcp.error_type': error.constructor.name,
        'mcp.duration_ms': duration * 1000
      });
      
      console.error(`Model inference failed: ${requestId}, model: ${modelType}, error: ${error.message}`);
      
      throw error;
      
    } finally {
      span.end();
    }
  }
  
  recordCacheHit(modelType) {
    this.cacheHitCounter.add(1, {
      'mcp.model_type': modelType
    });
  }
  
  recordCacheMiss(modelType) {
    this.cacheMissCounter.add(1, {
      'mcp.model_type': modelType
    });
  }
}

module.exports = ModelRouterTracer;
```

---

## 4. Workflow Execution Instrumentation

### 4.1 Python Implementation

```python
# mcp_workflow_tracing.py
from opentelemetry import trace, metrics
from opentelemetry.trace import Status, StatusCode, SpanKind
from opentelemetry.metrics import Counter, Histogram, UpDownCounter
from typing import Dict, Any, Optional, List
import structlog
import time
import asyncio

logger = structlog.get_logger(__name__)

class WorkflowTracer:
    """Custom tracer for workflow execution operations"""
    
    def __init__(self):
        self.tracer = trace.get_tracer("mcp-workflow-executor", "1.0.0")
        self.meter = metrics.get_meter("mcp-workflow-executor", "1.0.0")
        
        # Define metrics
        self.workflow_counter = self.meter.create_counter(
            "mcp_workflow_execution_total",
            description="Total number of workflow executions"
        )
        
        self.workflow_duration = self.meter.create_histogram(
            "mcp_workflow_execution_duration_seconds",
            description="Workflow execution duration in seconds",
            unit="s"
        )
        
        self.workflow_success_counter = self.meter.create_counter(
            "mcp_workflow_success_total",
            description="Total number of successful workflow executions"
        )
        
        self.workflow_error_counter = self.meter.create_counter(
            "mcp_workflow_errors_total",
            description="Total number of failed workflow executions"
        )
        
        self.active_workflows = self.meter.create_up_down_counter(
            "mcp_active_workflows",
            description="Number of active workflow executions"
        )
        
        self.step_counter = self.meter.create_counter(
            "mcp_workflow_step_total",
            description="Total number of workflow steps executed"
        )
        
        self.step_duration = self.meter.create_histogram(
            "mcp_workflow_step_duration_seconds",
            description="Workflow step duration in seconds",
            unit="s"
        )
        
        self.step_success_counter = self.meter.create_counter(
            "mcp_workflow_step_success_total",
            description="Total number of successful workflow steps"
        )
        
        self.step_error_counter = self.meter.create_counter(
            "mcp_workflow_step_errors_total",
            description="Total number of failed workflow steps"
        )
        
        self.workflow_branch_counter = self.meter.create_counter(
            "mcp_workflow_branch_total",
            description="Total number of workflow branches taken"
        )
        
        self.workflow_retry_counter = self.meter.create_counter(
            "mcp_workflow_retry_total",
            description="Total number of workflow step retries"
        )
        
        self.workflow_rollback_counter = self.meter.create_counter(
            "mcp_workflow_rollback_total",
            description="Total number of workflow rollbacks"
        )
    
    async def trace_workflow_execution(
        self,
        workflow_id: str,
        workflow_type: str,
        steps: List[Dict[str, Any]],
        input_data: Dict[str, Any],
        execution_func: callable
    ) -> Dict[str, Any]:
        """Trace a workflow execution"""
        span = self.tracer.start_span(
            "workflow_execution",
            kind=SpanKind.SERVER,
            attributes={
                "mcp.workflow_id": workflow_id,
                "mcp.workflow_type": workflow_type,
                "mcp.workflow_steps": len(steps),
                "mcp.operation": "workflow_execution",
                "mcp.service": "workflow-orchestrator"
            }
        )
        
        start_time = time.time()
        self.active_workflows.add(1, {
            "mcp.workflow_type": workflow_type,
            "mcp.service": "workflow-orchestrator"
        })
        
        try:
            # Execute workflow
            result = await execution_func(workflow_id, workflow_type, steps, input_data)
            
            duration = time.time() - start_time
            
            # Record metrics
            self.workflow_counter.add(1, {
                "mcp.workflow_type": workflow_type,
                "mcp.success": "true"
            })
            
            self.workflow_duration.record(duration, {
                "mcp.workflow_type": workflow_type
            })
            
            self.workflow_success_counter.add(1, {
                "mcp.workflow_type": workflow_type
            })
            
            # Set span attributes
            span.set_attribute("mcp.workflow_success", True)
            span.set_attribute("mcp.workflow_duration_ms", duration * 1000)
            span.set_attribute("mcp.completed_steps", result.get("completed_steps", 0))
            span.set_attribute("mcp.total_steps", len(steps))
            span.set_attribute("mcp.branches_taken", result.get("branches_taken", 0))
            span.set_attribute("mcp.retries", result.get("retries", 0))
            span.set_attribute("mcp.rollback", result.get("rollback", False))
            
            # Add events
            span.addEvent("Workflow execution started", {
                "mcp.workflow_id": workflow_id,
                "mcp.workflow_type": workflow_type,
                "mcp.steps_count": len(steps)
            })
            
            span.addEvent("Workflow execution completed", {
                "mcp.duration_ms": duration * 1000,
                "mcp.completed_steps": result.get("completed_steps", 0),
                "mcp.branches_taken": result.get("branches_taken", 0),
                "mcp.retries": result.get("retries", 0),
                "mcp.rollback": result.get("rollback", False)
            })
            
            logger.info(
                "Workflow execution completed",
                workflow_id=workflow_id,
                workflow_type=workflow_type,
                duration_ms=duration * 1000,
                completed_steps=result.get("completed_steps", 0),
                total_steps=len(steps)
            )
            
            span.set_status(Status(StatusCode.OK))
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            
            # Record error metrics
            self.workflow_counter.add(1, {
                "mcp.workflow_type": workflow_type,
                "mcp.success": "false"
            })
            
            self.workflow_error_counter.add(1, {
                "mcp.workflow_type": workflow_type,
                "mcp.error_type": type(e).__name__
            })
            
            # Set error status
            span.set_status(Status(StatusCode.ERROR, str(e)))
            span.record_exception(e)
            
            # Add error event
            span.addEvent("Workflow execution failed", {
                "mcp.error": str(e),
                "mcp.error_type": type(e).__name__,
                "mcp.duration_ms": duration * 1000
            })
            
            logger.error(
                "Workflow execution failed",
                workflow_id=workflow_id,
                workflow_type=workflow_type,
                error=str(e),
                error_type=type(e).__name__,
                duration_ms=duration * 1000
            )
            
            raise
            
        finally:
            self.active_workflows.add(-1, {
                "mcp.workflow_type": workflow_type,
                "mcp.service": "workflow-orchestrator"
            })
            span.end()
    
    async def trace_workflow_step(
        self,
        workflow_id: str,
        step_name: str,
        step_type: str,
        step_index: int,
        step_func: callable,
        *args, **kwargs
    ) -> Any:
        """Trace a single workflow step"""
        span = self.tracer.start_span(
            f"workflow_step_{step_name}",
            kind=SpanKind.INTERNAL,
            attributes={
                "mcp.workflow_id": workflow_id,
                "mcp.step_name": step_name,
                "mcp.step_type": step_type,
                "mcp.step_index": step_index,
                "mcp.operation": "workflow_step",
                "mcp.service": "workflow-orchestrator"
            }
        )
        
        start_time = time.time()
        
        try:
            # Execute workflow step
            result = await step_func(*args, **kwargs)
            
            duration = time.time() - start_time
            
            # Record metrics
            self.step_counter.add(1, {
                "mcp.step_type": step_type,
                "mcp.success": "true"
            })
            
            self.step_duration.record(duration, {
                "mcp.step_type": step_type
            })
            
            self.step_success_counter.add(1, {
                "mcp.step_type": step_type
            })
            
            # Set span attributes
            span.set_attribute("mcp.step_success", True)
            span.set_attribute("mcp.step_duration_ms", duration * 1000)
            
            # Add event
            span.addEvent("Workflow step completed", {
                "mcp.duration_ms": duration * 1000
            })
            
            logger.debug(
                "Workflow step completed",
                workflow_id=workflow_id,
                step_name=step_name,
                step_type=step_type,
                duration_ms=duration * 1000
            )
            
            span.set_status(Status(StatusCode.OK))
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            
            # Record error metrics
            self.step_counter.add(1, {
                "mcp.step_type": step_type,
                "mcp.success": "false"
            })
            
            self.step_error_counter.add(1, {
                "mcp.step_type": step_type,
                "mcp.error_type": type(e).__name__
            })
            
            # Set error status
            span.set_status(Status(StatusCode.ERROR, str(e)))
            span.record_exception(e)
            
            # Add error event
            span.addEvent("Workflow step failed", {
                "mcp.error": str(e),
                "mcp.error_type": type(e).__name__,
                "mcp.duration_ms": duration * 1000
            })
            
            logger.error(
                "Workflow step failed",
                workflow_id=workflow_id,
                step_name=step_name,
                step_type=step_type,
                error=str(e),
                error_type=type(e).__name__,
                duration_ms=duration * 1000
            )
            
            raise
            
        finally:
            span.end()
    
    def record_workflow_branch(
        self,
        workflow_id: str,
        branch_name: str,
        condition: str
    ):
        """Record a workflow branch decision"""
        self.workflow_branch_counter.add(1, {
            "mcp.workflow_id": workflow_id,
            "mcp.branch_name": branch_name,
            "mcp.condition": condition
        })
    
    def record_workflow_retry(
        self,
        workflow_id: str,
        step_name: str,
        retry_count: int
    ):
        """Record a workflow step retry"""
        self.workflow_retry_counter.add(1, {
            "mcp.workflow_id": workflow_id,
            "mcp.step_name": step_name,
            "mcp.retry_count": retry_count
        })
    
    def record_workflow_rollback(
        self,
        workflow_id: str,
        reason: str
    ):
        """Record a workflow rollback"""
        self.workflow_rollback_counter.add(1, {
            "mcp.workflow_id": workflow_id,
            "mcp.reason": reason
        })
```

### 4.2 JavaScript/Node.js Implementation

```javascript
// mcp-workflow-tracing.js
const { trace, metrics } = require('@opentelemetry/api');
const { SpanKind, SpanStatusCode } = require('@opentelemetry/api');

class WorkflowTracer {
  constructor() {
    this.tracer = trace.getTracer('mcp-workflow-executor', '1.0.0');
    this.meter = metrics.getMeter('mcp-workflow-executor', '1.0.0');
    
    // Define metrics
    this.workflowCounter = this.meter.createCounter('mcp_workflow_execution_total', {
      description: 'Total number of workflow executions'
    });
    
    this.workflowDuration = this.meter.createHistogram('mcp_workflow_execution_duration_seconds', {
      description: 'Workflow execution duration in seconds',
      unit: 's'
    });
    
    this.workflowSuccessCounter = this.meter.createCounter('mcp_workflow_success_total', {
      description: 'Total number of successful workflow executions'
    });
    
    this.workflowErrorCounter = this.meter.createCounter('mcp_workflow_errors_total', {
      description: 'Total number of failed workflow executions'
    });
    
    this.activeWorkflows = this.meter.createUpDownCounter('mcp_active_workflows', {
      description: 'Number of active workflow executions'
    });
    
    this.stepCounter = this.meter.createCounter('mcp_workflow_step_total', {
      description: 'Total number of workflow steps executed'
    });
    
    this.stepDuration = this.meter.createHistogram('mcp_workflow_step_duration_seconds', {
      description: 'Workflow step duration in seconds',
      unit: 's'
    });
    
    this.stepSuccessCounter = this.meter.createCounter('mcp_workflow_step_success_total', {
      description: 'Total number of successful workflow steps'
    });
    
    this.stepErrorCounter = this.meter.createCounter('mcp_workflow_step_errors_total', {
      description: 'Total number of failed workflow steps'
    });
    
    this.workflowBranchCounter = this.meter.createCounter('mcp_workflow_branch_total', {
      description: 'Total number of workflow branches taken'
    });
    
    this.workflowRetryCounter = this.meter.createCounter('mcp_workflow_retry_total', {
      description: 'Total number of workflow step retries'
    });
    
    this.workflowRollbackCounter = this.meter.createCounter('mcp_workflow_rollback_total', {
      description: 'Total number of workflow rollbacks'
    });
  }
  
  async traceWorkflowExecution(workflowId, workflowType, steps, inputData, executionFunc) {
    const span = this.tracer.startSpan('workflow_execution', {
      kind: SpanKind.SERVER,
      attributes: {
        'mcp.workflow_id': workflowId,
        'mcp.workflow_type': workflowType,
        'mcp.workflow_steps': steps.length,
        'mcp.operation': 'workflow_execution',
        'mcp.service': 'workflow-orchestrator'
      }
    });
    
    const startTime = Date.now();
    this.activeWorkflows.add(1, {
      'mcp.workflow_type': workflowType,
      'mcp.service': 'workflow-orchestrator'
    });
    
    try {
      // Execute workflow
      const result = await executionFunc(workflowId, workflowType, steps, inputData);
      
      const duration = (Date.now() - startTime) / 1000;
      
      // Record metrics
      this.workflowCounter.add(1, {
        'mcp.workflow_type': workflowType,
        'mcp.success': 'true'
      });
      
      this.workflowDuration.record(duration, {
        'mcp.workflow_type': workflowType
      });
      
      this.workflowSuccessCounter.add(1, {
        'mcp.workflow_type': workflowType
      });
      
      // Set span attributes
      span.setAttribute('mcp.workflow_success', true);
      span.setAttribute('mcp.workflow_duration_ms', duration * 1000);
      span.setAttribute('mcp.completed_steps', result.completed_steps || 0);
      span.setAttribute('mcp.total_steps', steps.length);
      span.setAttribute('mcp.branches_taken', result.branches_taken || 0);
      span.setAttribute('mcp.retries', result.retries || 0);
      span.setAttribute('mcp.rollback', result.rollback || false);
      
      // Add events
      span.addEvent('Workflow execution started', {
        'mcp.workflow_id': workflowId,
        'mcp.workflow_type': workflowType,
        'mcp.steps_count': steps.length
      });
      
      span.addEvent('Workflow execution completed', {
        'mcp.duration_ms': duration * 1000,
        'mcp.completed_steps': result.completed_steps || 0,
        'mcp.branches_taken': result.branches_taken || 0,
        'mcp.retries': result.retries || 0,
        'mcp.rollback': result.rollback || false
      });
      
      console.log(`Workflow execution completed: ${workflowId}, type: ${workflowType}, duration: ${duration * 1000}ms`);
      
      span.setStatus({ code: SpanStatusCode.OK });
      return result;
      
    } catch (error) {
      const duration = (Date.now() - startTime) / 1000;
      
      // Record error metrics
      this.workflowCounter.add(1, {
        'mcp.workflow_type': workflowType,
        'mcp.success': 'false'
      });
      
      this.workflowErrorCounter.add(1, {
        'mcp.workflow_type': workflowType,
        'mcp.error_type': error.constructor.name
      });
      
      // Set error status
      span.setStatus({
        code: SpanStatusCode.ERROR,
        message: error.message
      });
      span.recordException(error);
      
      // Add error event
      span.addEvent('Workflow execution failed', {
        'mcp.error': error.message,
        'mcp.error_type': error.constructor.name,
        'mcp.duration_ms': duration * 1000
      });
      
      console.error(`Workflow execution failed: ${workflowId}, type: ${workflowType}, error: ${error.message}`);
      
      throw error;
      
    } finally {
      this.activeWorkflows.add(-1, {
        'mcp.workflow_type': workflowType,
        'mcp.service': 'workflow-orchestrator'
      });
      span.end();
    }
  }
  
  async traceWorkflowStep(workflowId, stepName, stepType, stepIndex, stepFunc, ...args) {
    const span = this.tracer.startSpan(`workflow_step_${stepName}`, {
      kind: SpanKind.INTERNAL,
      attributes: {
        'mcp.workflow_id': workflowId,
        'mcp.step_name': stepName,
        'mcp.step_type': stepType,
        'mcp.step_index': stepIndex,
        'mcp.operation': 'workflow_step',
        'mcp.service': 'workflow-orchestrator'
      }
    });
    
    const startTime = Date.now();
    
    try {
      // Execute workflow step
      const result = await stepFunc(...args);
      
      const duration = (Date.now() - startTime) / 1000;
      
      // Record metrics
      this.stepCounter.add(1, {
        'mcp.step_type': stepType,
        'mcp.success': 'true'
      });
      
      this.stepDuration.record(duration, {
        'mcp.step_type': stepType
      });
      
      this.stepSuccessCounter.add(1, {
        'mcp.step_type': stepType
      });
      
      // Set span attributes
      span.setAttribute('mcp.step_success', true);
      span.setAttribute('mcp.step_duration_ms', duration * 1000);
      
      // Add event
      span.addEvent('Workflow step completed', {
        'mcp.duration_ms': duration * 1000
      });
      
      console.log(`Workflow step completed: ${stepName}, type: ${stepType}, duration: ${duration * 1000}ms`);
      
      span.setStatus({ code: SpanStatusCode.OK });
      return result;
      
    } catch (error) {
      const duration = (Date.now() - startTime) / 1000;
      
      // Record error metrics
      this.stepCounter.add(1, {
        'mcp.step_type': stepType,
        'mcp.success': 'false'
      });
      
      this.stepErrorCounter.add(1, {
        'mcp.step_type': stepType,
        'mcp.error_type': error.constructor.name
      });
      
      // Set error status
      span.setStatus({
        code: SpanStatusCode.ERROR,
        message: error.message
      });
      span.recordException(error);
      
      // Add error event
      span.addEvent('Workflow step failed', {
        'mcp.error': error.message,
        'mcp.error_type': error.constructor.name,
        'mcp.duration_ms': duration * 1000
      });
      
      console.error(`Workflow step failed: ${stepName}, type: ${stepType}, error: ${error.message}`);
      
      throw error;
      
    } finally {
      span.end();
    }
  }
  
  recordWorkflowBranch(workflowId, branchName, condition) {
    this.workflowBranchCounter.add(1, {
      'mcp.workflow_id': workflowId,
      'mcp.branch_name': branchName,
      'mcp.condition': condition
    });
  }
  
  recordWorkflowRetry(workflowId, stepName, retryCount) {
    this.workflowRetryCounter.add(1, {
      'mcp.workflow_id': workflowId,
      'mcp.step_name': stepName,
      'mcp.retry_count': retryCount
    });
  }
  
  recordWorkflowRollback(workflowId, reason) {
    this.workflowRollbackCounter.add(1, {
      'mcp.workflow_id': workflowId,
      'mcp.reason': reason
    });
  }
}

module.exports = WorkflowTracer;
```

---

## 5. Integration Examples

### 5.1 Python Integration