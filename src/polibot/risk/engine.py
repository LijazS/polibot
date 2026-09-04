from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Protocol
from uuid import UUID

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
    maximum_strategy_exposure: Decimal = Decimal("1000")
    maximum_market_exposure: Decimal = Decimal("1000")
    maximum_event_exposure: Decimal = Decimal("1000")
    maximum_unmatched_exposure: Decimal = Decimal("100")
    maximum_unmatched_duration: timedelta = timedelta(seconds=5)
    maximum_slippage: Decimal = Decimal("100")
    maximum_consecutive_execution_errors: int = 3
    maximum_daily_realized_loss: Decimal = Decimal("100")


@dataclass(frozen=True)
class RiskContext:
    current_global_exposure: Decimal
    strategy_exposure: dict[str, Decimal] = field(default_factory=dict)
    market_exposure: dict[str, Decimal] = field(default_factory=dict)
    event_exposure: dict[str, Decimal] = field(default_factory=dict)
    consumed_proposal_ids: frozenset[UUID] = frozenset()
    consecutive_execution_errors: int = 0
    daily_realized_pnl: Decimal = Decimal("0")
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
        if not proposal.market_tradable:
            reasons.append(RiskRejectionReason.MARKET_NOT_TRADABLE)
        if not proposal.restriction_passed:
            reasons.append(RiskRejectionReason.RESTRICTION_FAILED)
        if not proposal.token_mapping_valid:
            reasons.append(RiskRejectionReason.INVALID_TOKEN_MAPPING)
        if not proposal.quantity_rules_valid:
            reasons.append(RiskRejectionReason.INVALID_QUANTITY)
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
        if proposal.modeled_slippage > self._limits.maximum_slippage:
            reasons.append(RiskRejectionReason.SLIPPAGE_LIMIT)
        if (
            proposal.execution_plan.maximum_unmatched_exposure
            > self._limits.maximum_unmatched_exposure
        ):
            reasons.append(RiskRejectionReason.UNMATCHED_EXPOSURE_LIMIT)
        if (
            proposal.execution_plan.maximum_unmatched_duration
            > self._limits.maximum_unmatched_duration
        ):
            reasons.append(RiskRejectionReason.UNMATCHED_DURATION_LIMIT)
        proposal_cost = proposal.execution_plan.maximum_total_cost
        if context.strategy_exposure.get(proposal.strategy_id, Decimal("0")) + proposal_cost > (
            self._limits.maximum_strategy_exposure
        ):
            reasons.append(RiskRejectionReason.STRATEGY_EXPOSURE_LIMIT)
        if any(
            context.market_exposure.get(market_id, Decimal("0")) + proposal_cost
            > self._limits.maximum_market_exposure
            for market_id in proposal.market_ids
        ):
            reasons.append(RiskRejectionReason.MARKET_EXPOSURE_LIMIT)
        if any(
            context.event_exposure.get(event_id, Decimal("0")) + proposal_cost
            > self._limits.maximum_event_exposure
            for event_id in proposal.event_ids
        ):
            reasons.append(RiskRejectionReason.EVENT_EXPOSURE_LIMIT)
        if (
            context.current_global_exposure + proposal.execution_plan.maximum_total_cost
            > self._limits.maximum_global_exposure
        ):
            reasons.append(RiskRejectionReason.GLOBAL_EXPOSURE_LIMIT)
        if proposal.proposal_id in context.consumed_proposal_ids:
            reasons.append(RiskRejectionReason.DUPLICATE_PROPOSAL)
        if (
            context.consecutive_execution_errors
            >= self._limits.maximum_consecutive_execution_errors
        ):
            reasons.append(RiskRejectionReason.EXECUTION_ERROR_LIMIT)
        if context.daily_realized_pnl < -self._limits.maximum_daily_realized_loss:
            reasons.append(RiskRejectionReason.DAILY_LOSS_LIMIT)
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
