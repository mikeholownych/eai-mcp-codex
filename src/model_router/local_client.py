# mypy: ignore-errors
"""Local LLM client for Ollama integration."""

import os
import json
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime

import httpx
from src.common.logging import get_logger

logger = get_logger("local_client")


@dataclass
class LocalMessage:
    """Local LLM message structure."""

    role: str  # "user" or "assistant"
    content: str


@dataclass
class LocalRequest:
    """Local LLM request structure."""

    model: str
    messages: List[LocalMessage]
    max_tokens: int = 4096
    temperature: float = 0.7
    system: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


@dataclass
class LocalResponse:
    """Local LLM response structure."""

    id: str
    content: str
    model: str
    usage: Dict[str, int]
    stop_reason: str
    timestamp: datetime


class LocalLLMClient:
    """Client for interacting with local LLM services (Ollama + FastAPI)."""

    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or os.getenv("LOCAL_LLM_URL", "http://localhost:8000")
        self.ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")

        # Model configurations for local models - optimized for RAG agent workflows
        self.model_configs = {
            "mistral": {
                "max_tokens": 8192,  # Increased for longer responses
                "context_window": 8192,
                "cost_per_1k_input": 0.0,  # Local models are free
                "cost_per_1k_output": 0.0,
                "use_cases": ["general_purpose", "analysis", "brainstorming"],
                "provider": "ollama",
                "temperature": 0.3,  # Lower for more focused responses
                "top_p": 0.9,
                "repeat_penalty": 1.1,
                "system_prompt_prefix": "You are a helpful AI assistant working in a collaborative agent environment.",
            },
            "deepseek-coder": {
                "max_tokens": 8192,  # Increased for longer code responses
                "context_window": 32768,  # Updated to model's actual capacity
                "cost_per_1k_input": 0.0,
                "cost_per_1k_output": 0.0,
                "use_cases": [
                    "coding",
                    "debugging",
                    "code_review",
                    "programming",
                    "architecture",
                ],
                "provider": "ollama",
                "model_name": "deepseek-coder:6.7b",
                "temperature": 0.1,  # Very low for precise code generation
                "top_p": 0.95,
                "repeat_penalty": 1.05,
                "system_prompt_prefix": "You are an expert software engineer in a multi-agent system. Generate clean, well-documented code.",
            },
            "codellama": {
                "max_tokens": 8192,
                "context_window": 16384,
                "cost_per_1k_input": 0.0,
                "cost_per_1k_output": 0.0,
                "use_cases": [
                    "coding",
                    "code_generation",
                    "programming",
                    "code_explanation",
                ],
                "provider": "ollama",
                "model_name": "codellama:13b",
                "temperature": 0.2,
                "top_p": 0.9,
                "repeat_penalty": 1.1,
                "system_prompt_prefix": "You are a coding assistant focused on clear, maintainable code solutions.",
            },
            "codestral": {
                "max_tokens": 8192,
                "context_window": 32768,
                "cost_per_1k_input": 0.0,
                "cost_per_1k_output": 0.0,
                "use_cases": [
                    "advanced_coding",
                    "architecture",
                    "complex_programming",
                    "system_design",
                ],
                "provider": "ollama",
                "model_name": "codestral:22b",
                "temperature": 0.15,
                "top_p": 0.95,
                "repeat_penalty": 1.05,
                "system_prompt_prefix": "You are a senior software architect specializing in complex system design and implementation.",
            },
            "local-llm": {
                "max_tokens": 4096,
                "context_window": 8192,
                "cost_per_1k_input": 0.0,
                "cost_per_1k_output": 0.0,
                "use_cases": ["general_purpose", "quick_responses", "summarization"],
                "provider": "fastapi",
                "temperature": 0.4,
                "system_prompt_prefix": "You are a quick-response AI assistant in a collaborative environment.",
            },
        }

    async def send_message(self, request: LocalRequest) -> LocalResponse:
        """Send a message to local LLM and return the response."""
        try:
            model_config = self.model_configs.get(
                request.model, self.model_configs["mistral"]
            )

            if model_config["provider"] == "ollama":
                return await self._send_to_ollama(request)
            else:
                return await self._send_to_fastapi(request)

        except Exception as e:
            logger.error(f"Error sending message to local LLM: {e}")
            raise

    async def _send_to_ollama(self, request: LocalRequest) -> LocalResponse:
        """Send request directly to Ollama."""
        try:
            # Get the actual model name for Ollama
            model_config = self.model_configs.get(request.model, {})
            actual_model = model_config.get("model_name", request.model)

            # For deepseek-coder, use the full name
            if request.model == "deepseek-coder":
                actual_model = "deepseek-coder:6.7b"

            # Construct optimized prompt with model-specific system message
            model_config = self.model_configs.get(request.model, {})
            system_prefix = model_config.get("system_prompt_prefix", "")

            prompt = ""

            # Add model-specific system prompt prefix
            if system_prefix:
                prompt += f"System: {system_prefix}\n"

            # Add user-provided system message
            if request.system:
                prompt += f"Additional Context: {request.system}\n\n"
            elif system_prefix:
                prompt += "\n"

            # Add conversation history with better formatting
            for i, msg in enumerate(request.messages):
                if msg.role == "user":
                    prompt += f"User: {msg.content}\n"
                else:
                    prompt += f"Assistant: {msg.content}\n"

            # Ensure proper ending
            if not prompt.endswith(("User: ", "Assistant: ")):
                prompt += "Assistant: "

            # Get optimized parameters for this model
            model_config = self.model_configs.get(request.model, {})

            payload = {
                "model": actual_model,
                "prompt": prompt,
                "options": {
                    "num_predict": request.max_tokens,
                    "temperature": model_config.get("temperature", request.temperature),
                    "top_p": model_config.get("top_p", 0.9),
                    "repeat_penalty": model_config.get("repeat_penalty", 1.1),
                    "num_ctx": model_config.get("context_window", 8192),
                },
            }

            logger.info(f"Sending request to Ollama: {request.model}")

            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{self.ollama_url}/api/generate", json=payload
                )

                if response.status_code != 200:
                    error_msg = (
                        f"Ollama API error: {response.status_code} - {response.text}"
                    )
                    logger.error(error_msg)
                    raise Exception(error_msg)

                # Parse streaming response
                response_text = ""
                for line in response.text.strip().split("\n"):
                    if line:
                        try:
                            chunk = json.loads(line)
                            if "response" in chunk:
                                response_text += chunk["response"]
                        except json.JSONDecodeError:
                            continue

                return LocalResponse(
                    id=f"ollama_{datetime.utcnow().timestamp()}",
                    content=response_text,
                    model=request.model,
                    usage={"output_tokens": len(response_text.split())},
                    stop_reason="complete",
                    timestamp=datetime.utcnow(),
                )

        except Exception as e:
            logger.error(f"Error sending to Ollama: {e}")
            raise

    async def _send_to_fastapi(self, request: LocalRequest) -> LocalResponse:
        """Send request through FastAPI LLM router."""
        try:
            # Use the last user message as the query
            query = ""
            context = ""

            for msg in request.messages:
                if msg.role == "user":
                    query = msg.content
                elif msg.role == "assistant":
                    context += f"Assistant: {msg.content}\n"

            if request.system:
                context = f"System: {request.system}\n{context}"

            payload = {
                "query": query,
                "context": context if context else None,
                "max_tokens": request.max_tokens,
                "temperature": request.temperature,
            }

            logger.info("Sending request to FastAPI LLM router")

            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(f"{self.base_url}/query", json=payload)

                if response.status_code != 200:
                    error_msg = (
                        f"FastAPI LLM error: {response.status_code} - {response.text}"
                    )
                    logger.error(error_msg)
                    raise Exception(error_msg)

                result = response.json()

                return LocalResponse(
                    id=f"fastapi_{datetime.utcnow().timestamp()}",
                    content=result.get("response", ""),
                    model=result.get("model", "local-llm"),
                    usage={"output_tokens": result.get("tokens_used", 0)},
                    stop_reason="complete",
                    timestamp=datetime.utcnow(),
                )

        except Exception as e:
            logger.error(f"Error sending to FastAPI: {e}")
            raise

    async def route_and_send(
        self,
        text: str,
        context: Optional[Dict[str, Any]] = None,
        system_prompt: Optional[str] = None,
    ) -> LocalResponse:
        """Route request to appropriate local model and send message."""
        # Check if this is a coding task
        text_lower = text.lower()
        coding_keywords = [
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
        ]

        if any(keyword in text_lower for keyword in coding_keywords):
            model = "deepseek-coder"
        else:
            model = "deepseek-coder"  # Default to coding model for best results

        # Create message
        messages = [LocalMessage(role="user", content=text)]

        # Create request
        request = LocalRequest(
            model=model,
            messages=messages,
            max_tokens=4096,
            system=system_prompt,
            context=context,
        )

        return await self.send_message(request)

    def get_model_info(self, model: str) -> Dict[str, Any]:
        """Get information about a specific model."""
        return self.model_configs.get(model, {})

    def list_available_models(self) -> List[str]:
        """List all available local models."""
        return list(self.model_configs.keys())

    async def test_connection(self) -> bool:
        """Test connection to local LLM services."""
        try:
            # Test FastAPI connection
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url}/health")
                if response.status_code != 200:
                    logger.warning("FastAPI LLM service not available")

            # Test Ollama connection
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.ollama_url}/api/tags")
                if response.status_code != 200:
                    logger.warning("Ollama service not available")

            logger.info("Local LLM services connection test completed")
            return True

        except Exception as e:
            logger.error(f"Local LLM connection test failed: {e}")
            return False


# Singleton instance
_local_client: Optional[LocalLLMClient] = None


def get_local_client() -> LocalLLMClient:
    """Get singleton local LLM client instance."""
    global _local_client
    if _local_client is None:
        _local_client = LocalLLMClient()
    return _local_client
