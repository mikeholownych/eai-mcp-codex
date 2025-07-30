"""Model selection and routing logic with Claude API integration."""

from __future__ import annotations

import asyncio
import os
import re
from pathlib import Path
from typing import Iterable, List, Pattern, Tuple, Dict, Any, Optional
from datetime import datetime

import yaml
from src.common.logging import get_logger

from .config import settings
from .models import ModelRequest, ModelResponse
from .claude_client import get_claude_client
from .local_client import get_local_client


logger = get_logger("model_router")


class RoutingTable:
    """In-memory routing table compiled from YAML rules."""

    def __init__(self, rules: Iterable[Tuple[str, str]]) -> None:
        self.rules: List[Tuple[Pattern[str], str]] = [
            (re.compile(pattern), model) for pattern, model in rules
        ]

    def select(self, text: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Return the first matching model for the given text."""
        # First try rule-based matching
        for pattern, model in self.rules:
            if pattern.search(text):
                logger.info(f"Rule-based routing selected model: {model}")
                return self._normalize_model_name(model)

        # Fall back to intelligent routing
        return self._intelligent_route(text, context)

    def _normalize_model_name(self, model: str) -> str:
        """Normalize model names from config to actual model names."""
        model_mapping = {
            # Claude models
            "opus": "claude-3-opus-20240229",
            "sonnet": "claude-3-5-sonnet-20241022",
            "haiku": "claude-3-5-haiku-20241022",
            "o3": "claude-3-opus-20240229",  # Treat O3 requests as Opus
            "4": "claude-3-5-sonnet-20241022",  # Treat Sonnet 4 as 3.5 Sonnet
            # Local models
            "mistral": "mistral",
            "local": "mistral",
            "ollama": "mistral",
            "local-llm": "local-llm",
        }
        return model_mapping.get(model.lower(), "mistral")  # Default to local mistral

    def _intelligent_route(
        self, text: str, context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Intelligent model selection based on content analysis."""
        # Check for preference for local models
        prefer_local = os.getenv("PREFER_LOCAL_MODELS", "true").lower() == "true"
        
        # Analyze text complexity and requirements
        complexity_indicators = {
            "high": [
                "architecture",
                "design",
                "complex",
                "analysis",
                "research",
                "planning",
                "security audit",
            ],
            "medium": [
                "code review",
                "debugging",
                "implementation",
                "refactor",
                "optimize",
            ],
            "low": ["simple", "basic", "quick", "summary", "list", "format"],
        }

        text_lower = text.lower()

        # Check for high complexity indicators
        if any(indicator in text_lower for indicator in complexity_indicators["high"]):
            return "claude-3-opus-20240229" if not prefer_local else "mistral"

        # Check for coding-specific indicators
        coding_indicators = [
            "code", "function", "class", "algorithm", "programming", "debug", 
            "implement", "python", "javascript", "java", "c++", "sql", "api",
            "refactor", "optimize", "bug", "error", "syntax", "variable"
        ]
        
        if any(indicator in text_lower for indicator in coding_indicators):
            return "claude-3-5-sonnet-20241022" if not prefer_local else "deepseek-coder"
        
        # Check for medium complexity indicators
        if any(
            indicator in text_lower for indicator in complexity_indicators["medium"]
        ):
            return "claude-3-5-sonnet-20241022" if not prefer_local else "deepseek-coder"

        # Check text length
        if len(text) > 1000:
            return "claude-3-5-sonnet-20241022" if not prefer_local else "mistral"

        # Context-based routing
        if context:
            task_type = context.get("task_type", "").lower()
            if task_type in [
                "architecture_design",
                "security_analysis",
                "complex_planning",
            ]:
                return "claude-3-opus-20240229" if not prefer_local else "mistral"
            elif task_type in ["code_generation", "code_review", "debugging", "programming"]:
                return "claude-3-5-sonnet-20241022" if not prefer_local else "deepseek-coder"

        # Default to local model if preferred, otherwise cost-effective Claude model
        return "mistral" if prefer_local else "claude-3-5-haiku-20241022"


def _load_rules(file_path: str) -> RoutingTable:
    """Load routing rules from YAML configuration."""
    if not Path(file_path).exists():
        logger.warning(f"Rules file not found: {file_path}, using default rules")
        return RoutingTable(
            [
                (r"(?i)(complex|architecture|design|security)", "opus"),
                (r"(?i)(code|debug|implement|refactor)", "sonnet"),
                (r".*", "haiku"),
            ]
        )

    try:
        data = yaml.safe_load(Path(file_path).read_text())
        rules = [
            (rule.get("match", ".*"), rule["model"])
            for rule in data.get("rules", [])
            if "model" in rule
        ]
        logger.info(f"Loaded {len(rules)} routing rules from {file_path}")
        return RoutingTable(rules)
    except Exception as e:
        logger.error(f"Error loading rules from {file_path}: {e}")
        return RoutingTable([(r".*", "haiku")])


_table = _load_rules(settings.rules_file)


async def route_async(req: ModelRequest) -> ModelResponse:
    """Asynchronously route request to appropriate LLM (Claude or local) and return response."""
    try:
        # Select model
        selected_model = _table.select(req.text, req.context)
        logger.info(f"Selected model: {selected_model} for request")

        # Prepare system prompt
        system_prompt = None
        if req.context:
            if req.context.get("system_prompt"):
                system_prompt = req.context["system_prompt"]
            elif req.context.get("task_type"):
                system_prompt = _get_system_prompt_for_task(req.context["task_type"])

        # Determine if we should use local or Claude API
        is_local_model = selected_model in ["mistral", "local-llm"]
        
        if is_local_model:
            # Use local LLM client
            local_client = get_local_client()
            response = await local_client.route_and_send(
                text=req.text, context=req.context, system_prompt=system_prompt
            )
            
            # Calculate usage metrics
            usage_info = {
                "input_tokens": len(req.text.split()),  # Approximate
                "output_tokens": response.usage.get("output_tokens", 0),
                "model_used": response.model,
                "response_time_ms": (
                    datetime.utcnow() - response.timestamp
                ).total_seconds() * 1000,
                "cost": 0.0,  # Local models are free
                "provider": "local",
            }

            return ModelResponse(
                result=response.content,
                model_used=response.model,
                usage=usage_info,
                request_id=response.id,
                metadata={
                    "stop_reason": response.stop_reason,
                    "timestamp": response.timestamp.isoformat(),
                    "routing_decision": {
                        "selected_model": selected_model,
                        "selection_reason": "local_preferred",
                    },
                    "provider": "local",
                },
            )
        else:
            # Use Claude API client
            claude_client = get_claude_client()
            claude_response = await claude_client.route_and_send(
                text=req.text, context=req.context, system_prompt=system_prompt
            )

            # Calculate usage metrics
            usage_info = {
                "input_tokens": claude_response.usage.get("input_tokens", 0),
                "output_tokens": claude_response.usage.get("output_tokens", 0),
                "model_used": claude_response.model,
                "response_time_ms": (
                    datetime.utcnow() - claude_response.timestamp
                ).total_seconds()
                * 1000,
                "provider": "claude",
            }

            return ModelResponse(
                result=claude_response.content,
                model_used=claude_response.model,
                usage=usage_info,
                request_id=claude_response.id,
                metadata={
                    "stop_reason": claude_response.stop_reason,
                    "timestamp": claude_response.timestamp.isoformat(),
                    "routing_decision": {
                        "selected_model": selected_model,
                        "selection_reason": "rule_based"
                        if selected_model
                        else "intelligent_routing",
                    },
                    "provider": "claude",
                },
            )

    except Exception as e:
        logger.error(f"Error routing request: {e}")
        return ModelResponse(
            result=f"Error processing request: {str(e)}",
            model_used="error",
            usage={"error": True},
            request_id="error",
            metadata={"error": str(e)},
        )


def route(req: ModelRequest) -> ModelResponse:
    """Synchronous wrapper for routing requests."""
    try:
        # Run async function in event loop
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If loop is already running, create a task
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, route_async(req))
                return future.result(timeout=30)
        else:
            return asyncio.run(route_async(req))
    except Exception as e:
        logger.error(f"Error in synchronous route wrapper: {e}")
        return ModelResponse(
            result=f"Routing error: {str(e)}",
            model_used="error",
            usage={"error": True},
            request_id="sync_error",
            metadata={"error": str(e)},
        )


def _get_system_prompt_for_task(task_type: str) -> str:
    """Get system prompt based on task type."""
    prompts = {
        "code_generation": "You are an expert software developer. Generate clean, well-documented, and efficient code based on the requirements.",
        "code_review": "You are a senior code reviewer. Analyze the provided code for bugs, security issues, performance problems, and style violations.",
        "architecture_design": "You are a senior software architect. Design scalable, maintainable, and robust system architectures.",
        "security_analysis": "You are a cybersecurity expert. Analyze the provided information for security vulnerabilities and provide remediation recommendations.",
        "debugging": "You are an expert debugger. Analyze the provided code and error information to identify and fix issues.",
        "planning": "You are a project planning expert. Break down complex projects into manageable tasks with clear deliverables and timelines.",
        "documentation": "You are a technical writer. Create clear, comprehensive, and well-structured documentation.",
    }

    return prompts.get(
        task_type,
        "You are a helpful AI assistant. Provide accurate, helpful, and well-structured responses.",
    )


def get_routing_stats() -> Dict[str, Any]:
    """Get routing statistics and model usage information."""
    claude_client = get_claude_client()

    return {
        "available_models": claude_client.list_available_models(),
        "routing_rules_count": len(_table.rules),
        "default_model": "claude-3-5-haiku-20241022",
        "model_info": {
            model: claude_client.get_model_info(model)
            for model in claude_client.list_available_models()
        },
    }


async def test_routing() -> Dict[str, Any]:
    """Test routing functionality with sample requests."""
    test_cases = [
        {"text": "Hello, world!", "expected_model": "claude-3-5-haiku-20241022"},
        {
            "text": "Design a microservices architecture for a large e-commerce platform",
            "expected_model": "claude-3-opus-20240229",
        },
        {
            "text": "Review this Python code for bugs",
            "expected_model": "claude-3-5-sonnet-20241022",
        },
        {
            "text": "Simple question about Python syntax",
            "expected_model": "claude-3-5-haiku-20241022",
        },
    ]

    results = []
    for case in test_cases:
        req = ModelRequest(text=case["text"])
        selected_model = _table.select(req.text)
        results.append(
            {
                "text": case["text"][:50] + "..."
                if len(case["text"]) > 50
                else case["text"],
                "selected_model": selected_model,
                "expected_model": case["expected_model"],
                "correct": selected_model == case["expected_model"],
            }
        )

    return {
        "test_results": results,
        "accuracy": sum(1 for r in results if r["correct"]) / len(results) * 100,
    }
