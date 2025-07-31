"""Abacus.ai client for LLM model routing."""

from __future__ import annotations

import time
from datetime import datetime
from typing import Dict, Any, Optional, List
import os

import httpx

try:
    from abacusai import ApiClient
except ImportError:
    ApiClient = None

from src.common.logging import get_logger
from .models import LLMResponse

logger = get_logger("abacus_client")


class AbacusAIClient:
    """Client for Abacus.ai LLM models with intelligent model selection."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize AbacusAI client."""
        self.api_key = api_key or os.getenv("ABACUSAI_API_KEY")
        if not self.api_key:
            logger.warning(
                "ABACUSAI_API_KEY not found. Abacus.ai client will not be available."
            )
            self._client = None
        else:
            try:
                if ApiClient is None:
                    logger.error(
                        "abacusai package not installed. Run: pip install abacusai"
                    )
                    self._client = None
                else:
                    self._client = ApiClient(self.api_key)
                    logger.info("AbacusAI client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize AbacusAI client: {e}")
                self._client = None

        # Available models mapping
        self._model_mapping = {
            # High-capability models for complex tasks
            "gpt-4o": "gpt-4o",
            "o3": "o3",
            "sonnet-4": "claude-3-5-sonnet-20241022",
            "sonnet-3.7": "claude-3-5-sonnet-20241022",
            "opus-4": "claude-3-opus-20240229",
            # Specialized models
            "deepseek-r1": "deepseek-r1",
            "grok-4": "grok-4",
            "gemini-2.5": "gemini-2.5-pro",
            "llama-4": "meta-llama/Meta-Llama-3-8B-Instruct",
            # Fast models for simple tasks
            "gpt-4o-mini": "gpt-4o-mini",
            "gemini-2.0": "gemini-2.0-flash",
        }

    def is_available(self) -> bool:
        """Check if AbacusAI client is available."""
        return self._client is not None

    def _select_optimal_model(
        self, text: str, context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Select the most suitable Abacus.ai model based on request characteristics."""
        if not self.is_available():
            return "error"

        text_lower = text.lower()
        text_length = len(text)

        # High complexity indicators - use most capable models
        high_complexity_indicators = [
            "architecture",
            "design",
            "complex analysis",
            "research",
            "planning",
            "security audit",
            "system design",
            "multi-step reasoning",
            "mathematical proof",
            "strategic planning",
            "comprehensive analysis",
        ]

        # Coding specific indicators - use coding-optimized models
        coding_indicators = [
            "code",
            "function",
            "class",
            "algorithm",
            "programming",
            "debug",
            "implement",
            "python",
            "javascript",
            "java",
            "c++",
            "sql",
            "api",
            "refactor",
            "optimize",
            "bug",
            "error",
            "syntax",
            "variable",
            "repository",
            "git",
            "framework",
            "library",
            "database",
        ]

        # Creative/conversational indicators - use general purpose models
        creative_indicators = [
            "creative",
            "story",
            "poem",
            "creative writing",
            "brainstorm",
            "ideation",
            "marketing",
            "content",
            "blog",
            "social media",
        ]

        # Simple task indicators - use efficient models
        simple_indicators = [
            "simple",
            "basic",
            "quick",
            "summary",
            "list",
            "format",
            "translate",
            "define",
            "explain briefly",
            "what is",
        ]

        # Context-based routing
        if context:
            task_type = context.get("task_type", "").lower()
            priority = context.get("priority", "medium").lower()

            # High priority or complex tasks
            if priority == "high" or task_type in [
                "architecture_design",
                "security_analysis",
                "complex_planning",
                "research",
                "strategic_analysis",
            ]:
                return "o3"  # Most capable model

            # Coding tasks
            elif task_type in [
                "code_generation",
                "code_review",
                "debugging",
                "programming",
            ]:
                return "deepseek-r1"  # Specialized coding model

            # Creative tasks
            elif task_type in ["creative_writing", "content_generation", "marketing"]:
                return "gpt-4o"  # Good for creative tasks

        # Text analysis based routing
        if any(indicator in text_lower for indicator in high_complexity_indicators):
            return "o3"

        if any(indicator in text_lower for indicator in coding_indicators):
            return "deepseek-r1"

        if any(indicator in text_lower for indicator in creative_indicators):
            return "gpt-4o"

        if any(indicator in text_lower for indicator in simple_indicators):
            return "gpt-4o-mini"  # Fast and efficient for simple tasks

        # Length-based routing
        if text_length > 2000:
            return "sonnet-4"  # Good for long context
        elif text_length > 500:
            return "gpt-4o"
        else:
            return "gpt-4o-mini"

    async def route_and_send(
        self,
        text: str,
        context: Optional[Dict[str, Any]] = None,
        system_prompt: Optional[str] = None,
        model_override: Optional[str] = None,
    ) -> LLMResponse:
        """Route request to optimal Abacus.ai model and return response."""
        if not self.is_available():
            raise Exception("AbacusAI client not available")

        start_time = time.time()

        try:
            # Select model
            selected_model = model_override or self._select_optimal_model(text, context)
            logger.info(f"Selected Abacus.ai model: {selected_model}")

            # Prepare messages
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": text})

            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    "https://api.abacus.ai/v1/chat",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={"model": selected_model, "messages": messages},
                )
                response.raise_for_status()
                data = response.json()
                response_content = data["choices"][0]["message"]["content"]

            response_time = time.time() - start_time

            # Create response object
            return LLMResponse(
                id=f"abacus_{int(time.time())}",
                content=response_content,
                model=selected_model,
                usage={
                    "input_tokens": len(text.split()),
                    "output_tokens": len(response_content.split()),
                    "total_tokens": len(text.split()) + len(response_content.split()),
                },
                timestamp=datetime.utcnow(),
                stop_reason="end_turn",
                metadata={
                    "provider": "abacus.ai",
                    "response_time": response_time,
                    "selected_model": selected_model,
                },
            )

        except Exception as e:
            logger.error(f"Error calling Abacus.ai API: {e}")
            raise

    def list_available_models(self) -> List[str]:
        """Return list of available Abacus.ai models."""
        if not self.is_available():
            return []
        return list(self._model_mapping.keys())

    def get_model_info(self, model: str) -> Dict[str, Any]:
        """Get information about a specific model."""
        if model not in self._model_mapping:
            return {"error": f"Model {model} not available"}

        # Model capability information
        model_info = {
            "o3": {
                "capability": "highest",
                "best_for": ["complex reasoning", "research", "analysis"],
                "cost": "high",
                "speed": "slow",
            },
            "gpt-4o": {
                "capability": "high",
                "best_for": ["general purpose", "creative tasks", "conversation"],
                "cost": "medium-high",
                "speed": "medium",
            },
            "deepseek-r1": {
                "capability": "high",
                "best_for": ["coding", "programming", "technical tasks"],
                "cost": "medium",
                "speed": "medium",
            },
            "sonnet-4": {
                "capability": "high",
                "best_for": ["long context", "analysis", "writing"],
                "cost": "medium-high",
                "speed": "medium",
            },
            "gpt-4o-mini": {
                "capability": "medium",
                "best_for": ["simple tasks", "quick responses", "efficiency"],
                "cost": "low",
                "speed": "fast",
            },
        }

        return model_info.get(
            model,
            {
                "capability": "unknown",
                "best_for": ["general purpose"],
                "cost": "unknown",
                "speed": "unknown",
            },
        )


def get_abacus_client() -> AbacusAIClient:
    """Get AbacusAI client instance."""
    return AbacusAIClient()
