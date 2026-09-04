from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from enum import StrEnum
from uuid import UUID, uuid4

from polibot.config import ExecutionMode
from polibot.domain.models import OpportunityProposal, OrderBook, OrderIntent, RiskApproval
from polibot.execution.engine import ExecutionRejected


class SimulationStatus(StrEnum):
    COMPLETE = "complete"
    PARTIALLY_FILLED = "partially_filled"
    FAILED = "failed"


@dataclass(frozen=True)
class SimulatedFill:
    fill_id: UUID
    intent_id: UUID
    token_id: str
    quantity: Decimal
    cost: Decimal
    average_price: Decimal | None


@dataclass(frozen=True)
class SimulationResult:
    proposal_id: UUID
    status: SimulationStatus
    fills: tuple[SimulatedFill, ...]
    unmatched_exposure: Decimal
    unmatched_duration: timedelta
    assumptions: tuple[str, ...]


class PaperExecutionSimulator:
    def __init__(self, mode: ExecutionMode, execution_latency: timedelta = timedelta(0)) -> None:
        if mode not in {ExecutionMode.PAPER, ExecutionMode.SHADOW, ExecutionMode.REPLAY}:
            raise ExecutionRejected("paper simulator cannot run in LIVE mode")
        self._mode = mode
        if execution_latency < timedelta(0):
            raise ValueError("execution latency cannot be negative")
        self._execution_latency = execution_latency
        self._consumed: set[UUID] = set()

    def execute(
        self,
        proposal: OpportunityProposal,
        approval: RiskApproval | None,
        books: tuple[OrderBook, ...],
        now: datetime,
        *,
        failed_intent_ids: frozenset[UUID] = frozenset(),
    ) -> SimulationResult:
        if approval is None or approval.proposal_id != proposal.proposal_id:
            raise ExecutionRejected("matching risk approval is required")
        if proposal.proposal_id in self._consumed:
            raise ExecutionRejected("proposal approval has already been consumed")
        effective_now = now + self._execution_latency
        if effective_now >= approval.valid_until or effective_now >= proposal.expires_at:
            raise ExecutionRejected("approval or proposal has expired")
        self._consumed.add(proposal.proposal_id)
        book_by_token = {book.token_id: book for book in books}
        fills = tuple(
            self._fill(
                intent,
                book_by_token.get(intent.token_id),
                intent.intent_id in failed_intent_ids,
            )
            for intent in proposal.execution_plan.intents
        )
        complete = all(
            fill.quantity == intent.quantity
            for fill, intent in zip(fills, proposal.execution_plan.intents, strict=True)
        )
        any_fill = any(fill.quantity > 0 for fill in fills)
        status = (
            SimulationStatus.COMPLETE
            if complete
            else SimulationStatus.PARTIALLY_FILLED
            if any_fill
            else SimulationStatus.FAILED
        )
        filled_costs = [fill.cost for fill in fills if fill.quantity > 0]
        unmatched = max(filled_costs, default=Decimal("0")) if not complete else Decimal("0")
        return SimulationResult(
            proposal_id=proposal.proposal_id,
            status=status,
            fills=fills,
            unmatched_exposure=unmatched,
            unmatched_duration=self._execution_latency if not complete else timedelta(0),
            assumptions=(
                f"mode={self._mode.value}",
                f"execution_latency={self._execution_latency}",
                "taker consumes recorded asks up to limit price",
                "no queue priority assumed",
                "explicit injected intent failures applied",
            ),
        )

    @staticmethod
    def _fill(intent: OrderIntent, book: OrderBook | None, failed: bool) -> SimulatedFill:
        if failed or book is None or intent.side != "BUY":
            return SimulatedFill(
                uuid4(),
                intent.intent_id,
                intent.token_id,
                Decimal("0"),
                Decimal("0"),
                None,
            )
        remaining = intent.quantity
        quantity = Decimal("0")
        cost = Decimal("0")
        for level in book.asks:
            if level.price > intent.price:
                break
            take = min(remaining, level.quantity)
            quantity += take
            cost += take * level.price
            remaining -= take
            if remaining == 0:
                break
        average = cost / quantity if quantity > 0 else None
        return SimulatedFill(uuid4(), intent.intent_id, intent.token_id, quantity, cost, average)
