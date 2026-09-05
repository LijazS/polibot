from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from polibot.storage.database import Base


class RecordedEventRow(Base):
    __tablename__ = "recorded_events"
    __table_args__ = (
        UniqueConstraint("record_id"),
        Index("ix_recorded_events_market_time", "market_id", "source_timestamp"),
        Index("ix_recorded_events_kind_time", "kind", "source_timestamp"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    record_id: Mapped[str] = mapped_column(String(36), nullable=False)
    ordinal: Mapped[int] = mapped_column(BigInteger, nullable=False)
    kind: Mapped[str] = mapped_column(String(40), nullable=False)
    market_id: Mapped[str | None] = mapped_column(String(255))
    token_id: Mapped[str | None] = mapped_column(String(255))
    source_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    payload_json: Mapped[str] = mapped_column(Text, nullable=False)


class ProposalRow(Base):
    __tablename__ = "proposals"

    proposal_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    strategy_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    all_in_cost: Mapped[Decimal] = mapped_column(Numeric(38, 6), nullable=False)
    expected_net_edge: Mapped[Decimal] = mapped_column(Numeric(38, 6), nullable=False)
    payload_json: Mapped[str] = mapped_column(Text, nullable=False)


class RiskDecisionRow(Base):
    __tablename__ = "risk_decisions"

    decision_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    proposal_id: Mapped[str] = mapped_column(
        ForeignKey("proposals.proposal_id", ondelete="RESTRICT"), nullable=False, index=True
    )
    evaluated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    approved: Mapped[bool] = mapped_column(nullable=False)
    payload_json: Mapped[str] = mapped_column(Text, nullable=False)


class ExecutionTransitionRow(Base):
    __tablename__ = "execution_transitions"
    __table_args__ = (UniqueConstraint("execution_id", "transition_number"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    execution_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    proposal_id: Mapped[str] = mapped_column(
        ForeignKey("proposals.proposal_id", ondelete="RESTRICT"), nullable=False
    )
    transition_number: Mapped[int] = mapped_column(BigInteger, nullable=False)
    state: Mapped[str] = mapped_column(String(40), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    details_json: Mapped[str] = mapped_column(Text, nullable=False)


class PnLComponentRow(Base):
    __tablename__ = "pnl_components"

    component_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    strategy_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    component_type: Mapped[str] = mapped_column(String(40), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(38, 6), nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    reference_id: Mapped[str | None] = mapped_column(String(255))


class RewardObservationRow(Base):
    __tablename__ = "reward_observations"

    observation_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    market_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    eligible: Mapped[bool] = mapped_column(nullable=False)
    expected_reward: Mapped[Decimal | None] = mapped_column(Numeric(38, 6))
    actual_reward: Mapped[Decimal | None] = mapped_column(Numeric(38, 6))
    provenance: Mapped[str] = mapped_column(Text, nullable=False)


class ReconciliationRow(Base):
    __tablename__ = "reconciliations"

    reconciliation_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    reconciled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    details_json: Mapped[str] = mapped_column(Text, nullable=False)


class WorkerRunRow(Base):
    __tablename__ = "worker_runs"

    run_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    worker_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    stopped_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    execution_mode: Mapped[str] = mapped_column(String(20), nullable=False)
    application_version: Mapped[str] = mapped_column(String(50), nullable=False)
    git_sha: Mapped[str] = mapped_column(String(64), nullable=False)
    configuration_fingerprint: Mapped[str] = mapped_column(String(71), nullable=False)
    strategies_json: Mapped[str] = mapped_column(Text, nullable=False)
    selection_policy_json: Mapped[str] = mapped_column(Text, nullable=False)


class WorkerHeartbeatRow(Base):
    __tablename__ = "worker_heartbeats"

    worker_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    run_id: Mapped[str] = mapped_column(
        ForeignKey("worker_runs.run_id", ondelete="CASCADE"), nullable=False, index=True
    )
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_heartbeat_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    execution_mode: Mapped[str] = mapped_column(String(20), nullable=False)
    current_status: Mapped[str] = mapped_column(String(30), nullable=False)
    ready: Mapped[bool] = mapped_column(Boolean, nullable=False)
    websocket_connected: Mapped[bool] = mapped_column(Boolean, nullable=False)
    markets_discovered: Mapped[int] = mapped_column(BigInteger, nullable=False)
    markets_selected: Mapped[int] = mapped_column(BigInteger, nullable=False)
    markets_subscribed: Mapped[int] = mapped_column(BigInteger, nullable=False)
    messages_received: Mapped[int] = mapped_column(BigInteger, nullable=False)
    books_healthy: Mapped[int] = mapped_column(BigInteger, nullable=False)
    books_stale: Mapped[int] = mapped_column(BigInteger, nullable=False)
    strategy_evaluations: Mapped[int] = mapped_column(BigInteger, nullable=False)
    opportunities_detected: Mapped[int] = mapped_column(BigInteger, nullable=False)
    risk_approvals: Mapped[int] = mapped_column(BigInteger, nullable=False)
    paper_executions: Mapped[int] = mapped_column(BigInteger, nullable=False)
    recorder_queue_depth: Mapped[int] = mapped_column(BigInteger, nullable=False)
    recorder_dropped_events: Mapped[int] = mapped_column(BigInteger, nullable=False)
    database_errors: Mapped[int] = mapped_column(BigInteger, nullable=False)
    reconnect_count: Mapped[int] = mapped_column(BigInteger, nullable=False)
    last_strategy_cycle: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_error: Mapped[str | None] = mapped_column(Text)
    application_version: Mapped[str] = mapped_column(String(50), nullable=False)
    git_sha: Mapped[str] = mapped_column(String(64), nullable=False)
    paper_initial_capital: Mapped[Decimal] = mapped_column(Numeric(38, 6), nullable=False)
    paper_current_capital: Mapped[Decimal] = mapped_column(Numeric(38, 6), nullable=False)
    paper_gross_pnl: Mapped[Decimal] = mapped_column(Numeric(38, 6), nullable=False)
    paper_fees: Mapped[Decimal] = mapped_column(Numeric(38, 6), nullable=False)
    paper_slippage: Mapped[Decimal] = mapped_column(Numeric(38, 6), nullable=False)
    paper_net_pnl: Mapped[Decimal] = mapped_column(Numeric(38, 6), nullable=False)
    database_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    disk_used_percent: Mapped[Decimal] = mapped_column(Numeric(8, 3), nullable=False)


class MarketSelectionRow(Base):
    __tablename__ = "market_selections"
    __table_args__ = (
        UniqueConstraint("run_id", "observed_at", "market_id"),
        Index("ix_market_selections_run_selected", "run_id", "selected"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    run_id: Mapped[str] = mapped_column(
        ForeignKey("worker_runs.run_id", ondelete="CASCADE"), nullable=False
    )
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    market_id: Mapped[str] = mapped_column(String(255), nullable=False)
    condition_id: Mapped[str | None] = mapped_column(String(255))
    selected: Mapped[bool] = mapped_column(Boolean, nullable=False)
    reason: Mapped[str] = mapped_column(String(100), nullable=False)
