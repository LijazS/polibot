from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from polibot.domain.values import Money, Price, Quantity, SignedMoney


class FrozenModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class Market(FrozenModel):
    market_id: str
    event_id: str
    active: bool
    accepting_orders: bool
    metadata_observed_at: datetime


class Event(FrozenModel):
    event_id: str
    title: str
    mutually_exclusive: bool | None = None


class OutcomeToken(FrozenModel):
    token_id: str
    market_id: str
    outcome: str


class BookLevel(FrozenModel):
    price: Price
    quantity: Quantity


class OrderBook(FrozenModel):
    market_id: str
    token_id: str
    bids: tuple[BookLevel, ...]
    asks: tuple[BookLevel, ...]
    source_timestamp: datetime
    received_at: datetime
    sequence: int | None = None


class MarketSnapshot(FrozenModel):
    market: Market
    books: tuple[OrderBook, ...]
    captured_at: datetime


class FeeModel(FrozenModel):
    source: str
    observed_at: datetime
    version: str | None = None


class RewardProgram(FrozenModel):
    program_id: str
    eligible: bool
    source: str
    observed_at: datetime
    parameters: dict[str, str] = Field(default_factory=dict)


class PayoffProof(FrozenModel):
    terminal_state_payouts: dict[str, Money]
    worst_case_payout: Money

    @model_validator(mode="after")
    def verify_worst_case(self) -> PayoffProof:
        if not self.terminal_state_payouts:
            raise ValueError("at least one terminal state is required")
        if min(self.terminal_state_payouts.values()) != self.worst_case_payout:
            raise ValueError("worst_case_payout must equal the minimum state payout")
        return self


class OrderIntent(FrozenModel):
    market_id: str
    token_id: str
    side: str
    price: Price
    quantity: Quantity

    @field_validator("side")
    @classmethod
    def supported_side(cls, value: str) -> str:
        normalized = value.upper()
        if normalized not in {"BUY", "SELL"}:
            raise ValueError("side must be BUY or SELL")
        return normalized


class ExecutionPlan(FrozenModel):
    intents: tuple[OrderIntent, ...]
    maximum_total_cost: Money
    maximum_unmatched_exposure: Money


class OpportunityProposal(FrozenModel):
    proposal_id: UUID = Field(default_factory=uuid4)
    strategy_id: str
    market_ids: tuple[str, ...]
    observed_at: datetime
    book_received_at: datetime
    expires_at: datetime
    market_active: bool
    fee_model_known: bool
    metadata_validated: bool
    executable_depth_verified: bool
    all_in_cost: Money
    expected_net_edge: Money
    payoff_proof: PayoffProof | None
    execution_plan: ExecutionPlan

    @field_validator("observed_at", "book_received_at", "expires_at")
    @classmethod
    def require_aware_datetime(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("timestamps must be timezone-aware")
        return value.astimezone(UTC)


class RiskRejectionReason(StrEnum):
    MARKET_INACTIVE = "market_inactive"
    STALE_BOOK = "stale_book"
    EXPIRED_PROPOSAL = "expired_proposal"
    UNKNOWN_FEE_MODEL = "unknown_fee_model"
    INVALID_METADATA = "invalid_metadata"
    DEPTH_NOT_VERIFIED = "depth_not_verified"
    MISSING_PAYOFF_PROOF = "missing_payoff_proof"
    INCONSISTENT_ECONOMICS = "inconsistent_economics"
    INSUFFICIENT_NET_EDGE = "insufficient_net_edge"
    ORDER_NOTIONAL_LIMIT = "order_notional_limit"
    GLOBAL_EXPOSURE_LIMIT = "global_exposure_limit"
    RECONCILIATION_UNHEALTHY = "reconciliation_unhealthy"
    SYSTEM_UNHEALTHY = "system_unhealthy"


class RiskApproval(FrozenModel):
    approval_id: UUID = Field(default_factory=uuid4)
    proposal_id: UUID
    approved_at: datetime
    valid_until: datetime


class RiskDecision(FrozenModel):
    proposal_id: UUID
    evaluated_at: datetime
    approval: RiskApproval | None = None
    rejection_reasons: tuple[RiskRejectionReason, ...] = ()

    @property
    def approved(self) -> bool:
        return self.approval is not None and not self.rejection_reasons

    @model_validator(mode="after")
    def enforce_single_outcome(self) -> RiskDecision:
        if (self.approval is None) == (not self.rejection_reasons):
            raise ValueError("risk decision must contain either approval or rejection reasons")
        return self


class Order(FrozenModel):
    order_id: str
    proposal_id: UUID
    status: str


class Fill(FrozenModel):
    fill_id: str
    order_id: str
    price: Price
    quantity: Quantity


class Position(FrozenModel):
    token_id: str
    quantity: Quantity
    cost_basis: Money


class BalanceSnapshot(FrozenModel):
    asset: str
    available: Money
    observed_at: datetime


class ReconciliationResult(FrozenModel):
    reconciled_at: datetime
    healthy: bool
    details: tuple[str, ...] = ()


class PnLComponentType(StrEnum):
    STRUCTURAL_ARBITRAGE = "structural_arbitrage"
    SPREAD_CAPTURE = "spread_capture"
    INVENTORY = "inventory"
    FEES = "fees"
    SLIPPAGE = "slippage"
    MAKER_REBATE = "maker_rebate"
    LIQUIDITY_REWARD = "liquidity_reward"
    HOLDING_REWARD = "holding_reward"
    OPERATIONAL_ADJUSTMENT = "operational_adjustment"


class PnLComponent(FrozenModel):
    component_type: PnLComponentType
    amount: SignedMoney
    recorded_at: datetime


class StrategyRun(FrozenModel):
    run_id: UUID = Field(default_factory=uuid4)
    strategy_id: str
    started_at: datetime
    proposal_ids: tuple[UUID, ...] = ()


class AuditEvent(FrozenModel):
    event_id: UUID = Field(default_factory=uuid4)
    occurred_at: datetime
    severity: str
    event_type: str
    details: dict[str, str] = Field(default_factory=dict)
