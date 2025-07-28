"""API routes for the Verification Feedback service."""

from fastapi import APIRouter

from src.common.metrics import record_request

from .models import Feedback
from .verification_engine import verify

router = APIRouter(prefix="/feedback", tags=["verification-feedback"])


@router.get("/{feedback_id}", response_model=Feedback)
def fetch(feedback_id: int) -> Feedback:
    record_request("verification-feedback")
    return verify(feedback_id)
