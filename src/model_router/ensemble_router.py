"""Advanced Multi-Model Ensemble Intelligence Router."""

import asyncio
import numpy as np
from datetime import datetime
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
from enum import Enum

from ..common.logging import get_logger
from .models import ModelRequest, ModelResponse
from .claude_client import ClaudeClient

logger = get_logger("ensemble_router")


class TaskComplexity(str, Enum):
    """Task complexity levels for routing decisions."""

    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    CRITICAL = "critical"


@dataclass
class ModelPrediction:
    """Individual model prediction with confidence."""

    model_id: str
    response: str
    confidence: float
    latency: float
    tokens_used: int
    timestamp: datetime


@dataclass
class EnsembleResult:
    """Ensemble routing result with consensus data."""

    final_response: str
    consensus_confidence: float
    participating_models: List[str]
    prediction_details: List[ModelPrediction]
    routing_strategy: str
    processing_time: float


class PerformanceTracker:
    """Tracks real-time model performance metrics."""

    def __init__(self):
        self.performance_history: Dict[str, List[Dict]] = {}
        self.window_size = 100  # Track last 100 requests per model

    def record_performance(self, model_id: str, metrics: Dict[str, Any]):
        """Record performance metrics for a model."""
        if model_id not in self.performance_history:
            self.performance_history[model_id] = []

        self.performance_history[model_id].append(
            {
                "timestamp": datetime.utcnow(),
                "accuracy": metrics.get("accuracy", 0.0),
                "latency": metrics.get("latency", 0.0),
                "error_rate": metrics.get("error_rate", 0.0),
                "tokens_per_second": metrics.get("tokens_per_second", 0.0),
            }
        )

        # Keep only recent history
        if len(self.performance_history[model_id]) > self.window_size:
            self.performance_history[model_id] = self.performance_history[model_id][
                -self.window_size :
            ]

    def get_current_metrics(self, model_id: str) -> Dict[str, float]:
        """Get current performance metrics for a model."""
        if (
            model_id not in self.performance_history
            or not self.performance_history[model_id]
        ):
            return {
                "avg_accuracy": 0.85,  # Default values
                "avg_latency": 1.0,
                "error_rate": 0.05,
                "tokens_per_second": 50.0,
            }

        recent_data = self.performance_history[model_id][-20:]  # Last 20 requests

        return {
            "avg_accuracy": np.mean([d["accuracy"] for d in recent_data]),
            "avg_latency": np.mean([d["latency"] for d in recent_data]),
            "error_rate": np.mean([d["error_rate"] for d in recent_data]),
            "tokens_per_second": np.mean([d["tokens_per_second"] for d in recent_data]),
        }


class DynamicWeights:
    """Dynamic weight calculation for model selection."""

    def __init__(self):
        self.base_weights = {
            "claude-3-5-sonnet": 0.4,
            "claude-3-opus": 0.3,
            "claude-3-haiku": 0.2,
            "gpt-4": 0.1,
        }

    def calculate_best_model(
        self, task: ModelRequest, performance_data: Dict[str, Dict]
    ) -> str:
        """Calculate the best model for a task based on current performance."""
        task_complexity = self._assess_complexity(task)

        scores = {}
        for model_id, base_weight in self.base_weights.items():
            if model_id in performance_data:
                metrics = performance_data[model_id]

                # Calculate composite score
                accuracy_score = metrics["avg_accuracy"] * 0.4
                speed_score = (1.0 / max(metrics["avg_latency"], 0.1)) * 0.3
                reliability_score = (1.0 - metrics["error_rate"]) * 0.2
                efficiency_score = (metrics["tokens_per_second"] / 100.0) * 0.1

                composite_score = (
                    accuracy_score + speed_score + reliability_score + efficiency_score
                )

                # Adjust based on task complexity
                if task_complexity == TaskComplexity.CRITICAL:
                    composite_score *= 1.2 if "opus" in model_id.lower() else 0.9
                elif task_complexity == TaskComplexity.SIMPLE:
                    composite_score *= 1.1 if "haiku" in model_id.lower() else 0.95

                scores[model_id] = composite_score * base_weight
            else:
                scores[model_id] = base_weight * 0.5  # Penalty for no data

        return max(scores.items(), key=lambda x: x[1])[0]

    def _assess_complexity(self, task: ModelRequest) -> TaskComplexity:
        """Assess task complexity based on various factors."""
        complexity_indicators = 0

        # Check prompt length
        if len(task.messages[0].get("content", "")) > 2000:
            complexity_indicators += 1

        # Check for code-related keywords
        code_keywords = [
            "function",
            "class",
            "algorithm",
            "optimize",
            "refactor",
            "debug",
        ]
        if any(
            keyword in task.messages[0].get("content", "").lower()
            for keyword in code_keywords
        ):
            complexity_indicators += 1

        # Check for critical keywords
        critical_keywords = [
            "security",
            "critical",
            "production",
            "compliance",
            "audit",
        ]
        if any(
            keyword in task.messages[0].get("content", "").lower()
            for keyword in critical_keywords
        ):
            complexity_indicators += 2

        if complexity_indicators >= 3:
            return TaskComplexity.CRITICAL
        elif complexity_indicators >= 2:
            return TaskComplexity.COMPLEX
        elif complexity_indicators >= 1:
            return TaskComplexity.MODERATE
        else:
            return TaskComplexity.SIMPLE


class EnsembleModelRouter:
    """Advanced ensemble model router with consensus capabilities."""

    def __init__(self):
        self.claude_client = ClaudeClient()
        self.performance_tracker = PerformanceTracker()
        self.dynamic_weights = DynamicWeights()
        self.confidence_threshold = 0.85

        # Model configurations
        self.available_models = {
            "claude-3-5-sonnet": {"max_tokens": 4096, "speciality": "general"},
            "claude-3-opus": {"max_tokens": 4096, "speciality": "complex_reasoning"},
            "claude-3-haiku": {"max_tokens": 4096, "speciality": "speed"},
        }

    async def route_with_consensus(
        self, task: ModelRequest, confidence_threshold: float = 0.85
    ) -> EnsembleResult:
        """Route task with ensemble consensus for high-confidence results."""
        start_time = datetime.utcnow()

        task_complexity = self.dynamic_weights._assess_complexity(task)

        if task_complexity == TaskComplexity.CRITICAL:
            logger.info(f"Using consensus routing for critical task: {task.request_id}")
            result = await self._consensus_routing(task, confidence_threshold)
        else:
            logger.info(
                f"Using single model routing for {task_complexity.value} task: {task.request_id}"
            )
            result = await self._single_model_routing(task)

        processing_time = (datetime.utcnow() - start_time).total_seconds()
        result.processing_time = processing_time

        # Record performance metrics
        for prediction in result.prediction_details:
            await self._record_model_performance(prediction, task_complexity)

        return result

    async def _consensus_routing(
        self, task: ModelRequest, confidence_threshold: float
    ) -> EnsembleResult:
        """Use multiple models for consensus on critical tasks."""
        # Select top 3 models for consensus

        # Get predictions from multiple models
        predictions = await self._get_multi_model_predictions(
            task, list(self.available_models.keys())[:3]
        )

        # Calculate consensus
        consensus_response, consensus_confidence = self._calculate_consensus(
            predictions
        )

        return EnsembleResult(
            final_response=consensus_response,
            consensus_confidence=consensus_confidence,
            participating_models=[p.model_id for p in predictions],
            prediction_details=predictions,
            routing_strategy="consensus",
            processing_time=0.0,  # Will be set by caller
        )

    async def _single_model_routing(self, task: ModelRequest) -> EnsembleResult:
        """Route to single best model for non-critical tasks."""
        # Get current performance data
        performance_data = {
            model_id: self.performance_tracker.get_current_metrics(model_id)
            for model_id in self.available_models.keys()
        }

        # Select best model
        best_model = self.dynamic_weights.calculate_best_model(task, performance_data)

        # Get prediction
        prediction = await self._get_model_prediction(task, best_model)

        return EnsembleResult(
            final_response=prediction.response,
            consensus_confidence=prediction.confidence,
            participating_models=[best_model],
            prediction_details=[prediction],
            routing_strategy="single_best",
            processing_time=0.0,  # Will be set by caller
        )

    async def _get_multi_model_predictions(
        self, task: ModelRequest, model_ids: List[str]
    ) -> List[ModelPrediction]:
        """Get predictions from multiple models concurrently."""
        tasks = [self._get_model_prediction(task, model_id) for model_id in model_ids]
        predictions = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions
        valid_predictions = [p for p in predictions if isinstance(p, ModelPrediction)]

        return valid_predictions

    async def _get_model_prediction(
        self, task: ModelRequest, model_id: str
    ) -> ModelPrediction:
        """Get prediction from a specific model."""
        start_time = datetime.utcnow()

        try:
            # Create model-specific request
            model_task = ModelRequest(
                messages=task.messages,
                model=model_id,
                max_tokens=self.available_models[model_id]["max_tokens"],
                temperature=task.temperature,
                request_id=f"{task.request_id}_{model_id}",
            )

            # Get response from Claude client
            response = await self.claude_client.generate_response(model_task)

            latency = (datetime.utcnow() - start_time).total_seconds()

            # Calculate confidence score (simplified implementation)
            confidence = self._calculate_confidence(response.result, model_id)

            return ModelPrediction(
                model_id=model_id,
                response=response.result,
                confidence=confidence,
                latency=latency,
                tokens_used=response.usage.get("total_tokens", 0),
                timestamp=datetime.utcnow(),
            )

        except Exception as e:
            logger.error(f"Error getting prediction from {model_id}: {e}")

            # Return fallback prediction
            return ModelPrediction(
                model_id=model_id,
                response=f"Error: {str(e)}",
                confidence=0.0,
                latency=(datetime.utcnow() - start_time).total_seconds(),
                tokens_used=0,
                timestamp=datetime.utcnow(),
            )

    def _calculate_confidence(self, response: str, model_id: str) -> float:
        """Calculate confidence score for a response."""
        # Simplified confidence calculation
        base_confidence = 0.8

        # Adjust based on response length (longer responses might be more detailed)
        length_factor = min(len(response) / 1000, 1.0) * 0.1

        # Adjust based on model type
        model_factor = 0.1 if "opus" in model_id.lower() else 0.05

        # Check for uncertainty indicators
        uncertainty_keywords = ["maybe", "might", "possibly", "not sure", "unclear"]
        uncertainty_penalty = sum(
            0.02 for keyword in uncertainty_keywords if keyword in response.lower()
        )

        confidence = (
            base_confidence + length_factor + model_factor - uncertainty_penalty
        )

        return max(0.0, min(1.0, confidence))

    def _calculate_consensus(
        self, predictions: List[ModelPrediction]
    ) -> Tuple[str, float]:
        """Calculate consensus from multiple predictions."""
        if not predictions:
            return "No valid predictions available", 0.0

        # Weight predictions by confidence
        weighted_responses = []
        total_weight = 0.0

        for prediction in predictions:
            weight = prediction.confidence
            weighted_responses.append((prediction.response, weight))
            total_weight += weight

        if total_weight == 0:
            return predictions[0].response, 0.0

        # For now, return the highest confidence response
        # In a more sophisticated implementation, we would use semantic similarity
        best_prediction = max(predictions, key=lambda p: p.confidence)

        # Calculate consensus confidence as average of all confidences
        consensus_confidence = np.mean([p.confidence for p in predictions])

        return best_prediction.response, consensus_confidence

    async def _record_model_performance(
        self, prediction: ModelPrediction, complexity: TaskComplexity
    ):
        """Record performance metrics for a model prediction."""
        # Simplified accuracy assessment based on confidence and complexity
        accuracy = prediction.confidence
        if complexity == TaskComplexity.CRITICAL:
            accuracy *= 0.9  # More conservative accuracy for critical tasks

        error_rate = 1.0 - prediction.confidence
        tokens_per_second = prediction.tokens_used / max(prediction.latency, 0.1)

        metrics = {
            "accuracy": accuracy,
            "latency": prediction.latency,
            "error_rate": error_rate,
            "tokens_per_second": tokens_per_second,
        }

        self.performance_tracker.record_performance(prediction.model_id, metrics)


class AdaptiveModelRouter:
    """Real-time adaptive model router with performance-based routing."""

    def __init__(self):
        self.performance_tracker = PerformanceTracker()
        self.routing_weights = DynamicWeights()
        self.claude_client = ClaudeClient()

    async def adaptive_route(self, task: ModelRequest) -> ModelResponse:
        """Route task adaptively based on real-time performance metrics."""
        # Get current performance metrics for all models
        current_performance = {}
        for model_id in self.routing_weights.base_weights.keys():
            current_performance[model_id] = (
                self.performance_tracker.get_current_metrics(model_id)
            )

        # Calculate optimal model
        optimal_model = self.routing_weights.calculate_best_model(
            task, current_performance
        )

        logger.info(
            f"Adaptive routing selected {optimal_model} for task {task.request_id}"
        )

        # Update task model
        task.model = optimal_model

        # Route to selected model
        start_time = datetime.utcnow()
        response = await self.claude_client.generate_response(task)
        end_time = datetime.utcnow()

        # Record performance
        latency = (end_time - start_time).total_seconds()
        confidence = self._estimate_response_quality(response.result)

        metrics = {
            "accuracy": confidence,
            "latency": latency,
            "error_rate": 0.0 if response.success else 1.0,
            "tokens_per_second": response.usage.get("total_tokens", 0)
            / max(latency, 0.1),
        }

        self.performance_tracker.record_performance(optimal_model, metrics)

        return response

    def _estimate_response_quality(self, response: str) -> float:
        """Estimate response quality for performance tracking."""
        # Simplified quality estimation
        quality_score = 0.8  # Base score

        # Check for completeness indicators
        if len(response) > 100:
            quality_score += 0.1

        # Check for code blocks (indicates structured response)
        if "```" in response:
            quality_score += 0.05

        # Check for error indicators
        error_indicators = ["error", "failed", "cannot", "don't know"]
        error_penalty = sum(
            0.1 for indicator in error_indicators if indicator in response.lower()
        )
        quality_score -= error_penalty

        return max(0.0, min(1.0, quality_score))
