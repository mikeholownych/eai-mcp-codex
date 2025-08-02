import pytest

from src.verification_feedback.feedback_processor import FeedbackProcessor
from src.verification_feedback.models import (
    FeedbackRequest,
    FeedbackSeverity,
    FeedbackType,
)


@pytest.mark.asyncio
async def test_submit_and_fetch_feedback(monkeypatch) -> None:
    """Feedback can be stored and retrieved using the processor."""
    monkeypatch.setenv("TESTING_MODE", "true")
    processor = FeedbackProcessor()
    await processor.initialize_database()

    request = FeedbackRequest(
        feedback_type=FeedbackType.USER_FEEDBACK,
        severity=FeedbackSeverity.MEDIUM,
        title="Test feedback",
        content="Something happened",
    )

    feedback = await processor.submit_feedback(request, source="tester")
    fetched = await processor.get_feedback(feedback.id)

    assert fetched is not None
    assert fetched.title == "Test feedback"

    await processor.shutdown_database()
