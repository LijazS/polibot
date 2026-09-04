from fastapi import FastAPI, Response, status

from polibot.monitoring import HealthService, PolibotMetrics


def create_app(
    health_service: HealthService | None = None, metrics: PolibotMetrics | None = None
) -> FastAPI:
    service = health_service or HealthService()
    application_metrics = metrics or PolibotMetrics()
    app = FastAPI(title="Polibot Control API", version="0.1.0")

    @app.get("/health")
    async def health(response: Response) -> dict[str, object]:
        report = service.check()
        if not report.healthy:
            response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {
            "healthy": report.healthy,
            "checked_at": report.checked_at.isoformat(),
            "failures": report.failures,
        }

    @app.get("/metrics")
    async def prometheus_metrics() -> Response:
        return Response(
            application_metrics.render(),
            media_type="text/plain; version=0.0.4; charset=utf-8",
        )

    return app


app = create_app()
