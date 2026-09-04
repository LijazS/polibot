from datetime import datetime, timedelta
from decimal import Decimal

import pytest

from polibot.config import ExecutionMode
from polibot.domain.models import BookLevel, OpportunityProposal, OrderBook, RiskApproval
from polibot.execution import ExecutionRejected
from polibot.execution.paper import PaperExecutionSimulator, SimulationStatus


def books(now: datetime) -> tuple[OrderBook, ...]:
    return (
        OrderBook(
            market_id="market-1",
            token_id="yes-token",
            bids=(),
            asks=(BookLevel(price="0.48", quantity="1"),),
            source_timestamp=now,
            received_at=now,
        ),
        OrderBook(
            market_id="market-1",
            token_id="no-token",
            bids=(),
            asks=(BookLevel(price="0.49", quantity="1"),),
            source_timestamp=now,
            received_at=now,
        ),
    )


def approval(proposal: OpportunityProposal, now: datetime) -> RiskApproval:
    return RiskApproval(
        proposal_id=proposal.proposal_id,
        approved_at=now,
        valid_until=proposal.expires_at,
    )


def test_paper_simulation_consumes_actual_depth(
    valid_proposal: OpportunityProposal, now: datetime
) -> None:
    result = PaperExecutionSimulator(ExecutionMode.PAPER).execute(
        valid_proposal, approval(valid_proposal, now), books(now), now
    )
    assert result.status is SimulationStatus.COMPLETE
    assert result.unmatched_exposure == 0
    assert [fill.cost for fill in result.fills] == [Decimal("0.48"), Decimal("0.49")]


def test_second_leg_failure_records_unmatched_exposure(
    valid_proposal: OpportunityProposal, now: datetime
) -> None:
    second = valid_proposal.execution_plan.intents[1]
    result = PaperExecutionSimulator(ExecutionMode.SHADOW).execute(
        valid_proposal,
        approval(valid_proposal, now),
        books(now),
        now,
        failed_intent_ids=frozenset({second.intent_id}),
    )
    assert result.status is SimulationStatus.PARTIALLY_FILLED
    assert result.unmatched_exposure == Decimal("0.48")


def test_simulator_consumes_approval_once(
    valid_proposal: OpportunityProposal, now: datetime
) -> None:
    simulator = PaperExecutionSimulator(ExecutionMode.PAPER)
    risk_approval = approval(valid_proposal, now)
    simulator.execute(valid_proposal, risk_approval, books(now), now)
    with pytest.raises(ExecutionRejected, match="already been consumed"):
        simulator.execute(valid_proposal, risk_approval, books(now), now)


def test_simulator_hard_rejects_live() -> None:
    with pytest.raises(ExecutionRejected, match="LIVE"):
        PaperExecutionSimulator(ExecutionMode.LIVE)


def test_execution_latency_can_expire_opportunity(
    valid_proposal: OpportunityProposal, now: datetime
) -> None:
    simulator = PaperExecutionSimulator(ExecutionMode.PAPER, timedelta(seconds=3))
    with pytest.raises(ExecutionRejected, match="expired"):
        simulator.execute(valid_proposal, approval(valid_proposal, now), books(now), now)
