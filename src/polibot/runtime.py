from __future__ import annotations

from collections.abc import AsyncIterator, Callable, Sequence
from dataclasses import dataclass
from datetime import datetime

from polibot.config import ExecutionMode
from polibot.domain.models import MarketSnapshot, RiskDecision
from polibot.execution import ExecutionRejected, SimulatedExecutionEngine
from polibot.monitoring import PolibotMetrics
from polibot.risk import DeterministicRiskEngine, RiskContext
from polibot.storage import RecordedEnvelope, Recorder, RecordKind, canonical_payload
from polibot.strategies import Strategy


@dataclass(frozen=True)
class RuntimeCycle:
    proposals: int
    decisions: tuple[RiskDecision, ...]
    simulated_receipts: tuple[str, ...]


class PaperShadowRuntime:
    def __init__(
        self,
        *,
        mode: ExecutionMode,
        strategies: Sequence[Strategy],
        risk_engine: DeterministicRiskEngine,
        executor: SimulatedExecutionEngine,
        recorder: Recorder,
        metrics: PolibotMetrics,
    ) -> None:
        if mode not in {ExecutionMode.PAPER, ExecutionMode.SHADOW, ExecutionMode.REPLAY}:
            raise ExecutionRejected("runtime hard-disables LIVE mode")
        self._mode = mode
        self._strategies = strategies
        self._risk = risk_engine
        self._executor = executor
        self._recorder = recorder
        self._metrics = metrics
        self._ordinal = 0

    async def process_snapshot(
        self, snapshot: MarketSnapshot, context: RiskContext, now: datetime
    ) -> RuntimeCycle:
        decisions: list[RiskDecision] = []
        receipts: list[str] = []
        proposal_count = 0
        for strategy in self._strategies:
            for proposal in strategy.evaluate(snapshot):
                proposal_count += 1
                self._metrics.proposals.labels(strategy=proposal.strategy_id).inc()
                await self._record(
                    RecordKind.PROPOSAL,
                    proposal.model_dump(mode="json"),
                    snapshot,
                    now,
                )
                decision = self._risk.evaluate(proposal, context, now)
                decisions.append(decision)
                if decision.approved:
                    outcome = "approved"
                    reason = "none"
                else:
                    outcome = "rejected"
                    reason = ",".join(item.value for item in decision.rejection_reasons)
                self._metrics.risk_decisions.labels(outcome=outcome, reason=reason).inc()
                await self._record(
                    RecordKind.RISK_DECISION,
                    decision.model_dump(mode="json"),
                    snapshot,
                    now,
                )
                if decision.approval is not None:
                    receipt = await self._executor.execute(proposal, decision.approval, now)
                    receipts.append(receipt)
                    self._metrics.simulated_executions.labels(
                        mode=self._mode.value, status="recorded"
                    ).inc()
                    await self._record(
                        RecordKind.SIMULATED_EXECUTION,
                        {"proposal_id": str(proposal.proposal_id), "receipt": receipt},
                        snapshot,
                        now,
                    )
        return RuntimeCycle(proposal_count, tuple(decisions), tuple(receipts))

    async def run(
        self,
        snapshots: AsyncIterator[MarketSnapshot],
        context: RiskContext,
        clock: Callable[[], datetime],
    ) -> None:
        async for snapshot in snapshots:
            await self.process_snapshot(snapshot, context, clock())

    async def _record(
        self,
        kind: RecordKind,
        payload: dict[str, object],
        snapshot: MarketSnapshot,
        received_at: datetime,
    ) -> None:
        self._ordinal += 1
        await self._recorder.append(
            RecordedEnvelope(
                ordinal=self._ordinal,
                kind=kind,
                market_id=snapshot.market.market_id,
                source_timestamp=snapshot.captured_at,
                received_at=received_at,
                payload_json=canonical_payload(payload),
            )
        )
