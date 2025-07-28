"""Routes for Verification Feedback."""

from fastapi import APIRouter

from .models import Feedback

router = APIRouter()


@router.get("/feedback/{feedback_id}")
def get_feedback(feedback_id: int) -> Feedback:
    return Feedback(id=feedback_id)
