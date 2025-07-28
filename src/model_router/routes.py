"""API routes for Model Router."""

from fastapi import APIRouter

from .models import ModelRequest, ModelResponse

router = APIRouter()


@router.post("/route", response_model=ModelResponse)
def route_model(req: ModelRequest) -> ModelResponse:
    return ModelResponse(result=req.text)
