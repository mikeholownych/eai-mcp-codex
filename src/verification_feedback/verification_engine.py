"""Verification engine."""

from .models import Feedback


def verify(feedback_id: int) -> Feedback:
    return Feedback(id=feedback_id)
