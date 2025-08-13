"""
Model Router Application Performance Monitoring (APM) implementation.
Provides comprehensive performance monitoring for model selection, routing, and LLM operations.
"""

import logging
import time
from typing import Dict, Any, Optional, List
from contextlib import asynccontextmanager
from dataclasses import dataclass
from enum import Enum
from collections import defaultdict
import statistics
import json

from opentelemetry.trace import Status, StatusCode

from src.common.apm import (
    APMOperationType, 
    APMConfig, 
    get_apm
)
from src.common.tracing import get_tracing_config

logger = logging.getLogger(__name__)


class ModelRouterOperationType(Enum):
    """Model Router specific operation types."""
    MODEL_SELECTION = "model_selection"
    MODEL_REQUEST = "model_request"
    ENSEMBLE_ROUTING = "ensemble_routing"
    ADAPTIVE_ROUTING = "adaptive_routing"
    TOKEN_USAGE = "token_usage"
    HEALTH_CHECK = "health_check"
    CACHE_OPERATION = "cache_operation"
    LOAD_BALANCING = "load_balancing"
    FALLBACK_HANDLING = "fallback_handling"


@dataclass
class ModelPerformanceMetrics:
    """Model-specific performance metrics."""
    model_name: str
    request_count: int = 0
    success_count: int = 0
    error_count: int = 0
    total_duration: float = 0.0
    total_tokens: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    cache_hit_count: int = 0
    cache_miss_count: int = 0
    last_used: float = 0.0
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.request_count == 0:
            return 0.0
        return self.success_count / self.request_count
    
    @property
    def error_rate(self) -> float:
        """Calculate error rate."""
        if self.request_count == 0:
            return 0.0
        return self.error_count / self.request_count
    
    @property
    def average_duration(self) -> float:
        """Calculate average duration."""
        if self.request_count == 0:
            return 0.0
        return self.total_duration / self.request_count
    
    @property
    def average_tokens_per_request(self) -> float:
        """Calculate average tokens per request."""
        if self.request_count == 0:
            return 0.0
        return self.total_tokens / self.request_count
    
    @property
    def cache_hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total_cache_ops = self.cache_hit_count + self.cache_miss_count
        if total_cache_ops == 0:
            return 0.0
        return self.cache_hit_count / total_cache_ops


@dataclass
class RoutingDecisionMetrics:
    """Routing decision metrics."""
    decision_type: str
    selected_model: str
    candidate_models: List[str]
    decision_duration: float
    confidence_score: float
    reasoning: str
    context_size: int
    success: bool = True
    error_message: Optional[str] = None


class ModelRouterAPM:
    """APM implementation for Model Router service."""
    
    def __init__(self, config: APMConfig = None):
        """Initialize Model Router APM."""
        self.config = config or APMConfig()
        self.apm = get_apm()
        self.tracer = get_tracing_config().get_tracer()
        self.meter = get_tracing_config().get_meter()
        
        # Model performance tracking
        self.model_metrics = defaultdict(lambda: ModelPerformanceMetrics(model_name=""))
        
        # Initialize metrics
        self._initialize_metrics()
        
        # Routing decision history
        self.routing_decisions = []
        self.max_routing_history = 1000
        
        # Performance thresholds
        self.slow_model_threshold = 5.0  # seconds
        self.high_error_threshold = 0.1  # 10%
        self.low_confidence_threshold = 0.5  # 50%
    
    def _initialize_metrics(self):
        """Initialize OpenTelemetry metrics for Model Router."""
        # Counters
        self.model_requests_counter = self.meter.create_counter(
            "model_router_model_requests_total",
            description="Total number of model requests"
        )
        
        self.routing_decisions_counter = self.meter.create_counter(
            "model_router_routing_decisions_total",
            description="Total number of routing decisions"
        )
        
        self.token_usage_counter = self.meter.create_counter(
            "model_router_token_usage_total",
            description="Total token usage"
        )
        
        self.cache_operations_counter = self.meter.create_counter(
            "model_router_cache_operations_total",
            description="Total cache operations"
        )
        
        self.fallback_operations_counter = self.meter.create_counter(
            "model_router_fallback_operations_total",
            description="Total fallback operations"
        )
        
        # Histograms
        self.model_request_duration = self.meter.create_histogram(
            "model_router_request_duration_seconds",
            description="Duration of model requests"
        )
        
        self.routing_decision_duration = self.meter.create_histogram(
            "model_router_decision_duration_seconds",
            description="Duration of routing decisions"
        )
        
        self.token_processing_rate = self.meter.create_histogram(
            "model_router_tokens_per_second",
            description="Token processing rate"
        )
        
        self.confidence_score_histogram = self.meter.create_histogram(
            "model_router_confidence_score",
            description="Confidence scores for routing decisions"
        )
        
        # Gauges
        self.active_models_gauge = self.meter.create_up_down_counter(
            "model_router_active_models",
            description="Number of currently active models"
        )
        
        self.model_queue_size_gauge = self.meter.create_up_down_counter(
            "model_router_queue_size",
            description="Current queue size for each model"
        )
    
    @asynccontextmanager
    async def trace_model_selection(self, input_text: str, candidate_models: List[str],
                                 context: Optional[Dict[str, Any]] = None):
        """Trace model selection process."""
        operation_name = "model_selection"
        attributes = {
            "model_router.input_length": len(input_text),
            "model_router.candidate_models": ",".join(candidate_models),
            "model_router.has_context": context is not None
        }
        
        start_time = time.time()
        selected_model = None
        confidence_score = 0.0
        reasoning = ""
        success = True
        error_message = None
        
        async with self.apm.trace_async_operation(
            operation_name, APMOperationType.BUSINESS_TRANSACTION, attributes
        ) as span:
            try:
                yield span
            except Exception as e:
                success = False
                error_message = str(e)
                span.set_status(Status(StatusCode.ERROR, error_message))
                span.record_exception(e)
                raise
            finally:
                end_time = time.time()
                duration = end_time - start_time
                
                # Record routing decision metrics
                if selected_model:
                    routing_metrics = RoutingDecisionMetrics(
                        decision_type="model_selection",
                        selected_model=selected_model,
                        candidate_models=candidate_models,
                        decision_duration=duration,
                        confidence_score=confidence_score,
                        reasoning=reasoning,
                        context_size=len(json.dumps(context)) if context else 0,
                        success=success,
                        error_message=error_message
                    )
                    self._record_routing_decision(routing_metrics)
                
                # Update metrics
                self._update_model_selection_metrics(
                    selected_model, duration, confidence_score, success
                )
    
    @asynccontextmanager
    async def trace_model_request(self, model_name: str, operation: str,
                                input_text: str, output_text: str = None,
                                input_tokens: int = 0, output_tokens: int = 0):
        """Trace a request to a specific model."""
        operation_name = f"{model_name}_{operation}"
        attributes = {
            "llm.model_name": model_name,
            "llm.operation": operation,
            "llm.input_length": len(input_text),
            "llm.input_tokens": input_tokens
        }
        
        if output_text:
            attributes["llm.output_length"] = len(output_text)
            attributes["llm.output_tokens"] = output_tokens
        
        start_time = time.time()
        success = True
        error_message = None
        
        async with self.apm.trace_async_operation(
            operation_name, APMOperationType.EXTERNAL_API, attributes
        ) as span:
            try:
                yield span
            except Exception as e:
                success = False
                error_message = str(e)
                span.set_status(Status(StatusCode.ERROR, error_message))
                span.record_exception(e)
                raise
            finally:
                end_time = time.time()
                duration = end_time - start_time
                
                # Update model metrics
                self._update_model_metrics(
                    model_name, duration, success, input_tokens, output_tokens
                )
    
    @asynccontextmanager
    async def trace_ensemble_routing(self, request_text: str, models: List[str],
                                   weights: Optional[Dict[str, float]] = None):
        """Trace ensemble routing operations."""
        operation_name = "ensemble_routing"
        attributes = {
            "model_router.ensemble_models": len(models),
            "model_router.models": ",".join(models),
            "model_router.input_length": len(request_text),
            "model_router.has_weights": weights is not None
        }
        
        start_time = time.time()
        success = True
        error_message = None
        
        async with self.apm.trace_async_operation(
            operation_name, APMOperationType.BUSINESS_TRANSACTION, attributes
        ) as span:
            try:
                yield span
            except Exception as e:
                success = False
                error_message = str(e)
                span.set_status(Status(StatusCode.ERROR, error_message))
                span.record_exception(e)
                raise
            finally:
                end_time = time.time()
                duration = end_time - start_time
                
                # Update metrics
                self.routing_decisions_counter.add(1, {
                    "decision_type": "ensemble",
                    "success": success
                })
                
                self.routing_decision_duration.record(duration, {
                    "decision_type": "ensemble"
                })
    
    @asynccontextmanager
    async def trace_adaptive_routing(self, request_text: str, context_size: int = 0):
        """Trace adaptive routing operations."""
        operation_name = "adaptive_routing"
        attributes = {
            "model_router.input_length": len(request_text),
            "model_router.context_size": context_size
        }
        
        start_time = time.time()
        success = True
        error_message = None
        
        async with self.apm.trace_async_operation(
            operation_name, APMOperationType.BUSINESS_TRANSACTION, attributes
        ) as span:
            try:
                yield span
            except Exception as e:
                success = False
                error_message = str(e)
                span.set_status(Status(StatusCode.ERROR, error_message))
                span.record_exception(e)
                raise
            finally:
                end_time = time.time()
                duration = end_time - start_time
                
                # Update metrics
                self.routing_decisions_counter.add(1, {
                    "decision_type": "adaptive",
                    "success": success
                })
                
                self.routing_decision_duration.record(duration, {
                    "decision_type": "adaptive"
                })
    
    @asynccontextmanager
    async def trace_cache_operation(self, operation: str, cache_key: str,
                                  hit: bool = None, size: int = 0):
        """Trace cache operations."""
        operation_name = f"cache_{operation}"
        attributes = {
            "cache.operation": operation,
            "cache.key": cache_key,
            "cache.size": size
        }
        
        if hit is not None:
            attributes["cache.hit"] = hit
        
        start_time = time.time()
        success = True
        error_message = None
        
        async with self.apm.trace_async_operation(
            operation_name, APMOperationType.CPU_INTENSIVE, attributes
        ) as span:
            try:
                yield span
            except Exception as e:
                success = False
                error_message = str(e)
                span.set_status(Status(StatusCode.ERROR, error_message))
                span.record_exception(e)
                raise
            finally:
                end_time = time.time()
                duration = end_time - start_time
                
                # Update cache metrics
                self.cache_operations_counter.add(1, {
                    "operation": operation,
                    "hit": hit,
                    "success": success
                })
    
    @asynccontextmanager
    async def trace_health_check(self, model_name: str, check_type: str = "readiness"):
        """Trace model health check operations."""
        operation_name = f"health_check_{model_name}"
        attributes = {
            "health_check.model": model_name,
            "health_check.type": check_type
        }
        
        start_time = time.time()
        success = True
        error_message = None
        
        async with self.apm.trace_async_operation(
            operation_name, APMOperationType.HTTP_REQUEST, attributes
        ) as span:
            try:
                yield span
            except Exception as e:
                success = False
                error_message = str(e)
                span.set_status(Status(StatusCode.ERROR, error_message))
                span.record_exception(e)
                raise
            finally:
                end_time = time.time()
                duration = end_time - start_time
                
                # Update model metrics
                model_metrics = self.model_metrics[model_name]
                model_metrics.request_count += 1
                if success:
                    model_metrics.success_count += 1
                else:
                    model_metrics.error_count += 1
                model_metrics.total_duration += duration
                model_metrics.last_used = end_time
    
    def _update_model_selection_metrics(self, selected_model: str, duration: float,
                                      confidence_score: float, success: bool):
        """Update model selection metrics."""
        self.routing_decisions_counter.add(1, {
            "decision_type": "model_selection",
            "success": success
        })
        
        self.routing_decision_duration.record(duration, {
            "decision_type": "model_selection"
        })
        
        self.confidence_score_histogram.record(confidence_score, {
            "decision_type": "model_selection"
        })
    
    def _update_model_metrics(self, model_name: str, duration: float, success: bool,
                            input_tokens: int, output_tokens: int):
        """Update model performance metrics."""
        model_metrics = self.model_metrics[model_name]
        model_metrics.model_name = model_name
        model_metrics.request_count += 1
        model_metrics.total_duration += duration
        model_metrics.total_tokens += input_tokens + output_tokens
        model_metrics.total_input_tokens += input_tokens
        model_metrics.total_output_tokens += output_tokens
        model_metrics.last_used = time.time()
        
        if success:
            model_metrics.success_count += 1
        else:
            model_metrics.error_count += 1
        
        # Update OpenTelemetry metrics
        self.model_requests_counter.add(1, {
            "model": model_name,
            "success": success
        })
        
        self.model_request_duration.record(duration, {
            "model": model_name
        })
        
        self.token_usage_counter.add(input_tokens, {
            "model": model_name,
            "token_type": "input"
        })
        
        self.token_usage_counter.add(output_tokens, {
            "model": model_name,
            "token_type": "output"
        })
        
        # Calculate token processing rate
        if duration > 0:
            token_rate = (input_tokens + output_tokens) / duration
            self.token_processing_rate.record(token_rate, {
                "model": model_name
            })
    
    def _record_routing_decision(self, metrics: RoutingDecisionMetrics):
        """Record routing decision metrics."""
        self.routing_decisions.append(metrics)
        
        # Keep only recent decisions
        if len(self.routing_decisions) > self.max_routing_history:
            self.routing_decisions.pop(0)
    
    def get_model_performance_summary(self, model_name: str = None) -> Dict[str, Any]:
        """Get performance summary for models."""
        if model_name:
            metrics = self.model_metrics.get(model_name)
            if not metrics:
                return {"model_name": model_name, "message": "No data available"}
            
            return {
                "model_name": model_name,
                "request_count": metrics.request_count,
                "success_rate": metrics.success_rate,
                "error_rate": metrics.error_rate,
                "average_duration": metrics.average_duration,
                "average_tokens_per_request": metrics.average_tokens_per_request,
                "cache_hit_rate": metrics.cache_hit_rate,
                "last_used": metrics.last_used
            }
        else:
            # Return summary for all models
            summary = {}
            for model_name, metrics in self.model_metrics.items():
                if metrics.request_count > 0:
                    summary[model_name] = self.get_model_performance_summary(model_name)
            return summary
    
    def get_routing_decision_summary(self) -> Dict[str, Any]:
        """Get routing decision summary."""
        if not self.routing_decisions:
            return {"message": "No routing decisions recorded"}
        
        decisions = self.routing_decisions
        total_decisions = len(decisions)
        successful_decisions = sum(1 for d in decisions if d.success)
        
        # Calculate average decision duration
        avg_duration = statistics.mean(d.decision_duration for d in decisions)
        
        # Calculate average confidence score
        avg_confidence = statistics.mean(d.confidence_score for d in decisions)
        
        # Get most selected models
        model_selections = defaultdict(int)
        for d in decisions:
            model_selections[d.selected_model] += 1
        
        top_models = sorted(model_selections.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            "total_decisions": total_decisions,
            "success_rate": successful_decisions / total_decisions if total_decisions > 0 else 0,
            "average_decision_duration": avg_duration,
            "average_confidence_score": avg_confidence,
            "top_selected_models": top_models,
            "decision_types": {
                "model_selection": sum(1 for d in decisions if d.decision_type == "model_selection"),
                "ensemble": sum(1 for d in decisions if d.decision_type == "ensemble"),
                "adaptive": sum(1 for d in decisions if d.decision_type == "adaptive")
            }
        }
    
    def get_performance_insights(self) -> List[Dict[str, Any]]:
        """Get performance insights and recommendations."""
        insights = []
        
        # Analyze model performance
        for model_name, metrics in self.model_metrics.items():
            if metrics.request_count == 0:
                continue
            
            # Check for slow models
            if metrics.average_duration > self.slow_model_threshold:
                insights.append({
                    "type": "slow_model",
                    "model": model_name,
                    "severity": "warning",
                    "message": f"Model {model_name} has slow response time ({metrics.average_duration:.2f}s)",
                    "recommendation": "Consider using a faster model or optimizing prompts"
                })
            
            # Check for high error rates
            if metrics.error_rate > self.high_error_threshold:
                insights.append({
                    "type": "high_error_rate",
                    "model": model_name,
                    "severity": "error",
                    "message": f"Model {model_name} has high error rate ({metrics.error_rate:.2%})",
                    "recommendation": "Check model health and consider fallback models"
                })
            
            # Check for low cache hit rate
            if metrics.cache_hit_rate < 0.5 and (metrics.cache_hit_count + metrics.cache_miss_count) > 10:
                insights.append({
                    "type": "low_cache_hit_rate",
                    "model": model_name,
                    "severity": "info",
                    "message": f"Model {model_name} has low cache hit rate ({metrics.cache_hit_rate:.2%})",
                    "recommendation": "Consider adjusting cache strategy or TTL"
                })
        
        # Analyze routing decisions
        if self.routing_decisions:
            recent_decisions = self.routing_decisions[-100:]  # Last 100 decisions
            low_confidence_decisions = [d for d in recent_decisions if d.confidence_score < self.low_confidence_threshold]
            
            if len(low_confidence_decisions) > 10:  # More than 10 low confidence decisions
                insights.append({
                    "type": "low_confidence_routing",
                    "severity": "warning",
                    "message": f"High number of low confidence routing decisions ({len(low_confidence_decisions)} in last 100)",
                    "recommendation": "Review routing logic and improve decision criteria"
                })
        
        return insights
    
    def record_cache_metrics(self, model_name: str, hit: bool, operation: str = "get"):
        """Record cache operation metrics."""
        model_metrics = self.model_metrics[model_name]
        
        if hit:
            model_metrics.cache_hit_count += 1
        else:
            model_metrics.cache_miss_count += 1
        
        # Update OpenTelemetry metrics
        self.cache_operations_counter.add(1, {
            "model": model_name,
            "operation": operation,
            "hit": hit
        })
    
    def record_fallback_operation(self, original_model: str, fallback_model: str,
                                reason: str, success: bool):
        """Record fallback operation metrics."""
        self.fallback_operations_counter.add(1, {
            "original_model": original_model,
            "fallback_model": fallback_model,
            "reason": reason,
            "success": success
        })
    
    def set_selected_model(self, model_name: str, confidence_score: float, reasoning: str):
        """Set the selected model for the current operation."""
        # Record selection details for downstream spans/metrics
        self.selected_model = model_name
        self.selected_model_confidence = confidence_score
        self.selected_model_reasoning = reasoning


# Global instance
model_router_apm = None


def get_model_router_apm() -> ModelRouterAPM:
    """Get the global Model Router APM instance."""
    global model_router_apm
    if model_router_apm is None:
        model_router_apm = ModelRouterAPM()
    return model_router_apm


def initialize_model_router_apm(config: APMConfig = None):
    """Initialize the global Model Router APM instance."""
    global model_router_apm
    model_router_apm = ModelRouterAPM(config)
    return model_router_apm


# Decorators for Model Router operations
def trace_model_selection(operation_name: str = None):
    """Decorator to trace model selection operations."""
    def decorator(func):
        name = operation_name or f"model_selection.{func.__name__}"
        
        async def async_wrapper(*args, **kwargs):
            apm = get_model_router_apm()
            
            # Extract parameters
            input_text = kwargs.get('input_text', '')
            candidate_models = kwargs.get('candidate_models', [])
            context = kwargs.get('context', None)
            
            async with apm.trace_model_selection(input_text, candidate_models, context) as span:
                return await func(*args, **kwargs)
        
        return async_wrapper
    
    return decorator


def trace_model_request(model_name: str, operation: str = "generate"):
    """Decorator to trace model requests."""
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            apm = get_model_router_apm()
            
            # Extract parameters
            input_text = kwargs.get('input_text', '')
            input_tokens = kwargs.get('input_tokens', 0)
            
            async with apm.trace_model_request(model_name, operation, input_text, input_tokens=input_tokens) as span:
                result = await func(*args, **kwargs)
                
                # Extract output information if available
                if isinstance(result, dict):
                    output_text = result.get('text', '')
                    output_tokens = result.get('output_tokens', 0)
                    span.set_attribute("llm.output_length", len(output_text))
                    span.set_attribute("llm.output_tokens", output_tokens)
                
                return result
        
        return async_wrapper
    
    return decorator


def trace_ensemble_operation(operation_name: str = "ensemble"):
    """Decorator to trace ensemble operations."""
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            apm = get_model_router_apm()
            
            # Extract parameters
            request_text = kwargs.get('request_text', '')
            models = kwargs.get('models', [])
            weights = kwargs.get('weights', None)
            
            async with apm.trace_ensemble_routing(request_text, models, weights) as span:
                return await func(*args, **kwargs)
        
        return async_wrapper
    
    return decorator
