from fastapi import FastAPI, Response, status

from polibot.config import ExecutionMode, Settings
from polibot.monitoring import HealthService, PolibotMetrics


def create_app(
    health_service: HealthService | None = None,
    metrics: PolibotMetrics | None = None,
    settings: Settings | None = None,
) -> FastAPI:
    service = health_service or HealthService()
    application_metrics = metrics or PolibotMetrics()
    runtime_settings = settings or Settings()
    app = FastAPI(title="Polibot Control API", version="0.1.0")

    @app.get("/health")
    async def health(response: Response) -> dict[str, object]:
        report = service.check()
        safety_failures = (
            ("unsafe_execution_mode",)
            if runtime_settings.execution_mode is ExecutionMode.LIVE
            or runtime_settings.live_trading_enabled
            else ()
        )
        failures = report.failures + safety_failures
        if failures:
            response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {
            "healthy": not failures,
            "checked_at": report.checked_at.isoformat(),
            "failures": failures,
            "execution_mode": runtime_settings.execution_mode.value,
            "live_trading_enabled": runtime_settings.live_trading_enabled,
        }

    @app.get("/metrics")
    async def prometheus_metrics() -> Response:
        return Response(
            application_metrics.render(),
            media_type="text/plain; version=0.0.4; charset=utf-8",
        )

    return app


app = create_app()
