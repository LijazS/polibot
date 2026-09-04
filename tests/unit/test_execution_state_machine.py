from datetime import datetime
from decimal import Decimal

import pytest

from polibot.config import ExecutionMode
from polibot.execution.adapters import FakeExchangeAdapter, SubmissionStatus
from polibot.execution.engine import ExecutionRejected
from polibot.execution.state_machine import (
    ExecutionPreflight,
    ExecutionState,
    ExecutionTransition,
    GuardedExecutionStateMachine,
    InMemoryExecutionTransitionStore,
)

READY = ExecutionPreflight(True, True, True, True)


class FailingJournal:
    async def append(self, transition: ExecutionTransition) -> None:
        del transition
        raise RuntimeError("database unavailable")

    async def load(self, execution_id):
        del execution_id
        return ()


@pytest.mark.asyncio
async def test_complete_state_machine_consumes_approval_once(valid_proposal, now: datetime) -> None:
    store = InMemoryExecutionTransitionStore()
    machine = GuardedExecutionStateMachine(ExecutionMode.SHADOW, FakeExchangeAdapter(), store)
    approval = valid_proposal.model_copy().proposal_id
    from polibot.domain.models import RiskApproval

    risk_approval = RiskApproval(
        proposal_id=approval,
        approved_at=now,
        valid_until=valid_proposal.expires_at,
    )
    execution_id = await machine.execute(valid_proposal, risk_approval, now, preflight=READY)
    assert store.for_execution(execution_id)[-1].state is ExecutionState.COMPLETE
    with pytest.raises(ExecutionRejected, match="already been consumed"):
        await machine.execute(valid_proposal, risk_approval, now, preflight=READY)


@pytest.mark.asyncio
async def test_unknown_submission_must_reconcile(valid_proposal, now: datetime) -> None:
    first = valid_proposal.execution_plan.intents[0].intent_id
    store = InMemoryExecutionTransitionStore()
    adapter = FakeExchangeAdapter({first: SubmissionStatus.UNKNOWN})
    machine = GuardedExecutionStateMachine(ExecutionMode.PAPER, adapter, store)
    from polibot.domain.models import RiskApproval

    approval = RiskApproval(
        proposal_id=valid_proposal.proposal_id,
        approved_at=now,
        valid_until=valid_proposal.expires_at,
    )
    execution_id = await machine.execute(valid_proposal, approval, now, preflight=READY)
    assert store.for_execution(execution_id)[-1].state is ExecutionState.UNKNOWN_EXTERNAL_STATE
    await machine.begin_reconciliation(execution_id, now)
    await machine.require_manual_review(execution_id, now, "lookup inconclusive")
    assert store.for_execution(execution_id)[-1].state is ExecutionState.MANUAL_REVIEW_REQUIRED


@pytest.mark.asyncio
async def test_second_leg_failure_enters_hedging(valid_proposal, now: datetime) -> None:
    second = valid_proposal.execution_plan.intents[1].intent_id
    store = InMemoryExecutionTransitionStore()
    machine = GuardedExecutionStateMachine(
        ExecutionMode.PAPER,
        FakeExchangeAdapter({second: SubmissionStatus.REJECTED}),
        store,
    )
    from polibot.domain.models import RiskApproval

    approval = RiskApproval(
        proposal_id=valid_proposal.proposal_id,
        approved_at=now,
        valid_until=valid_proposal.expires_at,
    )
    execution_id = await machine.execute(valid_proposal, approval, now, preflight=READY)
    assert store.for_execution(execution_id)[-1].state is ExecutionState.HEDGING


def test_live_state_machine_is_hard_disabled() -> None:
    with pytest.raises(ExecutionRejected, match="not implemented"):
        GuardedExecutionStateMachine(
            ExecutionMode.LIVE,
            FakeExchangeAdapter(),
            InMemoryExecutionTransitionStore(),
        )


@pytest.mark.asyncio
async def test_database_failure_fails_before_submission(valid_proposal, now: datetime) -> None:
    store = InMemoryExecutionTransitionStore()
    machine = GuardedExecutionStateMachine(
        ExecutionMode.PAPER, FakeExchangeAdapter(), store, FailingJournal()
    )
    from polibot.domain.models import RiskApproval

    approval = RiskApproval(
        proposal_id=valid_proposal.proposal_id,
        approved_at=now,
        valid_until=valid_proposal.expires_at,
    )
    with pytest.raises(RuntimeError, match="database unavailable"):
        await machine.execute(valid_proposal, approval, now, preflight=READY)
    assert store.execution_for_proposal(valid_proposal.proposal_id) is None


@pytest.mark.asyncio
async def test_preflight_failure_prevents_execution(valid_proposal, now: datetime) -> None:
    machine = GuardedExecutionStateMachine(
        ExecutionMode.PAPER, FakeExchangeAdapter(), InMemoryExecutionTransitionStore()
    )
    from polibot.domain.models import RiskApproval

    approval = RiskApproval(
        proposal_id=valid_proposal.proposal_id,
        approved_at=now,
        valid_until=valid_proposal.expires_at,
    )
    unsafe = ExecutionPreflight(False, False, False, False)
    with pytest.raises(ExecutionRejected, match="preflight failed"):
        await machine.execute(valid_proposal, approval, now, preflight=unsafe)


@pytest.mark.asyncio
async def test_partial_fill_stops_before_next_leg(valid_proposal, now: datetime) -> None:
    first = valid_proposal.execution_plan.intents[0]
    store = InMemoryExecutionTransitionStore()
    machine = GuardedExecutionStateMachine(
        ExecutionMode.PAPER,
        FakeExchangeAdapter(fill_quantities={first.intent_id: Decimal("0.5")}),
        store,
    )
    from polibot.domain.models import RiskApproval

    approval = RiskApproval(
        proposal_id=valid_proposal.proposal_id,
        approved_at=now,
        valid_until=valid_proposal.expires_at,
    )
    execution_id = await machine.execute(valid_proposal, approval, now, preflight=READY)
    assert store.for_execution(execution_id)[-1].state is ExecutionState.PARTIALLY_FILLED
