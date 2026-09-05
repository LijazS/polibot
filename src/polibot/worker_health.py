from __future__ import annotations

import asyncio
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import async_sessionmaker

from polibot.config import Settings
from polibot.storage import WorkerStateStore, build_engine


async def check() -> int:
    settings = Settings()
    if settings.execution_mode.value == "live" or settings.live_trading_enabled:
        return 1
    engine = build_engine(settings.database_url)
    try:
        status = await WorkerStateStore(
            async_sessionmaker(engine, expire_on_commit=False)
        ).latest_status()
        if status is None or status["current_status"] != "running":
            return 1
        age = (datetime.now(UTC) - status["last_heartbeat_at"]).total_seconds()
        return 0 if age <= max(settings.worker_heartbeat_seconds * 3, 30) else 1
    finally:
        await engine.dispose()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(check()))
