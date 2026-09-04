from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import datetime

from polibot.storage.records import RecordedEnvelope


@dataclass(frozen=True)
class ReplayManifest:
    data_schema_version: str
    strategy_version: str
    configuration_fingerprint: str
    latency_model: str
    fee_model: str


@dataclass(frozen=True)
class ReplayResult:
    manifest: ReplayManifest
    processed: int
    first_timestamp: datetime | None
    last_timestamp: datetime | None


class ReplayEngine:
    """Deterministic event replay with no network or execution dependency."""

    def run(
        self,
        records: Iterable[RecordedEnvelope],
        manifest: ReplayManifest,
        consumer: Callable[[RecordedEnvelope], None],
        *,
        market_id: str | None = None,
        from_timestamp: datetime | None = None,
        to_timestamp: datetime | None = None,
    ) -> ReplayResult:
        selected = [
            record
            for record in records
            if (market_id is None or record.market_id == market_id)
            and (from_timestamp is None or record.source_timestamp >= from_timestamp)
            and (to_timestamp is None or record.source_timestamp <= to_timestamp)
        ]
        ordered = sorted(
            selected,
            key=lambda record: (
                record.source_timestamp,
                record.received_at,
                record.ordinal,
                str(record.record_id),
            ),
        )
        for record in ordered:
            consumer(record)
        return ReplayResult(
            manifest=manifest,
            processed=len(ordered),
            first_timestamp=ordered[0].source_timestamp if ordered else None,
            last_timestamp=ordered[-1].source_timestamp if ordered else None,
        )
