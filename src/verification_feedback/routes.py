"""API routes for the Verification Feedback service."""

from fastapi import APIRouter, HTTPException

from src.common.metrics import record_request

from .models import Feedback
from .feedback_processor import get_feedback_processor

router = APIRouter(prefix="/feedback", tags=["verification-feedback"])


@router.get("/{feedback_id}", response_model=Feedback)
async def fetch_feedback_route(feedback_id: str) -> Feedback:
    record_request("verification-feedback")
    processor = await get_feedback_processor()
    feedback = await processor.get_feedback(feedback_id)
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback not found")
    return feedback
