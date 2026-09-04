from datetime import datetime

import pytest

from polibot.config import ExecutionMode
from polibot.domain.models import OpportunityProposal
from polibot.execution import ExecutionRejected, SimulatedExecutionEngine


@pytest.mark.asyncio
async def test_execution_without_approval_is_rejected(
    valid_proposal: OpportunityProposal, now: datetime
) -> None:
    executor = SimulatedExecutionEngine(ExecutionMode.PAPER)
    with pytest.raises(ExecutionRejected, match="risk approval is required"):
        await executor.execute(valid_proposal, None, now)


def test_bootstrap_executor_cannot_be_live() -> None:
    with pytest.raises(ExecutionRejected, match="does not support LIVE"):
        SimulatedExecutionEngine(ExecutionMode.LIVE)

