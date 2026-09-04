from datetime import UTC, datetime, timedelta
from decimal import Decimal

from polibot.domain.models import (
    BookLevel,
    Market,
    MarketSnapshot,
    OrderBook,
    OutcomeToken,
    Tradability,
)
from polibot.strategies.binary_arb import (
    BinaryArbConfig,
    BinaryCompleteSetScanner,
    TakerFeeModel,
    walk_asks,
)

NOW = datetime(2026, 9, 4, 12, tzinfo=UTC)


def book(token_id: str, asks: list[tuple[str, str]]) -> OrderBook:
    return OrderBook(
        market_id="market-1",
        token_id=token_id,
        bids=(),
        asks=tuple(BookLevel(price=price, quantity=size) for price, size in asks),
        source_timestamp=NOW,
        received_at=NOW,
    )


def snapshot() -> MarketSnapshot:
    market = Market(
        market_id="market-1",
        event_id="event-1",
        condition_id="condition-1",
        outcome_tokens=(
            OutcomeToken(
                token_id="yes", market_id="market-1", condition_id="condition-1", outcome="YES"
            ),
            OutcomeToken(
                token_id="no", market_id="market-1", condition_id="condition-1", outcome="NO"
            ),
        ),
        active=True,
        accepting_orders=True,
        enable_order_book=True,
        tradability=Tradability.TRADABLE,
        minimum_tick_size=Decimal("0.01"),
        minimum_order_size=Decimal("5"),
        metadata_observed_at=NOW,
    )
    return MarketSnapshot(
        market=market,
        books=(
            book("yes", [("0.48", "5"), ("0.50", "5")]),
            book("no", [("0.49", "10")]),
        ),
        captured_at=NOW,
    )


def config() -> BinaryArbConfig:
    return BinaryArbConfig(
        maximum_quantity=Decimal("10"),
        minimum_net_edge=Decimal("0.10"),
        slippage_rate=Decimal("0"),
        execution_risk_buffer=Decimal("0.05"),
        proposal_lifetime=timedelta(seconds=2),
    )


def test_walks_multiple_ask_levels_for_executable_cost() -> None:
    result = walk_asks(book("yes", [("0.48", "5"), ("0.50", "5")]), Decimal("8"))
    assert result is not None
    assert result.cost == Decimal("3.90")
    assert result.maximum_price == Decimal("0.50")
    assert result.levels_consumed == 2


def test_scanner_emits_auditable_depth_aware_proposals() -> None:
    scanner = BinaryCompleteSetScanner(
        config(), TakerFeeModel(Decimal("0"), "official-market-info", "observed-1")
    )
    proposals = scanner.evaluate(snapshot())
    largest = max(proposals, key=lambda proposal: proposal.execution_plan.intents[0].quantity)
    assert largest.execution_plan.intents[0].quantity == Decimal("10.000000")
    assert largest.all_in_cost == Decimal("9.850000")
    assert largest.expected_net_edge == Decimal("0.150000")
    assert largest.payoff_proof is not None
    assert largest.payoff_proof.worst_case_payout == Decimal("10.000000")
    assert largest.evidence["yes_levels_consumed"] == "2"


def test_scanner_emits_nothing_without_fee_model() -> None:
    assert BinaryCompleteSetScanner(config(), None).evaluate(snapshot()) == ()


def test_scanner_emits_nothing_without_both_books() -> None:
    incomplete = snapshot().model_copy(update={"books": (book("yes", [("0.48", "10")]),)})
    scanner = BinaryCompleteSetScanner(config(), TakerFeeModel(Decimal("0"), "source", "version"))
    assert scanner.evaluate(incomplete) == ()


def test_fee_model_uses_documented_dynamic_formula_and_conservative_rounding() -> None:
    model = TakerFeeModel(Decimal("0.04"), "dynamic", "observed")
    assert model.fee(Decimal("10"), Decimal("0.5")) == Decimal("0.100000")
