from src.analytics.cost_tracker import CostTracker
from src.analytics.roi_tracker import ROITracker
from src.analytics.cost_optimizer import CostOptimizer


def test_cost_optimizer_recommendations() -> None:
    cost_tracker = CostTracker()
    roi_tracker = ROITracker(cost_tracker)
    optimizer = CostOptimizer(cost_tracker, roi_tracker)

    # cost events
    cost_tracker.record_cost("c1", 120.0, category="api")
    cost_tracker.record_cost("c2", 80.0, category="storage")

    # value event lower than cost to trigger ROI recommendation
    roi_tracker.record_value("v1", 150.0)

    recs = optimizer.generate_recommendations(threshold=100.0, roi_threshold=200.0)
    assert any("api" in r for r in recs)
    assert any("ROI" in r for r in recs)
