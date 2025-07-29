"""Claude API client for model routing and interaction."""

import os
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime

import httpx
from src.common.logging import get_logger


logger = get_logger("claude_client")


@dataclass
class ClaudeMessage:
    """Claude API message structure."""

    role: str  # "user" or "assistant"
    content: str


@dataclass
class ClaudeRequest:
    """Claude API request structure."""

    model: str
    messages: List[ClaudeMessage]
    max_tokens: int = 4096
    temperature: float = 0.7
    system: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ClaudeResponse:
    """Claude API response structure."""

    id: str
    content: str
    model: str
    usage: Dict[str, int]
    stop_reason: str
    timestamp: datetime


class ClaudeClient:
    """Client for interacting with Claude API."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY must be provided")

        self.base_url = "https://api.anthropic.com/v1"
        self.headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
        }

        # Model configurations
        self.model_configs = {
            "claude-3-5-sonnet-20241022": {
                "max_tokens": 8192,
                "context_window": 200000,
                "cost_per_1k_input": 0.003,
                "cost_per_1k_output": 0.015,
                "use_cases": ["complex_reasoning", "code_analysis", "planning"],
            },
            "claude-3-5-haiku-20241022": {
                "max_tokens": 8192,
                "context_window": 200000,
                "cost_per_1k_input": 0.0008,
                "cost_per_1k_output": 0.004,
                "use_cases": ["simple_tasks", "quick_responses", "classification"],
            },
            "claude-3-opus-20240229": {
                "max_tokens": 4096,
                "context_window": 200000,
                "cost_per_1k_input": 0.015,
                "cost_per_1k_output": 0.075,
                "use_cases": ["complex_analysis", "creative_tasks", "research"],
            },
        }

    async def send_message(self, request: ClaudeRequest) -> ClaudeResponse:
        """Send a message to Claude and return the response."""
        try:
            # Prepare request payload
            payload = {
                "model": request.model,
                "max_tokens": request.max_tokens,
                "temperature": request.temperature,
                "messages": [
                    {"role": msg.role, "content": msg.content}
                    for msg in request.messages
                ],
            }

            if request.system:
                payload["system"] = request.system

            if request.metadata:
                payload["metadata"] = request.metadata

            logger.info(f"Sending request to Claude model: {request.model}")

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/messages", headers=self.headers, json=payload
                )

                if response.status_code != 200:
                    error_msg = (
                        f"Claude API error: {response.status_code} - {response.text}"
                    )
                    logger.error(error_msg)
                    raise Exception(error_msg)

                result = response.json()

                # Extract content from response
                content = ""
                if result.get("content") and isinstance(result["content"], list):
                    content = "".join(
                        [
                            block.get("text", "")
                            for block in result["content"]
                            if block.get("type") == "text"
                        ]
                    )

                return ClaudeResponse(
                    id=result.get("id", ""),
                    content=content,
                    model=result.get("model", request.model),
                    usage=result.get("usage", {}),
                    stop_reason=result.get("stop_reason", ""),
                    timestamp=datetime.utcnow(),
                )

        except Exception as e:
            logger.error(f"Error sending message to Claude: {e}")
            raise

    async def route_and_send(
        self,
        text: str,
        context: Optional[Dict[str, Any]] = None,
        system_prompt: Optional[str] = None,
    ) -> ClaudeResponse:
        """Route request to appropriate model and send message."""
        # Determine best model based on request characteristics
        model = self._select_model(text, context)

        # Create message
        messages = [ClaudeMessage(role="user", content=text)]

        # Get model config
        config = self.model_configs.get(
            model, self.model_configs["claude-3-5-haiku-20241022"]
        )

        # Create request
        request = ClaudeRequest(
            model=model,
            messages=messages,
            max_tokens=min(config["max_tokens"], 4096),
            system=system_prompt,
            metadata=context,
        )

        return await self.send_message(request)

    def _select_model(self, text: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Select the most appropriate Claude model based on request characteristics."""
        # Analyze request complexity
        complexity_score = self._calculate_complexity(text, context)

        # Select model based on complexity and use case
        if complexity_score > 0.8:
            return "claude-3-opus-20240229"  # Most capable for complex tasks
        elif complexity_score > 0.5:
            return "claude-3-5-sonnet-20241022"  # Balanced for moderate complexity
        else:
            return "claude-3-5-haiku-20241022"  # Fast for simple tasks

    def _calculate_complexity(
        self, text: str, context: Optional[Dict[str, Any]] = None
    ) -> float:
        """Calculate complexity score for model selection."""
        score = 0.0

        # Text length factor
        if len(text) > 2000:
            score += 0.3
        elif len(text) > 500:
            score += 0.1

        # Complexity indicators in text
        complexity_keywords = [
            "analyze",
            "complex",
            "detailed",
            "comprehensive",
            "architecture",
            "design",
            "algorithm",
            "optimization",
            "security",
            "performance",
            "integration",
            "workflow",
            "collaboration",
            "planning",
        ]

        keyword_count = sum(
            1 for keyword in complexity_keywords if keyword.lower() in text.lower()
        )
        score += min(0.4, keyword_count * 0.05)

        # Context-based complexity
        if context:
            if context.get("task_type") in [
                "architecture",
                "security_review",
                "complex_analysis",
            ]:
                score += 0.3
            if context.get("priority") == "high":
                score += 0.1
            if context.get("requires_reasoning", False):
                score += 0.2

        return min(1.0, score)

    def get_model_info(self, model: str) -> Dict[str, Any]:
        """Get information about a specific model."""
        return self.model_configs.get(model, {})

    def list_available_models(self) -> List[str]:
        """List all available Claude models."""
        return list(self.model_configs.keys())

    async def test_connection(self) -> bool:
        """Test connection to Claude API."""
        try:
            test_request = ClaudeRequest(
                model="claude-3-5-haiku-20241022",
                messages=[
                    ClaudeMessage(
                        role="user", content="Hello, this is a connection test."
                    )
                ],
                max_tokens=50,
            )

            await self.send_message(test_request)
            logger.info("Claude API connection test successful")
            return True

        except Exception as e:
            logger.error(f"Claude API connection test failed: {e}")
            return False


# Singleton instance
_claude_client: Optional[ClaudeClient] = None


def get_claude_client() -> ClaudeClient:
    """Get singleton Claude client instance."""
    global _claude_client
    if _claude_client is None:
        _claude_client = ClaudeClient()
    return _claude_client
