from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from polibot.domain.models import ExecutionPlan, OpportunityProposal, OrderIntent, PayoffProof


@pytest.fixture
def now() -> datetime:
    return datetime(2026, 9, 4, 12, 0, tzinfo=UTC)


@pytest.fixture
def valid_proposal(now: datetime) -> OpportunityProposal:
    return OpportunityProposal(
        strategy_id="binary_complete_set",
        market_ids=("market-1",),
        observed_at=now,
        book_received_at=now,
        expires_at=now + timedelta(seconds=2),
        market_active=True,
        fee_model_known=True,
        metadata_validated=True,
        executable_depth_verified=True,
        all_in_cost=Decimal("0.97"),
        expected_net_edge=Decimal("0.02"),
        payoff_proof=PayoffProof(
            terminal_state_payouts={"yes": Decimal("1"), "no": Decimal("1")},
            worst_case_payout=Decimal("1"),
        ),
        execution_plan=ExecutionPlan(
            intents=(
                OrderIntent(
                    market_id="market-1",
                    token_id="yes-token",
                    side="BUY",
                    price=Decimal("0.48"),
                    quantity=Decimal("1"),
                ),
                OrderIntent(
                    market_id="market-1",
                    token_id="no-token",
                    side="BUY",
                    price=Decimal("0.49"),
                    quantity=Decimal("1"),
                ),
            ),
            maximum_total_cost=Decimal("0.98"),
            maximum_unmatched_exposure=Decimal("0.49"),
        ),
    )
