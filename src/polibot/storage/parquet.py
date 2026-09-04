from __future__ import annotations

from pathlib import Path

import polars as pl

from polibot.storage.records import RecordedEnvelope


class ParquetArchive:
    SCHEMA_VERSION = "1"

    def write(self, path: Path, records: tuple[RecordedEnvelope, ...]) -> None:
        rows = [
            {
                "schema_version": self.SCHEMA_VERSION,
                "record_id": str(record.record_id),
                "ordinal": record.ordinal,
                "kind": record.kind.value,
                "market_id": record.market_id,
                "token_id": record.token_id,
                "source_timestamp": record.source_timestamp,
                "received_at": record.received_at,
                "payload_json": record.payload_json,
            }
            for record in records
        ]
        frame = pl.DataFrame(rows)
        path.parent.mkdir(parents=True, exist_ok=True)
        frame.write_parquet(path)

    def read(self, path: Path) -> tuple[RecordedEnvelope, ...]:
        frame = pl.read_parquet(path)
        versions = set(frame.get_column("schema_version").to_list())
        if versions != {self.SCHEMA_VERSION}:
            raise ValueError("unsupported or mixed Parquet schema version")
        return tuple(
            RecordedEnvelope.model_validate(
                {
                    "record_id": row["record_id"],
                    "ordinal": row["ordinal"],
                    "kind": row["kind"],
                    "market_id": row["market_id"],
                    "token_id": row["token_id"],
                    "source_timestamp": row["source_timestamp"],
                    "received_at": row["received_at"],
                    "payload_json": row["payload_json"],
                }
            )
            for row in frame.iter_rows(named=True)
        )
