from datetime import timedelta

from src.analytics.productivity_benchmark import AgentProductivityBenchmark


def test_productivity_score() -> None:
    benchmark = AgentProductivityBenchmark()
    benchmark.record_metrics(
        "a1",
        {"tasks_completed": 5, "tasks_failed": 1, "average_execution_time": 2.0},
    )
    score = benchmark.get_productivity_score("a1")
    assert 0.0 < score <= 100.0


def test_clear_old_records() -> None:
    benchmark = AgentProductivityBenchmark()
    benchmark.record_metrics(
        "a1",
        {"tasks_completed": 2, "tasks_failed": 0, "average_execution_time": 1.0},
    )
    benchmark.records[0].timestamp -= timedelta(hours=25)
    benchmark.clear_old_records()
    assert len(benchmark.records) == 0
