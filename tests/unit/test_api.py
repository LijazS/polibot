from fastapi.testclient import TestClient

from polibot.api.app import create_app
from polibot.config import ExecutionMode, Settings
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


def test_health_reports_safe_runtime_mode() -> None:
    response = TestClient(create_app(settings=Settings(_env_file=None))).get("/health")
    assert response.status_code == 200
    assert response.json()["execution_mode"] == "paper"
    assert response.json()["live_trading_enabled"] is False


def test_health_fails_closed_for_live_configuration() -> None:
    unsafe = Settings(
        execution_mode=ExecutionMode.LIVE,
        live_trading_enabled=True,
        _env_file=None,
    )
    response = TestClient(create_app(settings=unsafe)).get("/health")
    assert response.status_code == 503
    assert "unsafe_execution_mode" in response.json()["failures"]
