"""API routes for the Verification Feedback service."""

from typing import List

from fastapi import APIRouter, HTTPException

from src.common.metrics import record_request

from .models import Feedback, FeedbackRequest
from .feedback_processor import get_feedback_processor

router = APIRouter(prefix="/feedback", tags=["verification-feedback"])


@router.post("/", response_model=Feedback, status_code=201)
async def submit_feedback_route(request: FeedbackRequest) -> Feedback:
    record_request("verification-feedback")
    processor = get_feedback_processor()
    return await processor.submit_feedback(request)


@router.get("/", response_model=List[Feedback])
async def list_feedback_route(limit: int = 100) -> List[Feedback]:
    record_request("verification-feedback")
    processor = get_feedback_processor()
    return await processor.list_feedback(limit)


@router.get("/{feedback_id}", response_model=Feedback)
async def fetch_feedback_route(feedback_id: str) -> Feedback:
    record_request("verification-feedback")
    processor = get_feedback_processor()
    feedback = await processor.get_feedback(feedback_id)
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback not found")
    return feedback
