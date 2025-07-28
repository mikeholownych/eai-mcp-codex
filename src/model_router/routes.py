"""API routes for the Model Router service."""

from fastapi import APIRouter

from src.common.metrics import record_request

from .models import ModelRequest, ModelResponse
from .router import route

router = APIRouter(prefix="/model", tags=["model-router"])


@router.post("/route", response_model=ModelResponse)
def route_model(req: ModelRequest) -> ModelResponse:
    record_request("model-router")
    return route(req)
