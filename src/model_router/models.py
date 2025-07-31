"""Data models for the Model Router service."""

from typing import Any, Dict, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class ModelRequest(BaseModel):
    """Request model for routing decisions."""

    text: str
    context: Optional[Dict[str, Any]] = None
    task_type: Optional[str] = None
    priority: Optional[str] = "medium"
    system_prompt: Optional[str] = None
    max_tokens: Optional[int] = 4096
    temperature: Optional[float] = 0.7
    metadata: Optional[Dict[str, Any]] = None
    request_id: Optional[str] = None


class ModelResponse(BaseModel):
    """Response model from routing."""

    result: str
    model_used: str = "unknown"
    usage: Dict[str, Any] = Field(default_factory=dict)
    request_id: str = "unknown"
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    success: bool = True
    error_message: Optional[str] = None


class LLMResponse(BaseModel):
    """Raw LLM response structure."""

    id: str
    content: str
    model: str
    usage: Dict[str, int] = Field(default_factory=dict)
    stop_reason: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ModelInfo(BaseModel):
    """Information about available models."""

    name: str
    max_tokens: int
    context_window: int
    cost_per_1k_input: float
    cost_per_1k_output: float
    use_cases: list[str]


class LLMResponse(BaseModel):
    """Response model from an LLM."""

    text: str
    model_name: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class RoutingStats(BaseModel):
    """Statistics about model routing."""

    total_requests: int = 0
    requests_by_model: Dict[str, int] = Field(default_factory=dict)
    average_response_time: float = 0.0
    error_rate: float = 0.0
    last_updated: datetime = Field(default_factory=datetime.utcnow)
