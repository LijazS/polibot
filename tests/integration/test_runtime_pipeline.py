from collections.abc import Sequence
from datetime import datetime, timedelta
from decimal import Decimal

import pytest

from polibot.config import ExecutionMode
from polibot.domain.models import MarketSnapshot, OpportunityProposal
from polibot.execution import SimulatedExecutionEngine
from polibot.monitoring import PolibotMetrics
from polibot.risk import DeterministicRiskEngine, RiskContext, RiskLimits
from polibot.runtime import PaperShadowRuntime
from polibot.storage import InMemoryRecorder, RecordKind


class StaticStrategy:
    strategy_id = "binary_complete_set"

    def __init__(self, proposal: OpportunityProposal) -> None:
        self._proposal = proposal

    def evaluate(self, snapshot: MarketSnapshot) -> Sequence[OpportunityProposal]:
        del snapshot
        return (self._proposal,)


@pytest.mark.asyncio
async def test_snapshot_flows_only_through_strategy_risk_and_simulated_execution(
    valid_proposal: OpportunityProposal, now: datetime
) -> None:
    recorder = InMemoryRecorder()
    runtime = PaperShadowRuntime(
        mode=ExecutionMode.SHADOW,
        strategies=(StaticStrategy(valid_proposal),),
        risk_engine=DeterministicRiskEngine(
            RiskLimits(
                stale_book_after=timedelta(seconds=5),
                minimum_net_edge=Decimal("0.005"),
                maximum_order_notional=Decimal("10"),
                maximum_global_exposure=Decimal("100"),
            )
        ),
        executor=SimulatedExecutionEngine(ExecutionMode.SHADOW),
        recorder=recorder,
        metrics=PolibotMetrics(),
    )
    snapshot = MarketSnapshot(
        market={
            "market_id": "market-1",
            "event_id": "event-1",
            "active": True,
            "accepting_orders": True,
            "metadata_observed_at": now,
        },
        books=(),
        captured_at=now,
    )
    cycle = await runtime.process_snapshot(snapshot, RiskContext(Decimal("0")), now)
    assert cycle.proposals == 1
    assert cycle.decisions[0].approved
    assert len(cycle.simulated_receipts) == 1
    records = await recorder.read_all()
    assert [record.kind for record in records] == [
        RecordKind.PROPOSAL,
        RecordKind.RISK_DECISION,
        RecordKind.SIMULATED_EXECUTION,
    ]
