from datetime import UTC, datetime, timedelta
from decimal import Decimal

from hypothesis import assume, given
from hypothesis import strategies as st

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
)

NOW = datetime(2026, 9, 4, tzinfo=UTC)


@given(
    yes_cents=st.integers(min_value=1, max_value=90),
    no_cents=st.integers(min_value=1, max_value=90),
    quantity=st.integers(min_value=1, max_value=100),
)
def test_emitted_binary_proposal_has_required_worst_case_margin(
    yes_cents: int, no_cents: int, quantity: int
) -> None:
    assume(yes_cents + no_cents <= 95)
    yes_price = Decimal(yes_cents) / Decimal("100")
    no_price = Decimal(no_cents) / Decimal("100")
    size = Decimal(quantity)
    market = Market(
        market_id="m",
        event_id="e",
        outcome_tokens=(
            OutcomeToken(token_id="yes", market_id="m", outcome="YES"),
            OutcomeToken(token_id="no", market_id="m", outcome="NO"),
        ),
        active=True,
        accepting_orders=True,
        enable_order_book=True,
        tradability=Tradability.TRADABLE,
        minimum_order_size=Decimal("1"),
        metadata_observed_at=NOW,
    )
    books = tuple(
        OrderBook(
            market_id="m",
            token_id=token,
            bids=(),
            asks=(BookLevel(price=price, quantity=size),),
            source_timestamp=NOW,
            received_at=NOW,
        )
        for token, price in (("yes", yes_price), ("no", no_price))
    )
    scanner = BinaryCompleteSetScanner(
        BinaryArbConfig(
            maximum_quantity=size,
            minimum_net_edge=Decimal("0.01"),
            slippage_rate=Decimal("0"),
            execution_risk_buffer=Decimal("0.01"),
            proposal_lifetime=timedelta(seconds=1),
        ),
        TakerFeeModel(Decimal("0"), "property", "test"),
    )
    proposals = scanner.evaluate(MarketSnapshot(market=market, books=books, captured_at=NOW))
    for proposal in proposals:
        assert proposal.payoff_proof is not None
        assert proposal.payoff_proof.worst_case_payout >= (proposal.all_in_cost + Decimal("0.01"))
