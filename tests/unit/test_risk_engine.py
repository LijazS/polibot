from datetime import datetime, timedelta
from decimal import Decimal

from polibot.domain.models import OpportunityProposal, RiskRejectionReason
from polibot.risk import DeterministicRiskEngine, RiskContext, RiskLimits


def engine() -> DeterministicRiskEngine:
    return DeterministicRiskEngine(
        RiskLimits(
            stale_book_after=timedelta(seconds=5),
            minimum_net_edge=Decimal("0.005"),
            maximum_order_notional=Decimal("10"),
            maximum_global_exposure=Decimal("100"),
        )
    )


def test_valid_complete_proposal_can_be_approved(
    valid_proposal: OpportunityProposal, now: datetime
) -> None:
    decision = engine().evaluate(valid_proposal, RiskContext(Decimal("0")), now)
    assert decision.approved
    assert decision.approval is not None
    assert decision.approval.proposal_id == valid_proposal.proposal_id


def test_stale_and_incomplete_proposal_fails_closed(
    valid_proposal: OpportunityProposal, now: datetime
) -> None:
    unsafe = valid_proposal.model_copy(
        update={
            "book_received_at": now - timedelta(seconds=10),
            "fee_model_known": False,
            "payoff_proof": None,
        }
    )
    decision = engine().evaluate(unsafe, RiskContext(Decimal("0")), now)
    assert not decision.approved
    assert set(decision.rejection_reasons) >= {
        RiskRejectionReason.STALE_BOOK,
        RiskRejectionReason.UNKNOWN_FEE_MODEL,
        RiskRejectionReason.MISSING_PAYOFF_PROOF,
    }


def test_unhealthy_reconciliation_rejects(
    valid_proposal: OpportunityProposal, now: datetime
) -> None:
    context = RiskContext(Decimal("0"), reconciliation_healthy=False)
    decision = engine().evaluate(valid_proposal, context, now)
    assert RiskRejectionReason.RECONCILIATION_UNHEALTHY in decision.rejection_reasons


def test_inconsistent_payoff_claim_is_rejected(
    valid_proposal: OpportunityProposal, now: datetime
) -> None:
    unsafe = valid_proposal.model_copy(update={"expected_net_edge": Decimal("0.5")})
    decision = engine().evaluate(unsafe, RiskContext(Decimal("0")), now)
    assert RiskRejectionReason.INCONSISTENT_ECONOMICS in decision.rejection_reasons
