from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Protocol

from polibot.domain.models import (
    OpportunityProposal,
    RiskApproval,
    RiskDecision,
    RiskRejectionReason,
)


@dataclass(frozen=True)
class RiskLimits:
    stale_book_after: timedelta
    minimum_net_edge: Decimal
    maximum_order_notional: Decimal
    maximum_global_exposure: Decimal


@dataclass(frozen=True)
class RiskContext:
    current_global_exposure: Decimal
    reconciliation_healthy: bool = True
    system_healthy: bool = True


class RiskEngine(Protocol):
    def evaluate(
        self, proposal: OpportunityProposal, context: RiskContext, now: datetime
    ) -> RiskDecision: ...


class DeterministicRiskEngine:
    def __init__(self, limits: RiskLimits) -> None:
        self._limits = limits

    def evaluate(
        self, proposal: OpportunityProposal, context: RiskContext, now: datetime
    ) -> RiskDecision:
        reasons: list[RiskRejectionReason] = []
        if not proposal.market_active:
            reasons.append(RiskRejectionReason.MARKET_INACTIVE)
        if now - proposal.book_received_at > self._limits.stale_book_after:
            reasons.append(RiskRejectionReason.STALE_BOOK)
        if now >= proposal.expires_at:
            reasons.append(RiskRejectionReason.EXPIRED_PROPOSAL)
        if not proposal.fee_model_known:
            reasons.append(RiskRejectionReason.UNKNOWN_FEE_MODEL)
        if not proposal.metadata_validated:
            reasons.append(RiskRejectionReason.INVALID_METADATA)
        if not proposal.executable_depth_verified:
            reasons.append(RiskRejectionReason.DEPTH_NOT_VERIFIED)
        if proposal.payoff_proof is None:
            reasons.append(RiskRejectionReason.MISSING_PAYOFF_PROOF)
        elif (
            proposal.payoff_proof.worst_case_payout - proposal.all_in_cost
            < proposal.expected_net_edge
        ):
            reasons.append(RiskRejectionReason.INCONSISTENT_ECONOMICS)
        if proposal.execution_plan.maximum_total_cost < proposal.all_in_cost:
            reasons.append(RiskRejectionReason.INCONSISTENT_ECONOMICS)
        if proposal.expected_net_edge < self._limits.minimum_net_edge:
            reasons.append(RiskRejectionReason.INSUFFICIENT_NET_EDGE)
        if proposal.execution_plan.maximum_total_cost > self._limits.maximum_order_notional:
            reasons.append(RiskRejectionReason.ORDER_NOTIONAL_LIMIT)
        if (
            context.current_global_exposure + proposal.execution_plan.maximum_total_cost
            > self._limits.maximum_global_exposure
        ):
            reasons.append(RiskRejectionReason.GLOBAL_EXPOSURE_LIMIT)
        if not context.reconciliation_healthy:
            reasons.append(RiskRejectionReason.RECONCILIATION_UNHEALTHY)
        if not context.system_healthy:
            reasons.append(RiskRejectionReason.SYSTEM_UNHEALTHY)

        if reasons:
            return RiskDecision(
                proposal_id=proposal.proposal_id,
                evaluated_at=now,
                rejection_reasons=tuple(dict.fromkeys(reasons)),
            )
        return RiskDecision(
            proposal_id=proposal.proposal_id,
            evaluated_at=now,
            approval=RiskApproval(
                proposal_id=proposal.proposal_id,
                approved_at=now,
                valid_until=proposal.expires_at,
            ),
        )
