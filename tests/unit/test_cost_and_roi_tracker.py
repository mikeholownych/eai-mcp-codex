from src.analytics.cost_tracker import CostTracker
from src.analytics.roi_tracker import ROITracker


def test_cost_tracker_basic() -> None:
    tracker = CostTracker()
    tracker.record_cost("m1", 1.0, category="model")
    tracker.record_cost("m2", 2.5, category="model")
    assert tracker.total_cost() == 3.5
    categories = tracker.cost_by_category()
    assert categories["model"] == 3.5


def test_roi_tracker_calculation() -> None:
    cost_tracker = CostTracker()
    roi_tracker = ROITracker(cost_tracker)
    cost_tracker.record_cost("m1", 2.0)
    roi_tracker.record_value("rev", 6.0)
    assert roi_tracker.total_value() == 6.0
    assert roi_tracker.calculate_roi() == 200.0
