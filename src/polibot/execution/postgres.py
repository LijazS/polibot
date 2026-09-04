from __future__ import annotations

import json
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from polibot.execution.state_machine import ExecutionState, ExecutionTransition
from polibot.storage.schema import ExecutionTransitionRow


class PostgresExecutionTransitionJournal:
    """Durable append/load journal using the migrated execution transition table."""

    def __init__(self, sessions: async_sessionmaker[AsyncSession]) -> None:
        self._sessions = sessions

    async def append(self, transition: ExecutionTransition) -> None:
        async with self._sessions() as session:
            session.add(
                ExecutionTransitionRow(
                    execution_id=str(transition.execution_id),
                    proposal_id=str(transition.proposal_id),
                    transition_number=transition.transition_number,
                    state=transition.state.value,
                    occurred_at=transition.occurred_at,
                    details_json=json.dumps({"detail": transition.detail}),
                )
            )
            await session.commit()

    async def load(self, execution_id: UUID) -> tuple[ExecutionTransition, ...]:
        async with self._sessions() as session:
            statement = (
                select(ExecutionTransitionRow)
                .where(ExecutionTransitionRow.execution_id == str(execution_id))
                .order_by(ExecutionTransitionRow.transition_number)
            )
            rows = (await session.scalars(statement)).all()
        return tuple(
            ExecutionTransition(
                execution_id=UUID(row.execution_id),
                proposal_id=UUID(row.proposal_id),
                transition_number=row.transition_number,
                state=ExecutionState(row.state),
                occurred_at=row.occurred_at,
                detail=str(json.loads(row.details_json)["detail"]),
            )
            for row in rows
        )
