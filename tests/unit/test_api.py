from fastapi.testclient import TestClient

from polibot.api.app import create_app
from polibot.monitoring import HealthService, PolibotMetrics


def test_health_fails_with_service_unavailable_when_required_check_fails() -> None:
    client = TestClient(create_app(HealthService({"reconciliation": lambda: False})))
    response = client.get("/health")
    assert response.status_code == 503
    assert response.json()["failures"] == ["reconciliation"]


def test_metrics_endpoint_is_prometheus_compatible() -> None:
    metrics = PolibotMetrics()
    metrics.stale_books.set(2)
    client = TestClient(create_app(metrics=metrics))
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "polibot_stale_books 2.0" in response.text
