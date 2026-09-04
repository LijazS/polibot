from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Protocol
from uuid import UUID, uuid4

from polibot.config import ExecutionMode
from polibot.domain.models import OpportunityProposal, RiskApproval
from polibot.execution.adapters import (
    ExchangeExecutionAdapter,
    OrderRequest,
    OrderType,
    SubmissionStatus,
)
from polibot.execution.engine import ExecutionRejected


class ExecutionState(StrEnum):
    PLANNED = "planned"
    RISK_APPROVED = "risk_approved"
    SUBMITTING = "submitting"
    PARTIALLY_FILLED = "partially_filled"
    HEDGING = "hedging"
    COMPLETE = "complete"
    CANCEL_REQUESTED = "cancel_requested"
    CANCELLED = "cancelled"
    FAILED = "failed"
    UNKNOWN_EXTERNAL_STATE = "unknown_external_state"
    RECONCILING = "reconciling"
    MANUAL_REVIEW_REQUIRED = "manual_review_required"


@dataclass(frozen=True)
class ExecutionTransition:
    execution_id: UUID
    proposal_id: UUID
    transition_number: int
    state: ExecutionState
    occurred_at: datetime
    detail: str


@dataclass(frozen=True)
class ExecutionPreflight:
    reconciliation_healthy: bool
    books_rebuilt: bool
    kill_switches_clear: bool
    external_state_known: bool

    @property
    def blockers(self) -> tuple[str, ...]:
        pairs = (
            (self.reconciliation_healthy, "reconciliation_unhealthy"),
            (self.books_rebuilt, "books_not_rebuilt"),
            (self.kill_switches_clear, "kill_switch_active"),
            (self.external_state_known, "unknown_external_state"),
        )
        return tuple(reason for healthy, reason in pairs if not healthy)


class ExecutionTransitionStore(Protocol):
    def append(self, transition: ExecutionTransition) -> None: ...

    def for_execution(self, execution_id: UUID) -> tuple[ExecutionTransition, ...]: ...

    def execution_for_proposal(self, proposal_id: UUID) -> UUID | None: ...


class ExecutionTransitionJournal(Protocol):
    async def append(self, transition: ExecutionTransition) -> None: ...

    async def load(self, execution_id: UUID) -> tuple[ExecutionTransition, ...]: ...


class InMemoryExecutionTransitionStore:
    def __init__(self) -> None:
        self._transitions: dict[UUID, list[ExecutionTransition]] = {}
        self._proposal_execution: dict[UUID, UUID] = {}

    def append(self, transition: ExecutionTransition) -> None:
        items = self._transitions.setdefault(transition.execution_id, [])
        if transition.transition_number != len(items):
            raise ValueError("transition number must be contiguous")
        known = self._proposal_execution.setdefault(transition.proposal_id, transition.execution_id)
        if known != transition.execution_id:
            raise ValueError("proposal already mapped to another execution")
        items.append(transition)

    def for_execution(self, execution_id: UUID) -> tuple[ExecutionTransition, ...]:
        return tuple(self._transitions.get(execution_id, ()))

    def execution_for_proposal(self, proposal_id: UUID) -> UUID | None:
        return self._proposal_execution.get(proposal_id)


class GuardedExecutionStateMachine:
    """Non-live execution coordinator using only an injected adapter boundary."""

    def __init__(
        self,
        mode: ExecutionMode,
        adapter: ExchangeExecutionAdapter,
        store: ExecutionTransitionStore,
        journal: ExecutionTransitionJournal | None = None,
    ) -> None:
        if mode is ExecutionMode.LIVE:
            raise ExecutionRejected("LIVE execution is not implemented or permitted")
        self._mode = mode
        self._adapter = adapter
        self._store = store
        self._journal = journal

    async def execute(
        self,
        proposal: OpportunityProposal,
        approval: RiskApproval | None,
        now: datetime,
        *,
        preflight: ExecutionPreflight,
        order_type: OrderType = OrderType.FAK,
    ) -> UUID:
        if approval is None or approval.proposal_id != proposal.proposal_id:
            raise ExecutionRejected("matching risk approval is required")
        if now >= approval.valid_until or now >= proposal.expires_at:
            raise ExecutionRejected("approval or proposal expired")
        if preflight.blockers:
            raise ExecutionRejected(f"execution preflight failed: {','.join(preflight.blockers)}")
        if self._store.execution_for_proposal(proposal.proposal_id) is not None:
            raise ExecutionRejected("proposal approval has already been consumed")
        execution_id = uuid4()
        await self._append(
            execution_id, proposal.proposal_id, ExecutionState.PLANNED, now, "created"
        )
        await self._append(
            execution_id,
            proposal.proposal_id,
            ExecutionState.RISK_APPROVED,
            now,
            str(approval.approval_id),
        )
        filled_legs = 0
        for intent in proposal.execution_plan.intents:
            await self._append(
                execution_id,
                proposal.proposal_id,
                ExecutionState.SUBMITTING,
                now,
                str(intent.intent_id),
            )
            result = await self._adapter.create_order(
                OrderRequest(intent=intent, order_type=order_type)
            )
            if result.status is SubmissionStatus.UNKNOWN:
                await self._append(
                    execution_id,
                    proposal.proposal_id,
                    ExecutionState.UNKNOWN_EXTERNAL_STATE,
                    now,
                    str(intent.intent_id),
                )
                return execution_id
            if result.status is SubmissionStatus.REJECTED:
                state = ExecutionState.HEDGING if filled_legs else ExecutionState.FAILED
                await self._append(
                    execution_id,
                    proposal.proposal_id,
                    state,
                    now,
                    result.reason or "rejected",
                )
                return execution_id
            if result.filled_quantity > 0:
                filled_legs += 1
            if result.filled_quantity < intent.quantity:
                await self._append(
                    execution_id,
                    proposal.proposal_id,
                    ExecutionState.PARTIALLY_FILLED,
                    now,
                    str(intent.intent_id),
                )
                return execution_id
        await self._append(
            execution_id, proposal.proposal_id, ExecutionState.COMPLETE, now, "all legs"
        )
        return execution_id

    async def begin_reconciliation(self, execution_id: UUID, now: datetime) -> None:
        transitions = self._store.for_execution(execution_id)
        if not transitions or transitions[-1].state is not ExecutionState.UNKNOWN_EXTERNAL_STATE:
            raise ExecutionRejected("only unknown external state can enter reconciliation")
        await self._append(
            execution_id,
            transitions[-1].proposal_id,
            ExecutionState.RECONCILING,
            now,
            "external lookup required",
        )

    async def require_manual_review(self, execution_id: UUID, now: datetime, detail: str) -> None:
        transitions = self._store.for_execution(execution_id)
        if not transitions or transitions[-1].state is not ExecutionState.RECONCILING:
            raise ExecutionRejected("manual review follows reconciliation")
        await self._append(
            execution_id,
            transitions[-1].proposal_id,
            ExecutionState.MANUAL_REVIEW_REQUIRED,
            now,
            detail,
        )

    async def _append(
        self,
        execution_id: UUID,
        proposal_id: UUID,
        state: ExecutionState,
        now: datetime,
        detail: str,
    ) -> None:
        number = len(self._store.for_execution(execution_id))
        transition = ExecutionTransition(execution_id, proposal_id, number, state, now, detail)
        if self._journal is not None:
            await self._journal.append(transition)
        self._store.append(transition)
