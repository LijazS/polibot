from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from polibot.market_data.messages import (
    BookMessage,
    LastTradeMessage,
    PriceChangeMessage,
    TickSizeChangeMessage,
    parse_market_message,
)
from polibot.orderbook import BookState, InvalidBookUpdate, NormalizedOrderBook

RECEIVED = datetime(2026, 9, 4, 12, tzinfo=UTC)


def snapshot(**updates: object) -> BookMessage:
    payload: dict[str, object] = {
        "event_type": "book",
        "asset_id": "token-yes",
        "market": "0xcondition",
        "bids": [{"price": "0.48", "size": "10"}, {"price": "0.47", "size": "20"}],
        "asks": [{"price": "0.52", "size": "15"}, {"price": "0.53", "size": "25"}],
        "timestamp": "1788523200000",
        "hash": "hash-1",
    }
    payload.update(updates)
    return BookMessage.model_validate(payload)


def ready_book() -> NormalizedOrderBook:
    book = NormalizedOrderBook("0xcondition", "token-yes", Decimal("0.01"))
    book.apply_snapshot(snapshot(), RECEIVED)
    return book


def test_snapshot_builds_sorted_ready_book_without_invented_sequence() -> None:
    result = ready_book().snapshot()
    assert [level.price for level in result.bids] == [Decimal("0.48"), Decimal("0.47")]
    assert [level.price for level in result.asks] == [Decimal("0.52"), Decimal("0.53")]
    assert result.sequence is None


def test_delta_inserts_updates_and_deletes_levels() -> None:
    book = ready_book()
    message = PriceChangeMessage.model_validate(
        {
            "event_type": "price_change",
            "market": "0xcondition",
            "timestamp": "1788523200001",
            "price_changes": [
                {"asset_id": "token-yes", "price": "0.48", "size": "12", "side": "BUY"},
                {"asset_id": "token-yes", "price": "0.47", "size": "0", "side": "BUY"},
                {"asset_id": "token-yes", "price": "0.54", "size": "4", "side": "SELL"},
            ],
        }
    )
    book.apply_price_change(message, RECEIVED + timedelta(milliseconds=1))
    result = book.snapshot()
    assert [(level.price, level.quantity) for level in result.bids] == [
        (Decimal("0.48"), Decimal("12.000000"))
    ]
    assert result.asks[-1].price == Decimal("0.54")


@pytest.mark.parametrize(
    "bad_snapshot",
    [
        snapshot(asks=[{"price": "0.48", "size": "1"}]),
        snapshot(bids=[{"price": "0.485", "size": "1"}]),
        snapshot(bids=[{"price": "0.48", "size": "-1"}]),
        snapshot(asset_id="wrong-token"),
    ],
)
def test_invalid_snapshot_fails_closed(bad_snapshot: BookMessage) -> None:
    book = NormalizedOrderBook("0xcondition", "token-yes", Decimal("0.01"))
    with pytest.raises(InvalidBookUpdate):
        book.apply_snapshot(bad_snapshot, RECEIVED)
    assert book.state is BookState.INVALID
    with pytest.raises(InvalidBookUpdate, match="ready book"):
        book.snapshot()


def test_out_of_order_delta_invalidates_book() -> None:
    book = ready_book()
    delta = PriceChangeMessage.model_validate(
        {
            "event_type": "price_change",
            "market": "0xcondition",
            "timestamp": "1",
            "price_changes": [
                {"asset_id": "token-yes", "price": "0.48", "size": "1", "side": "BUY"}
            ],
        }
    )
    with pytest.raises(InvalidBookUpdate, match="out-of-order"):
        book.apply_price_change(delta, RECEIVED)
    assert book.state is BookState.INVALID


def test_stale_or_disconnected_book_cannot_snapshot() -> None:
    book = ready_book()
    state = book.refresh_staleness(RECEIVED + timedelta(seconds=6), timedelta(seconds=5))
    assert state is BookState.STALE
    with pytest.raises(InvalidBookUpdate):
        book.snapshot()
    book.apply_snapshot(snapshot(hash="recovery"), RECEIVED + timedelta(seconds=7))
    assert book.state is BookState.READY
    book.mark_disconnected()
    assert book.state is BookState.INVALID


def test_tick_change_requires_consistent_transition() -> None:
    book = ready_book()
    change = TickSizeChangeMessage.model_validate(
        {
            "event_type": "tick_size_change",
            "asset_id": "token-yes",
            "market": "0xcondition",
            "old_tick_size": "0.01",
            "new_tick_size": "0.001",
            "timestamp": "1788523200001",
        }
    )
    book.apply_tick_change(change, RECEIVED)
    assert book.tick_size == Decimal("0.001")


def test_last_trade_is_validated_and_recorded() -> None:
    book = ready_book()
    trade = LastTradeMessage.model_validate(
        {
            "event_type": "last_trade_price",
            "asset_id": "token-yes",
            "market": "0xcondition",
            "price": "0.51",
            "size": "2",
            "fee_rate_bps": "0",
            "side": "BUY",
            "timestamp": "1788523200001",
        }
    )
    book.apply_last_trade(trade, RECEIVED)
    assert book.last_trade_price == Decimal("0.51")


def test_parser_uses_discriminated_official_message_shapes() -> None:
    message = parse_market_message(
        '{"event_type":"book","asset_id":"token-yes","market":"0xcondition",'
        '"bids":[],"asks":[],"timestamp":"1","hash":"h"}'
    )
    assert isinstance(message, BookMessage)
