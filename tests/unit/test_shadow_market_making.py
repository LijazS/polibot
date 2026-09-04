from datetime import timedelta
from decimal import Decimal

from polibot.domain.models import BookLevel, OrderBook
from polibot.strategies.market_making import ShadowMarketMaker, ShadowMarketMakingConfig


def _book(now) -> OrderBook:
    return OrderBook(
        market_id="m",
        token_id="yes",
        bids=(BookLevel(price="0.48", quantity="30"),),
        asks=(BookLevel(price="0.52", quantity="10"),),
        source_timestamp=now,
        received_at=now,
    )


def _maker() -> ShadowMarketMaker:
    return ShadowMarketMaker(
        ShadowMarketMakingConfig(
            half_spread=Decimal("0.02"),
            quote_quantity=Decimal("5"),
            maximum_inventory=Decimal("20"),
            inventory_skew_per_unit=Decimal("0.001"),
            maximum_volatility=Decimal("0.05"),
            minimum_time_to_resolution=timedelta(hours=1),
        )
    )


def test_shadow_quotes_use_microprice_and_are_post_only(now) -> None:
    observation = _maker().observe(
        _book(now),
        inventory=Decimal("0"),
        volatility=Decimal("0.01"),
        resolution_at=now + timedelta(days=1),
        now=now,
    )
    assert observation.midpoint == Decimal("0.500000")
    assert observation.microprice == Decimal("0.510000")
    assert len(observation.quotes) == 2
    assert all(quote.post_only for quote in observation.quotes)
    assert observation.quotes[0].price < observation.quotes[1].price


def test_shadow_market_maker_shuts_down_on_risk(now) -> None:
    observation = _maker().observe(
        _book(now),
        inventory=Decimal("20"),
        volatility=Decimal("0.10"),
        resolution_at=now + timedelta(minutes=5),
        now=now,
        event_risk=True,
    )
    assert observation.quotes == ()
    assert set(observation.shutdown_reasons) == {
        "inventory_limit",
        "volatility_limit",
        "resolution_too_close",
        "event_risk",
    }
