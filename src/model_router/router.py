"""Routing logic."""

from .models import ModelRequest, ModelResponse


def route(req: ModelRequest) -> ModelResponse:
    """Return a response echoing the request."""
    return ModelResponse(result=req.text)
