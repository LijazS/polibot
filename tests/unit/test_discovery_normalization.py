import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from polibot.discovery.dto import GammaEventDTO, GammaMarketDTO, TokenPairDTO
from polibot.discovery.normalization import InvalidMarketMetadata, normalize_event, normalize_market
from polibot.domain.models import Tradability

FIXTURE = Path(__file__).parents[1] / "fixtures" / "gamma_market.json"
OBSERVED_AT = datetime(2026, 9, 4, 12, tzinfo=UTC)


def market_dto(**updates: object) -> GammaMarketDTO:
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    payload.update(updates)
    return GammaMarketDTO.model_validate(payload)


def verification(**updates: str) -> TokenPairDTO:
    payload = {
        "condition_id": "0xcondition",
        "primary_token_id": "token-yes",
        "secondary_token_id": "token-no",
    }
    payload.update(updates)
    return TokenPairDTO.model_validate(payload)


def test_normalizes_verified_binary_token_mapping() -> None:
    market = normalize_market(market_dto(), OBSERVED_AT, verification())
    assert market.tradability is Tradability.TRADABLE
    assert [(token.outcome, token.token_id) for token in market.outcome_tokens] == [
        ("YES", "token-yes"),
        ("NO", "token-no"),
    ]
    assert str(market.minimum_tick_size) == "0.010000"
    assert str(market.minimum_order_size) == "5.000000"


@pytest.mark.parametrize(
    ("updates", "message"),
    [
        ({"outcomes": '["Yes"]'}, "exactly Yes and No"),
        ({"outcomes": '["Up", "Down"]'}, "exactly Yes and No"),
        ({"clobTokenIds": '["same", "same"]'}, "two unique token IDs"),
        ({"clobTokenIds": "not-json"}, "not valid JSON"),
        ({"orderPriceMinTickSize": 0.01}, "binary floating-point"),
    ],
)
def test_rejects_malformed_market_metadata(updates: dict[str, object], message: str) -> None:
    with pytest.raises(InvalidMarketMetadata, match=message):
        normalize_market(market_dto(**updates), OBSERVED_AT, verification())


def test_requires_authoritative_token_verification() -> None:
    with pytest.raises(InvalidMarketMetadata, match="verification is required"):
        normalize_market(market_dto(), OBSERVED_AT, None)


def test_rejects_mismatched_token_verification() -> None:
    with pytest.raises(InvalidMarketMetadata, match="do not match"):
        normalize_market(
            market_dto(),
            OBSERVED_AT,
            verification(primary_token_id="different-token"),
        )


def test_classifies_restricted_before_tradable() -> None:
    market = normalize_market(market_dto(restricted=True), OBSERVED_AT, verification())
    assert market.tradability is Tradability.RESTRICTED


def test_normalizes_event_without_inferring_exclusivity_from_title() -> None:
    event = normalize_event(
        GammaEventDTO.model_validate(
            {
                "id": "event-456",
                "slug": "example-event",
                "title": "Example event",
                "active": True,
                "closed": False,
                "negRisk": False,
            }
        )
    )
    assert event.mutually_exclusive is None
