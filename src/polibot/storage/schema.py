from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
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
