from datetime import UTC, datetime
from decimal import Decimal

from polibot.accounting import AccountingLedger
from polibot.domain.models import PnLComponent, PnLComponentType
from polibot.strategies.holding_rewards import HoldingRewardPilot

NOW = datetime(2026, 9, 4, tzinfo=UTC)


def test_reward_pilot_requires_current_sourced_parameters() -> None:
    pilot = HoldingRewardPilot()
    assert (
        pilot.observe(
            market_id="m1",
            position_quantity=Decimal("10"),
            observed_at=NOW,
            eligible=None,
            parameters=None,
            provenance=None,
        )
        is None
    )


def test_reward_observation_reconciles_expected_and_actual_separately() -> None:
    observation = HoldingRewardPilot().observe(
        market_id="m1",
        position_quantity=Decimal("10"),
        observed_at=NOW,
        eligible=True,
        parameters={"rate_source_value": "dynamic"},
        provenance="official-observation-2026-09-04",
        expected_reward=Decimal("0.10"),
        actual_reward=Decimal("0.08"),
    )
    assert observation is not None
    assert observation.difference == Decimal("-0.020000")


def test_accounting_never_hides_components_inside_total() -> None:
    ledger = AccountingLedger()
    ledger.record(
        PnLComponent(
            component_type=PnLComponentType.STRUCTURAL_ARBITRAGE,
            amount=Decimal("1"),
            recorded_at=NOW,
        )
    )
    ledger.record(
        PnLComponent(
            component_type=PnLComponentType.FEES,
            amount=Decimal("-0.2"),
            recorded_at=NOW,
        )
    )
    summary = ledger.summary()
    assert summary.by_component[PnLComponentType.STRUCTURAL_ARBITRAGE] == Decimal("1")
    assert summary.by_component[PnLComponentType.FEES] == Decimal("-0.2")
    assert summary.net == Decimal("0.8")
