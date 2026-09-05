from __future__ import annotations

import argparse
import asyncio
import json
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy.ext.asyncio import async_sessionmaker

from polibot.backtest import ReplayEngine, ReplayManifest
from polibot.config import Settings
from polibot.storage import ParquetArchive, WorkerStateStore, build_engine


def _timestamp(value: str | None) -> datetime | None:
    if value is None:
        return None
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.tzinfo is None or result.utcoffset() is None:
        raise argparse.ArgumentTypeError("timestamps must include a timezone")
    return result


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="polibot")
    commands = root.add_subparsers(dest="command", required=True)
    replay = commands.add_parser("replay", help="replay a versioned Parquet event archive")
    replay.add_argument("archive", type=Path)
    replay.add_argument("--market")
    replay.add_argument("--from", dest="from_timestamp")
    replay.add_argument("--to", dest="to_timestamp")
    replay.add_argument("--strategy-version", required=True)
    replay.add_argument("--config-fingerprint", required=True)
    replay.add_argument("--latency-model", required=True)
    replay.add_argument("--fee-model", required=True)
    commands.add_parser("worker", help="run the continuous public-data PAPER worker")
    commands.add_parser("status", help="show the latest durable worker status")
    commands.add_parser("markets", help="show market discovery and book counts")
    opportunities = commands.add_parser("opportunities", help="show recorded opportunity counts")
    opportunities.add_argument("--last", default="1h")
    commands.add_parser("paper-pnl", help="show the durable paper account summary")
    commands.add_parser("worker-runs", help="show recent worker runs")
    books = commands.add_parser("books", help="show durable book health counts")
    books.add_argument("--stale", action="store_true")
    report = commands.add_parser("report", help="produce a read-only recorded-data report")
    report.add_argument("period", choices=("daily",))
    return root


def _json_default(value: object) -> str:
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


async def _operational_report(command: str) -> object:
    settings = Settings()
    engine = build_engine(settings.database_url)
    try:
        store = WorkerStateStore(async_sessionmaker(engine, expire_on_commit=False))
        latest = await store.latest_status()
        since = (
            datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
            if command == "report"
            else None
        )
        counts = await store.activity_counts(since)
        if command == "worker-runs":
            return await store.recent_runs()
        if latest is None:
            return {"status": "worker_missing", "activity": counts}
        if command == "markets":
            return {
                "markets_discovered": latest["markets_discovered"],
                "markets_selected": latest["markets_selected"],
                "subscribed_tokens": latest["markets_subscribed"],
                "books_healthy": latest["books_healthy"],
                "books_stale": latest["books_stale"],
            }
        if command == "opportunities":
            return {
                "opportunities_detected": latest["opportunities_detected"],
                "recorded_proposals": counts.get("proposal", 0),
                "risk_decisions": counts.get("risk_decision", 0),
            }
        if command == "paper-pnl":
            return {
                "starting_capital": latest["paper_initial_capital"],
                "current_capital": latest["paper_current_capital"],
                "gross_pnl": latest["paper_gross_pnl"],
                "fees": latest["paper_fees"],
                "slippage": latest["paper_slippage"],
                "net_pnl": latest["paper_net_pnl"],
            }
        if command == "books":
            return {
                "healthy": latest["books_healthy"],
                "stale": latest["books_stale"],
            }
        if command == "report":
            return {"worker": latest, "recorded_activity": counts}
        return latest
    finally:
        await engine.dispose()


def main(argv: Sequence[str] | None = None) -> int:
    arguments = parser().parse_args(argv)
    if arguments.command == "worker":
        from polibot.worker import run_worker

        asyncio.run(run_worker())
        return 0
    if arguments.command != "replay":
        result = asyncio.run(_operational_report(arguments.command))
        print(json.dumps(result, sort_keys=True, default=_json_default))
        return 0
    records = ParquetArchive().read(arguments.archive)
    manifest = ReplayManifest(
        data_schema_version=ParquetArchive.SCHEMA_VERSION,
        strategy_version=arguments.strategy_version,
        configuration_fingerprint=arguments.config_fingerprint,
        latency_model=arguments.latency_model,
        fee_model=arguments.fee_model,
    )
    result = ReplayEngine().run(
        records,
        manifest,
        lambda _: None,
        market_id=arguments.market,
        from_timestamp=_timestamp(arguments.from_timestamp),
        to_timestamp=_timestamp(arguments.to_timestamp),
    )
    print(
        json.dumps(
            {
                "processed": result.processed,
                "first_timestamp": (
                    result.first_timestamp.isoformat() if result.first_timestamp else None
                ),
                "last_timestamp": (
                    result.last_timestamp.isoformat() if result.last_timestamp else None
                ),
                "manifest": {
                    "data_schema_version": manifest.data_schema_version,
                    "strategy_version": manifest.strategy_version,
                    "configuration_fingerprint": manifest.configuration_fingerprint,
                    "latency_model": manifest.latency_model,
                    "fee_model": manifest.fee_model,
                },
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
