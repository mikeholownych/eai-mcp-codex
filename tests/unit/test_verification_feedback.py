from src.verification_feedback.verification_engine import verify


def test_verify():
    assert verify(2).id == 2
