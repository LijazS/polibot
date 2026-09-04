from datetime import datetime
from typing import Protocol

from polibot.config import ExecutionMode
from polibot.domain.models import OpportunityProposal, RiskApproval


class ExecutionRejected(RuntimeError):
    pass


class ExecutionEngine(Protocol):
    async def execute(
        self, proposal: OpportunityProposal, approval: RiskApproval | None, now: datetime
    ) -> str: ...


class SimulatedExecutionEngine:
    """Records safe-mode intent; contains no exchange or signer dependency."""

    def __init__(self, mode: ExecutionMode) -> None:
        if mode is ExecutionMode.LIVE:
            raise ExecutionRejected("bootstrap executor does not support LIVE mode")
        self._mode = mode

    async def execute(
        self, proposal: OpportunityProposal, approval: RiskApproval | None, now: datetime
    ) -> str:
        if approval is None:
            raise ExecutionRejected("risk approval is required")
        if approval.proposal_id != proposal.proposal_id:
            raise ExecutionRejected("approval does not match proposal")
        if now >= approval.valid_until or now >= proposal.expires_at:
            raise ExecutionRejected("approval or proposal has expired")
        return f"{self._mode.value}:recorded:{proposal.proposal_id}"
