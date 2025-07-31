from datetime import timedelta, datetime

from src.analytics.user_engagement import UserEngagementTracker


def test_user_engagement_tracker_basic() -> None:
    tracker = UserEngagementTracker()

    now = datetime.utcnow()
    tracker.record_event("u1", "login")
    tracker.record_event("u1", "view")
    tracker.record_event("u2", "login")

    assert tracker.get_active_users() == 2
    assert tracker.get_event_count("login") == 2
    assert tracker.get_user_engagement_score("u1") == 2.5

    # events older than window are ignored
    tracker.events.append(
        tracker.events[0].__class__(
            user_id="u3", event_type="login", timestamp=now - timedelta(minutes=61)
        )
    )
    assert tracker.get_active_users() == 2

    tracker.clear_old_events(older_than_minutes=60)
    for event in tracker.events:
        assert event.timestamp >= datetime.utcnow() - timedelta(minutes=60)
