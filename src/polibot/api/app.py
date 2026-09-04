from fastapi import FastAPI, Response, status

from polibot.monitoring import HealthService


def create_app(health_service: HealthService | None = None) -> FastAPI:
    service = health_service or HealthService()
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

    return app


app = create_app()

