from datetime import UTC, datetime, timedelta
from uuid import UUID

from polibot.backtest import ReplayEngine, ReplayManifest
from polibot.storage import RecordedEnvelope, RecordKind

NOW = datetime(2026, 9, 4, 12, tzinfo=UTC)


def item(ordinal: int, source_offset: int, market_id: str = "m1") -> RecordedEnvelope:
    return RecordedEnvelope(
        record_id=UUID(int=ordinal + 1),
        ordinal=ordinal,
        kind=RecordKind.RAW_MARKET_MESSAGE,
        market_id=market_id,
        source_timestamp=NOW + timedelta(seconds=source_offset),
        received_at=NOW + timedelta(seconds=source_offset, milliseconds=ordinal),
        payload_json="{}",
    )


def manifest() -> ReplayManifest:
    return ReplayManifest(
        data_schema_version="1",
        strategy_version="test",
        configuration_fingerprint="sha256:test",
        latency_model="recorded-receipt-time",
        fee_model="recorded",
    )


def test_replay_is_deterministic_and_filters_market_and_time() -> None:
    records = [item(2, 2), item(0, 0), item(1, 1), item(3, 1, "other")]
    seen: list[int] = []
    result = ReplayEngine().run(
        records,
        manifest(),
        lambda record: seen.append(record.ordinal),
        market_id="m1",
        from_timestamp=NOW,
        to_timestamp=NOW + timedelta(seconds=1),
    )
    assert seen == [0, 1]
    assert result.processed == 2
    assert result.first_timestamp == NOW
    assert result.manifest == manifest()


def test_empty_replay_has_explicit_no_data_result() -> None:
    result = ReplayEngine().run([], manifest(), lambda _: None)
    assert result.processed == 0
    assert result.first_timestamp is None
    assert result.last_timestamp is None
