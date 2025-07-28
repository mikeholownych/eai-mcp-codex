from src.verification_feedback.verification_engine import verify


def test_verify() -> None:
    assert verify(2).id == 2
