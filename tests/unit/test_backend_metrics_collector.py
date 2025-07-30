from src.backend.metrics_collector import get_backend_collector


def test_get_backend_collector_singleton() -> None:
    a = get_backend_collector("service-a")
    b = get_backend_collector("service-a")
    assert a is b
