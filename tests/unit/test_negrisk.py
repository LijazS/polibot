from datetime import UTC, datetime, timedelta
from decimal import Decimal

from polibot.domain.models import BookLevel, OrderBook
from polibot.strategies.binary_arb import TakerFeeModel
from polibot.strategies.negrisk import (
    NegRiskConfig,
    NegRiskOutcome,
    NegRiskScanner,
    NegRiskStructure,
)

NOW = datetime(2026, 9, 4, 12, tzinfo=UTC)


def structure(**updates: object) -> NegRiskStructure:
    values: dict[str, object] = {
        "event_id": "event-1",
        "outcomes": tuple(
            NegRiskOutcome(
                outcome_id=name,
                market_id=f"market-{name}",
                yes_token_id=f"yes-{name}",
                no_token_id=f"no-{name}",
            )
            for name in ("a", "b", "other")
        ),
        "structure_verified": True,
        "augmented": False,
        "other_outcome_defined": True,
        "outcome_set_closed": True,
    }
    values.update(updates)
    return NegRiskStructure(**values)  # type: ignore[arg-type]


def books() -> tuple[OrderBook, ...]:
    result: list[OrderBook] = []
    for name in ("a", "b", "other"):
        for prefix, price in (("yes", "0.30"), ("no", "0.80")):
            result.append(
                OrderBook(
                    market_id=f"market-{name}",
                    token_id=f"{prefix}-{name}",
                    bids=(),
                    asks=(BookLevel(price=price, quantity="10"),),
                    source_timestamp=NOW,
                    received_at=NOW,
                )
            )
    return tuple(result)


def scanner() -> NegRiskScanner:
    return NegRiskScanner(
        NegRiskConfig(
            target_payout=Decimal("1"),
            minimum_net_edge=Decimal("0.05"),
            slippage_rate=Decimal("0"),
            execution_risk_buffer=Decimal("0.02"),
            proposal_lifetime=timedelta(seconds=2),
        ),
        TakerFeeModel(Decimal("0"), "dynamic", "observed"),
    )


def test_scanner_proves_every_explicit_terminal_state() -> None:
    proposals = scanner().evaluate(structure(), books(), NOW)
    assert len(proposals) == 1
    proposal = proposals[0]
    assert proposal.all_in_cost == Decimal("0.920000")
    assert proposal.expected_net_edge == Decimal("0.080000")
    assert proposal.payoff_proof is not None
    assert proposal.payoff_proof.terminal_state_payouts == {
        "a": Decimal("1.000000"),
        "b": Decimal("1.000000"),
        "other": Decimal("1.000000"),
    }
    assert {intent.token_id for intent in proposal.execution_plan.intents} == {
        "yes-a",
        "yes-b",
        "yes-other",
    }


def test_ambiguous_or_augmented_structure_is_unsupported() -> None:
    assert scanner().evaluate(structure(augmented=True), books(), NOW) == ()
    assert scanner().evaluate(structure(other_outcome_defined=False), books(), NOW) == ()
    assert scanner().evaluate(structure(outcome_set_closed=False), books(), NOW) == ()


def test_missing_book_is_not_an_executable_opportunity() -> None:
    assert scanner().evaluate(structure(), books()[:-1], NOW) == ()
