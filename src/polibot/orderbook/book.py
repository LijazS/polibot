from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal, InvalidOperation
from enum import StrEnum

from polibot.domain.models import BookLevel, OrderBook
from polibot.market_data.messages import (
    BookMessage,
    LastTradeMessage,
    PriceChangeMessage,
    TickSizeChangeMessage,
)


class BookState(StrEnum):
    AWAITING_SNAPSHOT = "awaiting_snapshot"
    READY = "ready"
    INVALID = "invalid"
    STALE = "stale"


class InvalidBookUpdate(ValueError):
    pass


def _decimal(value: str, field: str) -> Decimal:
    try:
        result = Decimal(value)
    except InvalidOperation as exc:
        raise InvalidBookUpdate(f"{field} is not a decimal") from exc
    if not result.is_finite():
        raise InvalidBookUpdate(f"{field} must be finite")
    return result


def _timestamp_ms(value: str) -> datetime:
    timestamp = _decimal(value, "timestamp")
    if timestamp < 0 or timestamp != timestamp.to_integral_value():
        raise InvalidBookUpdate("timestamp must be a non-negative integer in milliseconds")
    return datetime(1970, 1, 1, tzinfo=UTC) + timedelta(milliseconds=int(timestamp))


class NormalizedOrderBook:
    """Single-token L2 book that becomes usable only after a valid full snapshot."""

    def __init__(self, market_id: str, token_id: str, tick_size: Decimal) -> None:
        if not market_id or not token_id or tick_size <= 0:
            raise ValueError("market_id, token_id, and positive tick_size are required")
        self.market_id = market_id
        self.token_id = token_id
        self.tick_size = tick_size
        self.state = BookState.AWAITING_SNAPSHOT
        self.last_source_timestamp: datetime | None = None
        self.last_received_at: datetime | None = None
        self.last_hash: str | None = None
        self.last_trade_price: Decimal | None = None
        self._bids: dict[Decimal, Decimal] = {}
        self._asks: dict[Decimal, Decimal] = {}

    def apply_snapshot(self, message: BookMessage, received_at: datetime) -> None:
        try:
            self._validate_identity(message.market, message.asset_id)
            bids = self._levels(message.bids, "bid")
            asks = self._levels(message.asks, "ask")
            self._validate_not_crossed(bids, asks)
            self._bids = bids
            self._asks = asks
            self.last_source_timestamp = _timestamp_ms(message.timestamp)
            self.last_received_at = self._aware(received_at)
            self.last_hash = message.hash
            self.state = BookState.READY
        except (InvalidBookUpdate, ValueError):
            self.invalidate()
            raise

    def apply_price_change(self, message: PriceChangeMessage, received_at: datetime) -> None:
        if self.state is not BookState.READY:
            raise InvalidBookUpdate("book requires a valid snapshot before deltas")
        try:
            if message.market != self.market_id:
                raise InvalidBookUpdate("delta market does not match book")
            source_timestamp = _timestamp_ms(message.timestamp)
            if (
                self.last_source_timestamp is not None
                and source_timestamp < self.last_source_timestamp
            ):
                raise InvalidBookUpdate("out-of-order timestamp invalidates the book")
            for change in message.price_changes:
                if change.asset_id != self.token_id:
                    continue
                price = self._valid_price(change.price)
                size = self._valid_size(change.size)
                levels = self._bids if change.side == "BUY" else self._asks
                if size == 0:
                    levels.pop(price, None)
                else:
                    levels[price] = size
                if change.hash:
                    self.last_hash = change.hash
            self._validate_not_crossed(self._bids, self._asks)
            self.last_source_timestamp = source_timestamp
            self.last_received_at = self._aware(received_at)
        except (InvalidBookUpdate, ValueError):
            self.invalidate()
            raise

    def apply_tick_change(self, message: TickSizeChangeMessage, received_at: datetime) -> None:
        try:
            self._validate_identity(message.market, message.asset_id)
            old_tick = _decimal(message.old_tick_size, "old_tick_size")
            new_tick = _decimal(message.new_tick_size, "new_tick_size")
            if old_tick != self.tick_size or new_tick <= 0:
                raise InvalidBookUpdate("tick-size transition does not match current book")
            self.tick_size = new_tick
            if any(price % new_tick != 0 for price in (*self._bids, *self._asks)):
                raise InvalidBookUpdate("existing level is invalid under new tick size")
            self.last_source_timestamp = _timestamp_ms(message.timestamp)
            self.last_received_at = self._aware(received_at)
        except (InvalidBookUpdate, ValueError):
            self.invalidate()
            raise

    def apply_last_trade(self, message: LastTradeMessage, received_at: datetime) -> None:
        try:
            self._validate_identity(message.market, message.asset_id)
            self.last_trade_price = self._valid_price(message.price)
            self._valid_size(message.size)
            self.last_source_timestamp = _timestamp_ms(message.timestamp)
            self.last_received_at = self._aware(received_at)
        except (InvalidBookUpdate, ValueError):
            self.invalidate()
            raise

    def invalidate(self) -> None:
        self.state = BookState.INVALID

    def mark_disconnected(self) -> None:
        self.invalidate()

    def refresh_staleness(self, now: datetime, maximum_age: timedelta) -> BookState:
        now = self._aware(now)
        if maximum_age <= timedelta(0):
            raise ValueError("maximum_age must be positive")
        if self.state is BookState.READY and (
            self.last_received_at is None or now - self.last_received_at > maximum_age
        ):
            self.state = BookState.STALE
        return self.state

    def snapshot(self) -> OrderBook:
        if self.state is not BookState.READY:
            raise InvalidBookUpdate("only a ready book can produce a strategy snapshot")
        if self.last_source_timestamp is None or self.last_received_at is None:
            self.invalidate()
            raise InvalidBookUpdate("ready book is missing timestamps")
        return OrderBook(
            market_id=self.market_id,
            token_id=self.token_id,
            bids=tuple(
                BookLevel(price=price, quantity=size)
                for price, size in sorted(self._bids.items(), reverse=True)
            ),
            asks=tuple(
                BookLevel(price=price, quantity=size) for price, size in sorted(self._asks.items())
            ),
            source_timestamp=self.last_source_timestamp,
            received_at=self.last_received_at,
            sequence=None,
        )

    def _levels(self, levels: tuple[object, ...], side: str) -> dict[Decimal, Decimal]:
        result: dict[Decimal, Decimal] = {}
        for item in levels:
            price_value = getattr(item, "price", None)
            size_value = getattr(item, "size", None)
            if not isinstance(price_value, str) or not isinstance(size_value, str):
                raise InvalidBookUpdate(f"invalid {side} level")
            price = self._valid_price(price_value)
            size = self._valid_size(size_value)
            if size == 0 or price in result:
                raise InvalidBookUpdate(f"invalid or duplicate {side} level")
            result[price] = size
        return result

    def _valid_price(self, value: str) -> Decimal:
        price = _decimal(value, "price")
        if not Decimal("0") <= price <= Decimal("1") or price % self.tick_size != 0:
            raise InvalidBookUpdate("price is outside bounds or not tick-aligned")
        return price

    @staticmethod
    def _valid_size(value: str) -> Decimal:
        size = _decimal(value, "size")
        if size < 0:
            raise InvalidBookUpdate("size must be non-negative")
        return size

    @staticmethod
    def _validate_not_crossed(bids: dict[Decimal, Decimal], asks: dict[Decimal, Decimal]) -> None:
        if bids and asks and max(bids) >= min(asks):
            raise InvalidBookUpdate("crossed or locked book is unsafe")

    def _validate_identity(self, market_id: str, token_id: str) -> None:
        if market_id != self.market_id or token_id != self.token_id:
            raise InvalidBookUpdate("message identity does not match book")

    @staticmethod
    def _aware(value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise InvalidBookUpdate("received timestamp must be timezone-aware")
        return value.astimezone(UTC)
