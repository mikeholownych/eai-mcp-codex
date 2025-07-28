"""Model selection and routing logic."""

from .models import ModelRequest, ModelResponse


_DEF_THRESHOLD = 100


def route(req: ModelRequest) -> ModelResponse:
    """Select a target model based on text length."""
    model = "sonnet" if len(req.text) > _DEF_THRESHOLD else "haiku"
    return ModelResponse(result=f"{model}:{req.text}")
