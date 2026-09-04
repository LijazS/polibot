from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import ROUND_DOWN, Decimal
from enum import StrEnum
from uuid import UUID, uuid4

from polibot.domain.models import OrderBook


class QuoteSide(StrEnum):
    BUY = "BUY"
    SELL = "SELL"


@dataclass(frozen=True)
class ShadowQuote:
    quote_id: UUID
    market_id: str
    token_id: str
    side: QuoteSide
    price: Decimal
    quantity: Decimal
    expires_at: datetime
    post_only: bool


@dataclass(frozen=True)
class MarketMakingObservation:
    midpoint: Decimal
    microprice: Decimal
    imbalance: Decimal
    fair_value: Decimal
    quotes: tuple[ShadowQuote, ...]
    shutdown_reasons: tuple[str, ...]
    assumptions: tuple[str, ...]


@dataclass(frozen=True)
class ShadowMarketMakingConfig:
    half_spread: Decimal
    quote_quantity: Decimal
    maximum_inventory: Decimal
    inventory_skew_per_unit: Decimal
    maximum_volatility: Decimal
    minimum_time_to_resolution: timedelta
    quote_ttl: timedelta = timedelta(seconds=2)

    def __post_init__(self) -> None:
        financial = (
            self.half_spread,
            self.quote_quantity,
            self.maximum_inventory,
            self.inventory_skew_per_unit,
            self.maximum_volatility,
        )
        if any(isinstance(value, float) for value in financial):
            raise ValueError("market-making financial values must use Decimal")
        if self.half_spread <= 0 or self.quote_quantity <= 0 or self.maximum_inventory <= 0:
            raise ValueError("spread, size, and inventory limit must be positive")


class ShadowMarketMaker:
    """Research-only quote generator. It has no execution or adapter dependency."""

    def __init__(self, config: ShadowMarketMakingConfig) -> None:
        self._config = config

    def observe(
        self,
        book: OrderBook,
        *,
        inventory: Decimal,
        volatility: Decimal,
        resolution_at: datetime,
        now: datetime,
        event_risk: bool = False,
    ) -> MarketMakingObservation:
        if any(isinstance(value, float) for value in (inventory, volatility)):
            raise ValueError("market-making inputs must use Decimal")
        if not book.bids or not book.asks:
            return self._shutdown("empty_book")
        best_bid, best_ask = book.bids[0], book.asks[0]
        if best_bid.price >= best_ask.price:
            return self._shutdown("crossed_or_locked_book")
        midpoint = (best_bid.price + best_ask.price) / Decimal("2")
        total_top = best_bid.quantity + best_ask.quantity
        microprice = (
            best_ask.price * best_bid.quantity + best_bid.price * best_ask.quantity
        ) / total_top
        imbalance = (best_bid.quantity - best_ask.quantity) / total_top
        reasons: list[str] = []
        if abs(inventory) >= self._config.maximum_inventory:
            reasons.append("inventory_limit")
        if volatility > self._config.maximum_volatility:
            reasons.append("volatility_limit")
        if resolution_at - now < self._config.minimum_time_to_resolution:
            reasons.append("resolution_too_close")
        if event_risk:
            reasons.append("event_risk")
        if reasons:
            return MarketMakingObservation(
                midpoint,
                microprice,
                imbalance,
                microprice,
                (),
                tuple(reasons),
                self._assumptions(),
            )
        fair_value = microprice - inventory * self._config.inventory_skew_per_unit
        bid = min(fair_value - self._config.half_spread, best_bid.price)
        ask = max(fair_value + self._config.half_spread, best_ask.price)
        bid = max(Decimal("0"), bid).quantize(Decimal("0.000001"), rounding=ROUND_DOWN)
        ask = min(Decimal("1"), ask).quantize(Decimal("0.000001"), rounding=ROUND_DOWN)
        if bid >= ask:
            return MarketMakingObservation(
                midpoint,
                microprice,
                imbalance,
                fair_value,
                (),
                ("unsafe_quote_spread",),
                self._assumptions(),
            )
        quotes = (
            ShadowQuote(
                uuid4(),
                book.market_id,
                book.token_id,
                QuoteSide.BUY,
                bid,
                self._config.quote_quantity,
                now + self._config.quote_ttl,
                True,
            ),
            ShadowQuote(
                uuid4(),
                book.market_id,
                book.token_id,
                QuoteSide.SELL,
                ask,
                self._config.quote_quantity,
                now + self._config.quote_ttl,
                True,
            ),
        )
        return MarketMakingObservation(
            midpoint,
            microprice,
            imbalance,
            fair_value,
            quotes,
            (),
            self._assumptions(),
        )

    def _shutdown(self, reason: str) -> MarketMakingObservation:
        zero = Decimal("0")
        return MarketMakingObservation(zero, zero, zero, zero, (), (reason,), self._assumptions())

    @staticmethod
    def _assumptions() -> tuple[str, ...]:
        return (
            "shadow_only_no_submission",
            "top_level_microprice",
            "post_only_quotes_do_not_imply_fill",
            "queue_priority_and_adverse_selection_require replay calibration",
            "fees_rebates_rewards_are separate dynamic inputs",
        )
