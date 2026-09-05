import asyncio
from datetime import UTC, datetime
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from polibot.api.app import create_app
from polibot.config import ExecutionMode, Settings
from polibot.domain.models import Market, OutcomeToken, Tradability
from polibot.storage import BatchedPostgresRecorder, RecordedEnvelope, RecordKind
from polibot.worker import UnsafeWorkerConfiguration, run_worker, select_binary_markets


def market(market_id: str, *, neg_risk: bool = False) -> Market:
    return Market(
        market_id=market_id,
        condition_id=f"condition-{market_id}",
        outcome_tokens=(
            OutcomeToken(
                token_id=f"yes-{market_id}",
                market_id=market_id,
                condition_id=f"condition-{market_id}",
                outcome="YES",
            ),
            OutcomeToken(
                token_id=f"no-{market_id}",
                market_id=market_id,
                condition_id=f"condition-{market_id}",
                outcome="NO",
            ),
        ),
        active=True,
        accepting_orders=True,
        enable_order_book=True,
        neg_risk=neg_risk,
        tradability=Tradability.TRADABLE,
        minimum_tick_size=Decimal("0.01"),
        minimum_order_size=Decimal("5"),
        metadata_observed_at=datetime.now(UTC),
    )


def test_market_selection_is_deterministic_bounded_and_excludes_negrisk() -> None:
    selected, decisions = select_binary_markets(
        (market("first"), market("neg", neg_risk=True), market("last")), maximum=1
    )
    assert [item.market_id for item in selected] == ["first"]
    assert [item.reason for item in decisions] == [
        "selected",
        "negrisk_requires_validated_event_structure",
        "selection_limit",
    ]


@pytest.mark.asyncio
async def test_worker_hard_rejects_live_before_opening_dependencies() -> None:
    with pytest.raises(UnsafeWorkerConfiguration, match="refuses LIVE"):
        await run_worker(
            Settings(
                execution_mode=ExecutionMode.LIVE,
                live_trading_enabled=True,
                _env_file=None,
            )
        )


def test_api_distinguishes_current_worker_health_and_readiness() -> None:
    now = datetime.now(UTC)

    async def status() -> dict[str, object]:
        return {
            "last_heartbeat_at": now,
            "current_status": "running",
            "ready": True,
            "markets_discovered": 10,
            "markets_selected": 2,
            "markets_subscribed": 4,
            "books_healthy": 4,
            "books_stale": 0,
            "messages_received": 20,
        }

    client = TestClient(create_app(worker_status=status))
    assert client.get("/health").status_code == 200
    assert client.get("/ready").json()["ready"] is True
    assert client.get("/status").json()["markets"]["messages_received"] == 20


def test_api_rejects_stale_worker_heartbeat() -> None:
    async def status() -> dict[str, object]:
        return {
            "last_heartbeat_at": datetime(2020, 1, 1, tzinfo=UTC),
            "current_status": "running",
            "ready": True,
        }

    response = TestClient(create_app(worker_status=status)).get("/health")
    assert response.status_code == 503
    assert "worker_stale" in response.json()["failures"]


@pytest.mark.asyncio
async def test_batched_recorder_flushes_on_graceful_shutdown() -> None:
    written: list[RecordedEnvelope] = []
    recorder = BatchedPostgresRecorder(  # type: ignore[arg-type]
        None, batch_size=10, flush_seconds=0.01, queue_size=100
    )

    async def write(records: tuple[RecordedEnvelope, ...]) -> None:
        written.extend(records)

    recorder._write = write  # type: ignore[method-assign]
    await recorder.start()
    now = datetime.now(UTC)
    await recorder.append(
        RecordedEnvelope(
            ordinal=1,
            kind=RecordKind.BOOK_SNAPSHOT,
            market_id="m1",
            token_id="t1",
            source_timestamp=now,
            received_at=now,
            payload_json="{}",
        )
    )
    await asyncio.sleep(0)
    await recorder.close()
    assert len(written) == 1
    assert recorder.queue_depth == 0
