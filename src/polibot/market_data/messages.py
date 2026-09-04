from __future__ import annotations

import json
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter


class MarketMessage(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True)


class LevelDTO(MarketMessage):
    price: str
    size: str


class BookMessage(MarketMessage):
    event_type: Literal["book"]
    asset_id: str
    market: str
    bids: tuple[LevelDTO, ...]
    asks: tuple[LevelDTO, ...]
    timestamp: str
    hash: str


class PriceChangeDTO(MarketMessage):
    asset_id: str
    price: str
    size: str
    side: Literal["BUY", "SELL"]
    hash: str | None = None
    best_bid: str | None = None
    best_ask: str | None = None


class PriceChangeMessage(MarketMessage):
    event_type: Literal["price_change"]
    market: str
    price_changes: tuple[PriceChangeDTO, ...]
    timestamp: str


class LastTradeMessage(MarketMessage):
    event_type: Literal["last_trade_price"]
    asset_id: str
    market: str
    price: str
    size: str
    fee_rate_bps: str
    side: Literal["BUY", "SELL"]
    timestamp: str
    transaction_hash: str | None = None


class TickSizeChangeMessage(MarketMessage):
    event_type: Literal["tick_size_change"]
    asset_id: str
    market: str
    old_tick_size: str
    new_tick_size: str
    timestamp: str


NormalizedMarketMessage = Annotated[
    BookMessage | PriceChangeMessage | LastTradeMessage | TickSizeChangeMessage,
    Field(discriminator="event_type"),
]
_MESSAGE_ADAPTER: TypeAdapter[NormalizedMarketMessage] = TypeAdapter(NormalizedMarketMessage)


def parse_market_message(raw: str) -> NormalizedMarketMessage:
    payload = json.loads(raw, parse_float=Decimal)
    return _MESSAGE_ADAPTER.validate_python(payload)
