from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from datetime import datetime
from pathlib import Path

from polibot.backtest import ReplayEngine, ReplayManifest
from polibot.storage import ParquetArchive


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
    return root


def main(argv: Sequence[str] | None = None) -> int:
    arguments = parser().parse_args(argv)
    if arguments.command != "replay":
        return 2
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
