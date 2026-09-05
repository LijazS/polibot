from __future__ import annotations

import asyncio
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import func, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from polibot.storage.records import RecordedEnvelope, Recorder
from polibot.storage.schema import (
    MarketSelectionRow,
    RecordedEventRow,
    WorkerHeartbeatRow,
    WorkerRunRow,
)


class RecorderBackpressure(RuntimeError):
    pass


@dataclass
class WorkerStatus:
    worker_id: str
    run_id: str
    started_at: datetime
    last_heartbeat_at: datetime
    execution_mode: str
    current_status: str = "starting"
    ready: bool = False
    websocket_connected: bool = False
    markets_discovered: int = 0
    markets_selected: int = 0
    markets_subscribed: int = 0
    messages_received: int = 0
    books_healthy: int = 0
    books_stale: int = 0
    strategy_evaluations: int = 0
    opportunities_detected: int = 0
    risk_approvals: int = 0
    paper_executions: int = 0
    recorder_queue_depth: int = 0
    recorder_dropped_events: int = 0
    database_errors: int = 0
    reconnect_count: int = 0
    last_strategy_cycle: datetime | None = None
    last_error: str | None = None
    application_version: str = "unknown"
    git_sha: str = "unknown"
    paper_initial_capital: Decimal = Decimal("0")
    paper_current_capital: Decimal = Decimal("0")
    paper_gross_pnl: Decimal = Decimal("0")
    paper_fees: Decimal = Decimal("0")
    paper_slippage: Decimal = Decimal("0")
    paper_net_pnl: Decimal = Decimal("0")
    database_size_bytes: int = 0
    disk_used_percent: Decimal = Decimal("0")


@dataclass(frozen=True)
class MarketSelection:
    market_id: str
    condition_id: str | None
    selected: bool
    reason: str


class WorkerStateStore:
    def __init__(self, sessions: async_sessionmaker[AsyncSession]) -> None:
        self._sessions = sessions

    async def start_run(
        self,
        status: WorkerStatus,
        *,
        configuration_fingerprint: str,
        strategies_json: str,
        selection_policy_json: str,
    ) -> None:
        async with self._sessions() as session:
            session.add(
                WorkerRunRow(
                    run_id=status.run_id,
                    worker_id=status.worker_id,
                    started_at=status.started_at,
                    stopped_at=None,
                    execution_mode=status.execution_mode,
                    application_version=status.application_version,
                    git_sha=status.git_sha,
                    configuration_fingerprint=configuration_fingerprint,
                    strategies_json=strategies_json,
                    selection_policy_json=selection_policy_json,
                )
            )
            await session.commit()
        await self.save_heartbeat(status)

    async def stop_run(self, run_id: str, stopped_at: datetime) -> None:
        async with self._sessions() as session:
            await session.execute(
                update(WorkerRunRow)
                .where(WorkerRunRow.run_id == run_id)
                .values(stopped_at=stopped_at)
            )
            await session.commit()

    async def save_heartbeat(self, status: WorkerStatus) -> None:
        values = asdict(status)
        statement = insert(WorkerHeartbeatRow).values(**values)
        statement = statement.on_conflict_do_update(
            index_elements=[WorkerHeartbeatRow.worker_id],
            set_={key: value for key, value in values.items() if key != "worker_id"},
        )
        async with self._sessions() as session:
            await session.execute(statement)
            await session.commit()

    async def record_selections(
        self, run_id: str, observed_at: datetime, selections: tuple[MarketSelection, ...]
    ) -> None:
        if not selections:
            return
        async with self._sessions() as session:
            session.add_all(
                MarketSelectionRow(
                    run_id=run_id,
                    observed_at=observed_at,
                    market_id=item.market_id,
                    condition_id=item.condition_id,
                    selected=item.selected,
                    reason=item.reason,
                )
                for item in selections
            )
            await session.commit()

    async def latest_status(self) -> dict[str, Any] | None:
        async with self._sessions() as session:
            row = await session.scalar(
                select(WorkerHeartbeatRow).order_by(WorkerHeartbeatRow.last_heartbeat_at.desc())
            )
        if row is None:
            return None
        return {
            column.name: getattr(row, column.name)
            for column in WorkerHeartbeatRow.__table__.columns
        }

    async def activity_counts(self, since: datetime | None = None) -> dict[str, int]:
        statement = select(RecordedEventRow.kind, func.count(RecordedEventRow.id)).group_by(
            RecordedEventRow.kind
        )
        if since is not None:
            statement = statement.where(RecordedEventRow.received_at >= since)
        async with self._sessions() as session:
            rows = (await session.execute(statement)).all()
        return {str(kind): int(count) for kind, count in rows}

    async def database_size_bytes(self) -> int:
        async with self._sessions() as session:
            value = await session.scalar(select(func.pg_database_size(func.current_database())))
        return int(value or 0)

    async def recent_runs(self, limit: int = 20) -> tuple[dict[str, Any], ...]:
        async with self._sessions() as session:
            rows = (
                await session.scalars(
                    select(WorkerRunRow).order_by(WorkerRunRow.started_at.desc()).limit(limit)
                )
            ).all()
        return tuple(
            {column.name: getattr(row, column.name) for column in WorkerRunRow.__table__.columns}
            for row in rows
        )


class BatchedPostgresRecorder(Recorder):
    """Bounded, loss-intolerant writer for decision-reproduction records."""

    def __init__(
        self,
        sessions: async_sessionmaker[AsyncSession],
        *,
        batch_size: int,
        flush_seconds: float,
        queue_size: int,
    ) -> None:
        self._sessions = sessions
        self._batch_size = batch_size
        self._flush_seconds = flush_seconds
        self._queue: asyncio.Queue[RecordedEnvelope] = asyncio.Queue(maxsize=queue_size)
        self._stopping = asyncio.Event()
        self._task: asyncio.Task[None] | None = None
        self.degraded = False
        self.database_errors = 0
        self.dropped_events = 0
        self.batches_written = 0

    @property
    def queue_depth(self) -> int:
        return self._queue.qsize()

    async def start(self) -> None:
        if self._task is not None:
            raise RuntimeError("recorder already started")
        self._task = asyncio.create_task(self._run(), name="postgres-batch-recorder")

    async def append(self, record: RecordedEnvelope) -> None:
        if self._task is None or self._task.done():
            self.degraded = True
            raise RecorderBackpressure("recorder is not running")
        try:
            self._queue.put_nowait(record)
        except asyncio.QueueFull as exc:
            self.degraded = True
            self.dropped_events += 1
            raise RecorderBackpressure("recorder queue is full") from exc

    async def read_all(self) -> tuple[RecordedEnvelope, ...]:
        from polibot.storage.postgres import PostgresRecorder

        return await PostgresRecorder(self._sessions).read_all()

    async def close(self, timeout_seconds: float = 30.0) -> None:
        self._stopping.set()
        if self._task is None:
            return
        try:
            await asyncio.wait_for(self._task, timeout_seconds)
        except TimeoutError as exc:
            self._task.cancel()
            self.dropped_events += self._queue.qsize()
            self.degraded = True
            raise RecorderBackpressure("recorder did not flush before shutdown") from exc

    async def _run(self) -> None:
        pending: list[RecordedEnvelope] = []
        while not self._stopping.is_set() or not self._queue.empty() or pending:
            if not pending:
                try:
                    pending.append(await asyncio.wait_for(self._queue.get(), self._flush_seconds))
                except TimeoutError:
                    continue
            while len(pending) < self._batch_size:
                try:
                    pending.append(self._queue.get_nowait())
                except asyncio.QueueEmpty:
                    break
            try:
                await self._write(tuple(pending))
            except Exception:
                self.database_errors += 1
                self.degraded = True
                await asyncio.sleep(min(self._flush_seconds, 5.0))
                continue
            for _ in pending:
                self._queue.task_done()
            pending.clear()
            self.batches_written += 1
            self.degraded = self.dropped_events > 0

    async def _write(self, records: tuple[RecordedEnvelope, ...]) -> None:
        async with self._sessions() as session:
            session.add_all(
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
                for record in records
            )
            await session.commit()


def utc_now() -> datetime:
    return datetime.now(UTC)
