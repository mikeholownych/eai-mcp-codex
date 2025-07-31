from datetime import timedelta
from src.analytics.usage_analyzer import UsagePatternAnalyzer


def test_usage_analyzer_counts_users_and_actions():
    analyzer = UsagePatternAnalyzer()
    analyzer.record_event("u1", "login")
    analyzer.record_event("u1", "view")
    analyzer.record_event("u2", "login")
    assert analyzer.get_daily_active_users() == 2
    assert analyzer.get_action_frequency("login") == 2
    assert analyzer.get_action_frequency("view") == 1


def test_usage_analyzer_clears_old_events():
    analyzer = UsagePatternAnalyzer()
    analyzer.record_event("u1", "login")
    analyzer.events[0].timestamp -= timedelta(days=31)
    analyzer.clear_old_events()
    assert len(analyzer.events) == 0
