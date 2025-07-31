"""Enhanced Model Router integrating ensemble capabilities."""

from datetime import datetime
from typing import Dict, Any

from .models import ModelRequest, ModelResponse
from .ensemble_router import EnsembleModelRouter, AdaptiveModelRouter
from .claude_client import ClaudeClient
from ..common.logging import get_logger

logger = get_logger("enhanced_router")


class EnhancedModelRouter:
    """Enhanced model router with ensemble and adaptive capabilities."""

    def __init__(self, claude_client: ClaudeClient | None = None):
        self.claude_client = claude_client
        self.ensemble_router = EnsembleModelRouter()
        self.adaptive_router = AdaptiveModelRouter()

        # Configuration
        self.use_ensemble_for_critical = True
        self.use_adaptive_routing = True
        self.performance_tracking_enabled = True

    async def route_request(self, request: ModelRequest) -> ModelResponse:
        """Route request using enhanced capabilities."""
        try:
            # Determine routing strategy
            routing_strategy = self._determine_routing_strategy(request)

            if routing_strategy == "ensemble":
                return await self._route_with_ensemble(request)
            elif routing_strategy == "adaptive":
                return await self._route_with_adaptive(request)
            else:
                return await self._route_standard(request)

        except Exception as e:
            logger.error(f"Enhanced routing failed for {request.request_id}: {e}")
            # Fallback to standard routing
            return await self._route_standard(request)

    def _determine_routing_strategy(self, request: ModelRequest) -> str:
        """Determine the best routing strategy for the request."""
        # Check for critical task indicators
        content = " ".join(msg.get("content", "") for msg in request.messages).lower()

        critical_keywords = [
            "security",
            "critical",
            "production",
            "compliance",
            "audit",
            "financial",
            "legal",
            "safety",
            "regulatory",
        ]

        if any(keyword in content for keyword in critical_keywords):
            return "ensemble" if self.use_ensemble_for_critical else "adaptive"

        # Use adaptive routing for general requests if enabled
        if self.use_adaptive_routing:
            return "adaptive"

        return "standard"

    async def _route_with_ensemble(self, request: ModelRequest) -> ModelResponse:
        """Route using ensemble consensus for critical tasks."""
        logger.info(
            f"Using ensemble routing for critical request: {request.request_id}"
        )

        ensemble_result = await self.ensemble_router.route_with_consensus(request)

        # Convert ensemble result to ModelResponse
        return ModelResponse(
            result=ensemble_result.final_response,
            model_used=f"ensemble({','.join(ensemble_result.participating_models)})",
            usage={
                "total_tokens": sum(
                    p.tokens_used for p in ensemble_result.prediction_details
                ),
                "consensus_confidence": ensemble_result.consensus_confidence,
                "participating_models": len(ensemble_result.participating_models),
            },
            request_id=request.request_id,
            metadata={
                "routing_strategy": ensemble_result.routing_strategy,
                "processing_time": ensemble_result.processing_time,
                "consensus_confidence": ensemble_result.consensus_confidence,
                "model_predictions": [
                    {
                        "model": p.model_id,
                        "confidence": p.confidence,
                        "latency": p.latency,
                    }
                    for p in ensemble_result.prediction_details
                ],
            },
            timestamp=datetime.utcnow(),
            success=True,
        )

    async def _route_with_adaptive(self, request: ModelRequest) -> ModelResponse:
        """Route using adaptive performance-based selection."""
        logger.info(f"Using adaptive routing for request: {request.request_id}")

        response = await self.adaptive_router.adaptive_route(request)

        # Add adaptive routing metadata
        if response.metadata is None:
            response.metadata = {}

        response.metadata.update(
            {
                "routing_strategy": "adaptive",
                "model_selection_reason": "performance_optimized",
            }
        )

        return response

    async def _route_standard(self, request: ModelRequest) -> ModelResponse:
        """Standard routing fallback."""
        logger.info(f"Using standard routing for request: {request.request_id}")
        if self.claude_client is None:
            self.claude_client = ClaudeClient()

        response = await self.claude_client.generate_response(request)

        # Add routing metadata
        if response.metadata is None:
            response.metadata = {}

        response.metadata.update({"routing_strategy": "standard"})

        return response

    async def get_routing_stats(self) -> Dict[str, Any]:
        """Get routing performance statistics."""
        return {
            "ensemble_router": {
                "performance_data": len(
                    self.ensemble_router.performance_tracker.performance_history
                ),
                "models_tracked": list(
                    self.ensemble_router.performance_tracker.performance_history.keys()
                ),
            },
            "adaptive_router": {
                "performance_data": len(
                    self.adaptive_router.performance_tracker.performance_history
                ),
                "routing_weights": self.adaptive_router.routing_weights.base_weights,
            },
            "configuration": {
                "ensemble_enabled": self.use_ensemble_for_critical,
                "adaptive_enabled": self.use_adaptive_routing,
                "performance_tracking": self.performance_tracking_enabled,
            },
        }
