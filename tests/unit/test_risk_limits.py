from datetime import datetime, timedelta
from decimal import Decimal

from polibot.domain.models import OpportunityProposal, RiskRejectionReason
from polibot.risk import DeterministicRiskEngine, RiskContext, RiskLimits


def test_scoped_exposure_duplicate_error_and_loss_guards(
    valid_proposal: OpportunityProposal, now: datetime
) -> None:
    limits = RiskLimits(
        stale_book_after=timedelta(seconds=5),
        minimum_net_edge=Decimal("0.005"),
        maximum_order_notional=Decimal("10"),
        maximum_global_exposure=Decimal("100"),
        maximum_strategy_exposure=Decimal("0.9"),
        maximum_unmatched_exposure=Decimal("0.1"),
        maximum_unmatched_duration=timedelta(seconds=1),
        maximum_consecutive_execution_errors=1,
        maximum_daily_realized_loss=Decimal("1"),
    )
    context = RiskContext(
        current_global_exposure=Decimal("0"),
        consumed_proposal_ids=frozenset({valid_proposal.proposal_id}),
        consecutive_execution_errors=1,
        daily_realized_pnl=Decimal("-2"),
    )
    decision = DeterministicRiskEngine(limits).evaluate(valid_proposal, context, now)
    assert set(decision.rejection_reasons) >= {
        RiskRejectionReason.STRATEGY_EXPOSURE_LIMIT,
        RiskRejectionReason.UNMATCHED_EXPOSURE_LIMIT,
        RiskRejectionReason.UNMATCHED_DURATION_LIMIT,
        RiskRejectionReason.DUPLICATE_PROPOSAL,
        RiskRejectionReason.EXECUTION_ERROR_LIMIT,
        RiskRejectionReason.DAILY_LOSS_LIMIT,
    }
