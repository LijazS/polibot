from __future__ import annotations

import json
from collections.abc import Sequence
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation

from polibot.discovery.dto import GammaEventDTO, GammaMarketDTO, TokenPairDTO
from polibot.domain.models import Event, Market, OutcomeToken, Tradability


class InvalidMarketMetadata(ValueError):
    pass


def _string_array(value: object, field: str) -> tuple[str, ...]:
    parsed = value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError as exc:
            raise InvalidMarketMetadata(f"{field} is not valid JSON") from exc
    if not isinstance(parsed, Sequence) or isinstance(parsed, (str, bytes)):
        raise InvalidMarketMetadata(f"{field} must be an array")
    result = tuple(item.strip() for item in parsed if isinstance(item, str) and item.strip())
    if len(result) != len(parsed):
        raise InvalidMarketMetadata(f"{field} contains a non-string or empty value")
    return result


def _decimal(value: object, field: str) -> Decimal | None:
    if value is None:
        return None
    if isinstance(value, (bool, float)):
        raise InvalidMarketMetadata(f"{field} must not use binary floating-point")
    try:
        result = Decimal(value) if isinstance(value, (str, int)) else value
    except InvalidOperation as exc:
        raise InvalidMarketMetadata(f"{field} is not a decimal") from exc
    if not isinstance(result, Decimal) or not result.is_finite():
        raise InvalidMarketMetadata(f"{field} is not a finite decimal")
    return result


def _timestamp(value: str | None, field: str) -> datetime | None:
    if value is None or not value.strip():
        return None
    normalized = value.replace("Z", "+00:00")
    try:
        result = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise InvalidMarketMetadata(f"{field} is not an ISO-8601 timestamp") from exc
    if result.tzinfo is None or result.utcoffset() is None:
        raise InvalidMarketMetadata(f"{field} must include a timezone")
    return result.astimezone(UTC)


def _token_mapping(
    dto: GammaMarketDTO, verification: TokenPairDTO | None
) -> tuple[OutcomeToken, ...]:
    outcomes = _string_array(dto.outcomes, "outcomes")
    token_ids = _string_array(dto.clob_token_ids, "clobTokenIds")
    if len(outcomes) != 2 or {item.casefold() for item in outcomes} != {"yes", "no"}:
        raise InvalidMarketMetadata("binary market must have exactly Yes and No outcomes")
    if len(token_ids) != 2 or len(set(token_ids)) != 2:
        raise InvalidMarketMetadata("binary market must have two unique token IDs")
    if dto.condition_id is None or verification is None:
        raise InvalidMarketMetadata("authoritative Yes/No token verification is required")
    if verification.condition_id != dto.condition_id:
        raise InvalidMarketMetadata("token verification condition does not match market")
    if set(token_ids) != {verification.primary_token_id, verification.secondary_token_id}:
        raise InvalidMarketMetadata("verified token IDs do not match market token IDs")
    return (
        OutcomeToken(
            token_id=verification.primary_token_id,
            market_id=dto.id,
            condition_id=dto.condition_id,
            outcome="YES",
        ),
        OutcomeToken(
            token_id=verification.secondary_token_id,
            market_id=dto.id,
            condition_id=dto.condition_id,
            outcome="NO",
        ),
    )


def extract_token_ids(dto: GammaMarketDTO) -> tuple[str, ...]:
    """Return unassigned IDs for verification lookup; this does not infer outcomes."""
    return _string_array(dto.clob_token_ids, "clobTokenIds")


def classify_tradability(dto: GammaMarketDTO, metadata_valid: bool) -> Tradability:
    if not metadata_valid:
        return Tradability.INVALID_METADATA
    if dto.closed or not dto.active:
        return Tradability.CLOSED
    if dto.restricted:
        return Tradability.RESTRICTED
    if not dto.enable_order_book:
        return Tradability.ORDERBOOK_DISABLED
    if not dto.accepting_orders:
        return Tradability.DISCOVERED
    return Tradability.TRADABLE


def normalize_market(
    dto: GammaMarketDTO,
    observed_at: datetime,
    verification: TokenPairDTO | None,
    event_id: str | None = None,
) -> Market:
    if observed_at.tzinfo is None or observed_at.utcoffset() is None:
        raise InvalidMarketMetadata("observed_at must be timezone-aware")
    try:
        tokens = _token_mapping(dto, verification)
        tick_size = _decimal(dto.minimum_tick_size, "orderPriceMinTickSize")
        minimum_size = _decimal(dto.minimum_order_size, "orderMinSize")
        if tick_size is None or minimum_size is None:
            raise InvalidMarketMetadata("tick size and minimum order size are required")
        resolved_event_id = event_id or (dto.events[0].id if len(dto.events) == 1 else None)
        return Market(
            market_id=dto.id,
            event_id=resolved_event_id,
            condition_id=dto.condition_id,
            question_id=dto.question_id,
            slug=dto.slug,
            title=dto.question,
            outcome_tokens=tokens,
            active=dto.active,
            closed=dto.closed,
            accepting_orders=dto.accepting_orders,
            enable_order_book=dto.enable_order_book,
            restricted=dto.restricted,
            neg_risk=dto.neg_risk,
            tradability=classify_tradability(dto, metadata_valid=True),
            minimum_tick_size=tick_size,
            minimum_order_size=minimum_size,
            start_at=_timestamp(dto.start_date, "startDate"),
            end_at=_timestamp(dto.end_date, "endDate"),
            metadata_observed_at=observed_at.astimezone(UTC),
        )
    except (InvalidMarketMetadata, ValueError) as exc:
        if isinstance(exc, InvalidMarketMetadata):
            raise
        raise InvalidMarketMetadata(str(exc)) from exc


def normalize_event(dto: GammaEventDTO) -> Event:
    return Event(
        event_id=dto.id,
        slug=dto.slug,
        title=dto.title,
        start_at=_timestamp(dto.start_date, "startDate"),
        end_at=_timestamp(dto.end_date, "endDate"),
        active=dto.active,
        closed=dto.closed,
        restricted=dto.restricted,
        neg_risk=dto.neg_risk,
        mutually_exclusive=True if dto.neg_risk else None,
        market_ids=tuple(market.id for market in dto.markets),
    )
