from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from typing import Any

from fastapi import FastAPI, Response, status
from sqlalchemy.ext.asyncio import async_sessionmaker

from polibot.config import ExecutionMode, Settings
from polibot.monitoring import HealthService, PolibotMetrics
from polibot.storage import WorkerStateStore, build_engine

WorkerStatusReader = Callable[[], Awaitable[dict[str, Any] | None]]


def create_app(
    health_service: HealthService | None = None,
    metrics: PolibotMetrics | None = None,
    settings: Settings | None = None,
    worker_status: WorkerStatusReader | None = None,
) -> FastAPI:
    service = health_service or HealthService()
    application_metrics = metrics or PolibotMetrics()
    runtime_settings = settings or Settings()
    app = FastAPI(title="Polibot Control API", version="0.1.0")

    async def read_worker() -> tuple[dict[str, Any] | None, tuple[str, ...]]:
        if worker_status is None:
            return None, ()
        try:
            value = await worker_status()
        except Exception:
            return None, ("worker_status_unavailable",)
        if value is None:
            return None, ("worker_missing",)
        heartbeat = value.get("last_heartbeat_at")
        if not isinstance(heartbeat, datetime):
            return value, ("worker_heartbeat_invalid",)
        maximum_age = max(runtime_settings.worker_heartbeat_seconds * 3, 30)
        if (datetime.now(UTC) - heartbeat).total_seconds() > maximum_age:
            return value, ("worker_stale",)
        if value.get("current_status") not in {"running", "starting"}:
            return value, ("worker_degraded",)
        return value, ()

    @app.get("/health")
    async def health(response: Response) -> dict[str, object]:
        report = service.check()
        worker, worker_failures = await read_worker()
        safety_failures = (
            ("unsafe_execution_mode",)
            if runtime_settings.execution_mode is ExecutionMode.LIVE
            or runtime_settings.live_trading_enabled
            else ()
        )
        failures = report.failures + safety_failures + worker_failures
        if failures:
            response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {
            "healthy": not failures,
            "checked_at": report.checked_at.isoformat(),
            "failures": failures,
            "execution_mode": runtime_settings.execution_mode.value,
            "live_trading_enabled": runtime_settings.live_trading_enabled,
            "worker": worker,
        }

    @app.get("/ready")
    async def readiness(response: Response) -> dict[str, object]:
        worker, failures = await read_worker()
        ready = not failures and worker is not None and worker.get("ready") is True
        if not ready:
            response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"ready": ready, "failures": failures, "worker": worker}

    @app.get("/status")
    async def runtime_status(response: Response) -> dict[str, object]:
        worker, failures = await read_worker()
        if failures:
            response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        activity = {
            "discovered": worker.get("markets_discovered", 0) if worker else 0,
            "selected": worker.get("markets_selected", 0) if worker else 0,
            "subscribed_tokens": worker.get("markets_subscribed", 0) if worker else 0,
            "books_healthy": worker.get("books_healthy", 0) if worker else 0,
            "books_stale": worker.get("books_stale", 0) if worker else 0,
            "messages_received": worker.get("messages_received", 0) if worker else 0,
        }
        paper = {
            "starting_capital": worker.get("paper_initial_capital", "0") if worker else "0",
            "current_capital": worker.get("paper_current_capital", "0") if worker else "0",
            "gross_pnl": worker.get("paper_gross_pnl", "0") if worker else "0",
            "fees": worker.get("paper_fees", "0") if worker else "0",
            "slippage": worker.get("paper_slippage", "0") if worker else "0",
            "net_pnl": worker.get("paper_net_pnl", "0") if worker else "0",
            "executions": worker.get("paper_executions", 0) if worker else 0,
        }
        system = {
            "database_size_bytes": worker.get("database_size_bytes", 0) if worker else 0,
            "disk_used_percent": worker.get("disk_used_percent", "0") if worker else "0",
            "recorder_queue_depth": worker.get("recorder_queue_depth", 0) if worker else 0,
            "recorder_dropped_events": (worker.get("recorder_dropped_events", 0) if worker else 0),
            "database_errors": worker.get("database_errors", 0) if worker else 0,
        }
        return {
            "mode": runtime_settings.execution_mode.value,
            "live_trading": runtime_settings.live_trading_enabled,
            "failures": failures,
            "worker": worker,
            "markets": activity,
            "strategies": {
                "binary_complete_set": {
                    "enabled": True,
                    "evaluations": worker.get("strategy_evaluations", 0) if worker else 0,
                    "opportunities": worker.get("opportunities_detected", 0) if worker else 0,
                    "approvals": worker.get("risk_approvals", 0) if worker else 0,
                },
                "vanilla_negrisk": {"enabled": False},
            },
            "paper": paper,
            "system": system,
        }

    @app.get("/metrics")
    async def prometheus_metrics() -> Response:
        return Response(
            application_metrics.render(),
            media_type="text/plain; version=0.0.4; charset=utf-8",
        )

    return app


_settings = Settings()
_engine = build_engine(_settings.database_url)
_sessions = async_sessionmaker(_engine, expire_on_commit=False)
_worker_store = WorkerStateStore(_sessions)
app = create_app(settings=_settings, worker_status=_worker_store.latest_status)
