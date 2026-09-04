"""Initial append-only recording and decision schema."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260904_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "recorded_events",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("record_id", sa.String(36), nullable=False),
        sa.Column("ordinal", sa.BigInteger(), nullable=False),
        sa.Column("kind", sa.String(40), nullable=False),
        sa.Column("market_id", sa.String(255)),
        sa.Column("token_id", sa.String(255)),
        sa.Column("source_timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("payload_json", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("record_id"),
    )
    op.create_index(
        "ix_recorded_events_market_time",
        "recorded_events",
        ["market_id", "source_timestamp"],
    )
    op.create_index(
        "ix_recorded_events_kind_time",
        "recorded_events",
        ["kind", "source_timestamp"],
    )
    op.create_table(
        "proposals",
        sa.Column("proposal_id", sa.String(36), primary_key=True),
        sa.Column("strategy_id", sa.String(100), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("all_in_cost", sa.Numeric(38, 6), nullable=False),
        sa.Column("expected_net_edge", sa.Numeric(38, 6), nullable=False),
        sa.Column("payload_json", sa.Text(), nullable=False),
    )
    op.create_index("ix_proposals_strategy_id", "proposals", ["strategy_id"])
    op.create_table(
        "risk_decisions",
        sa.Column("decision_id", sa.String(36), primary_key=True),
        sa.Column("proposal_id", sa.String(36), nullable=False),
        sa.Column("evaluated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("approved", sa.Boolean(), nullable=False),
        sa.Column("payload_json", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["proposal_id"], ["proposals.proposal_id"], ondelete="RESTRICT"),
    )
    op.create_index("ix_risk_decisions_proposal_id", "risk_decisions", ["proposal_id"])
    op.create_table(
        "execution_transitions",
        sa.Column("id", sa.BigInteger(), autoincrement=True, primary_key=True),
        sa.Column("execution_id", sa.String(36), nullable=False),
        sa.Column("proposal_id", sa.String(36), nullable=False),
        sa.Column("transition_number", sa.BigInteger(), nullable=False),
        sa.Column("state", sa.String(40), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("details_json", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["proposal_id"], ["proposals.proposal_id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("execution_id", "transition_number"),
    )
    op.create_index(
        "ix_execution_transitions_execution_id",
        "execution_transitions",
        ["execution_id"],
    )
    op.create_table(
        "pnl_components",
        sa.Column("component_id", sa.String(36), primary_key=True),
        sa.Column("strategy_id", sa.String(100), nullable=False),
        sa.Column("component_type", sa.String(40), nullable=False),
        sa.Column("amount", sa.Numeric(38, 6), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reference_id", sa.String(255)),
    )
    op.create_index("ix_pnl_components_strategy_id", "pnl_components", ["strategy_id"])
    op.create_table(
        "reward_observations",
        sa.Column("observation_id", sa.String(36), primary_key=True),
        sa.Column("market_id", sa.String(255), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("eligible", sa.Boolean(), nullable=False),
        sa.Column("expected_reward", sa.Numeric(38, 6)),
        sa.Column("actual_reward", sa.Numeric(38, 6)),
        sa.Column("provenance", sa.Text(), nullable=False),
    )
    op.create_index("ix_reward_observations_market_id", "reward_observations", ["market_id"])
    op.create_table(
        "reconciliations",
        sa.Column("reconciliation_id", sa.String(36), primary_key=True),
        sa.Column("reconciled_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(40), nullable=False),
        sa.Column("details_json", sa.Text(), nullable=False),
    )
    op.create_index("ix_reconciliations_status", "reconciliations", ["status"])


def downgrade() -> None:
    op.drop_index("ix_reconciliations_status", table_name="reconciliations")
    op.drop_table("reconciliations")
    op.drop_index("ix_reward_observations_market_id", table_name="reward_observations")
    op.drop_table("reward_observations")
    op.drop_index("ix_pnl_components_strategy_id", table_name="pnl_components")
    op.drop_table("pnl_components")
    op.drop_index("ix_execution_transitions_execution_id", table_name="execution_transitions")
    op.drop_table("execution_transitions")
    op.drop_index("ix_risk_decisions_proposal_id", table_name="risk_decisions")
    op.drop_table("risk_decisions")
    op.drop_index("ix_proposals_strategy_id", table_name="proposals")
    op.drop_table("proposals")
    op.drop_index("ix_recorded_events_kind_time", table_name="recorded_events")
    op.drop_index("ix_recorded_events_market_time", table_name="recorded_events")
    op.drop_table("recorded_events")
