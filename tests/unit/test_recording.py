from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from uuid import UUID

import pytest

from polibot.storage import (
    InMemoryRecorder,
    ParquetArchive,
    RecordedEnvelope,
    RecordKind,
    canonical_payload,
)

NOW = datetime(2026, 9, 4, 12, tzinfo=UTC)


def record(ordinal: int = 0) -> RecordedEnvelope:
    return RecordedEnvelope(
        record_id=UUID(int=ordinal + 1),
        ordinal=ordinal,
        kind=RecordKind.BOOK_SNAPSHOT,
        market_id="market-1",
        token_id="token-yes",
        source_timestamp=NOW + timedelta(milliseconds=ordinal),
        received_at=NOW + timedelta(milliseconds=ordinal + 1),
        payload_json=canonical_payload({"price": Decimal("0.50"), "size": "10"}),
    )


def test_canonical_payload_is_stable_and_preserves_decimal_text() -> None:
    first = canonical_payload({"b": "value", "a": Decimal("0.500")})
    second = canonical_payload({"a": Decimal("0.500"), "b": "value"})
    assert first == second == '{"a":"0.500","b":"value"}'


def test_canonical_payload_rejects_float_recursively() -> None:
    with pytest.raises(ValueError, match="binary floating-point"):
        canonical_payload({"levels": [{"price": 0.5}]})


@pytest.mark.asyncio
async def test_recorder_is_append_only_and_rejects_duplicate_ids() -> None:
    recorder = InMemoryRecorder()
    item = record()
    await recorder.append(item)
    with pytest.raises(ValueError, match="duplicate record ID"):
        await recorder.append(item)
    assert await recorder.read_all() == (item,)


def test_parquet_archive_round_trip(tmp_path: Path) -> None:
    path = tmp_path / "market-1.parquet"
    items = (record(0), record(1))
    archive = ParquetArchive()
    archive.write(path, items)
    assert archive.read(path) == items
