from src.analytics.escalation_tracker import EscalationAbuseTracker


def test_escalation_abuse_detection() -> None:
    tracker = EscalationAbuseTracker(threshold=2, window_minutes=10)
    tracker.record_escalation("s1", "u1", "bug")
    tracker.record_escalation("s2", "u1", "bug")
    assert tracker.is_abuse("u1")

    tracker.clear_old_events()
    assert len(tracker.events) <= 2
