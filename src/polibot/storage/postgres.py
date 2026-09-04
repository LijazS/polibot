from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from polibot.storage.records import RecordedEnvelope, Recorder, RecordKind
from polibot.storage.schema import RecordedEventRow


class PostgresRecorder(Recorder):
    def __init__(self, sessions: async_sessionmaker[AsyncSession]) -> None:
        self._sessions = sessions

    async def append(self, record: RecordedEnvelope) -> None:
        async with self._sessions() as session:
            session.add(
                RecordedEventRow(
                    record_id=str(record.record_id),
                    ordinal=record.ordinal,
                    kind=record.kind.value,
                    market_id=record.market_id,
                    token_id=record.token_id,
                    source_timestamp=record.source_timestamp,
                    received_at=record.received_at,
                    payload_json=record.payload_json,
                )
            )
            try:
                await session.commit()
            except IntegrityError as exc:
                await session.rollback()
                raise ValueError("duplicate or invalid recorded event") from exc

    async def read_all(self) -> tuple[RecordedEnvelope, ...]:
        async with self._sessions() as session:
            statement = select(RecordedEventRow).order_by(
                RecordedEventRow.source_timestamp,
                RecordedEventRow.received_at,
                RecordedEventRow.ordinal,
                RecordedEventRow.record_id,
            )
            rows = (await session.scalars(statement)).all()
        return tuple(
            RecordedEnvelope(
                record_id=UUID(row.record_id),
                ordinal=row.ordinal,
                kind=RecordKind(row.kind),
                market_id=row.market_id,
                token_id=row.token_id,
                source_timestamp=row.source_timestamp,
                received_at=row.received_at,
                payload_json=row.payload_json,
            )
            for row in rows
        )
