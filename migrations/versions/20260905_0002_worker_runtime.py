"""Continuous PAPER worker run, heartbeat, and market selection state."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260905_0002"
down_revision: str | None = "20260904_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "worker_runs",
        sa.Column("run_id", sa.String(36), primary_key=True),
        sa.Column("worker_id", sa.String(100), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("stopped_at", sa.DateTime(timezone=True)),
        sa.Column("execution_mode", sa.String(20), nullable=False),
        sa.Column("application_version", sa.String(50), nullable=False),
        sa.Column("git_sha", sa.String(64), nullable=False),
        sa.Column("configuration_fingerprint", sa.String(71), nullable=False),
        sa.Column("strategies_json", sa.Text(), nullable=False),
        sa.Column("selection_policy_json", sa.Text(), nullable=False),
    )
    op.create_index("ix_worker_runs_worker_id", "worker_runs", ["worker_id"])
    op.create_table(
        "worker_heartbeats",
        sa.Column("worker_id", sa.String(100), primary_key=True),
        sa.Column("run_id", sa.String(36), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_heartbeat_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("execution_mode", sa.String(20), nullable=False),
        sa.Column("current_status", sa.String(30), nullable=False),
        sa.Column("ready", sa.Boolean(), nullable=False),
        sa.Column("websocket_connected", sa.Boolean(), nullable=False),
        sa.Column("markets_discovered", sa.BigInteger(), nullable=False),
        sa.Column("markets_selected", sa.BigInteger(), nullable=False),
        sa.Column("markets_subscribed", sa.BigInteger(), nullable=False),
        sa.Column("messages_received", sa.BigInteger(), nullable=False),
        sa.Column("books_healthy", sa.BigInteger(), nullable=False),
        sa.Column("books_stale", sa.BigInteger(), nullable=False),
        sa.Column("strategy_evaluations", sa.BigInteger(), nullable=False),
        sa.Column("opportunities_detected", sa.BigInteger(), nullable=False),
        sa.Column("risk_approvals", sa.BigInteger(), nullable=False),
        sa.Column("paper_executions", sa.BigInteger(), nullable=False),
        sa.Column("recorder_queue_depth", sa.BigInteger(), nullable=False),
        sa.Column("recorder_dropped_events", sa.BigInteger(), nullable=False),
        sa.Column("database_errors", sa.BigInteger(), nullable=False),
        sa.Column("reconnect_count", sa.BigInteger(), nullable=False),
        sa.Column("last_strategy_cycle", sa.DateTime(timezone=True)),
        sa.Column("last_error", sa.Text()),
        sa.Column("application_version", sa.String(50), nullable=False),
        sa.Column("git_sha", sa.String(64), nullable=False),
        sa.Column("paper_initial_capital", sa.Numeric(38, 6), nullable=False),
        sa.Column("paper_current_capital", sa.Numeric(38, 6), nullable=False),
        sa.Column("paper_gross_pnl", sa.Numeric(38, 6), nullable=False),
        sa.Column("paper_fees", sa.Numeric(38, 6), nullable=False),
        sa.Column("paper_slippage", sa.Numeric(38, 6), nullable=False),
        sa.Column("paper_net_pnl", sa.Numeric(38, 6), nullable=False),
        sa.Column("database_size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("disk_used_percent", sa.Numeric(8, 3), nullable=False),
        sa.ForeignKeyConstraint(["run_id"], ["worker_runs.run_id"], ondelete="CASCADE"),
    )
    op.create_index("ix_worker_heartbeats_run_id", "worker_heartbeats", ["run_id"])
    op.create_table(
        "market_selections",
        sa.Column("id", sa.BigInteger(), autoincrement=True, primary_key=True),
        sa.Column("run_id", sa.String(36), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("market_id", sa.String(255), nullable=False),
        sa.Column("condition_id", sa.String(255)),
        sa.Column("selected", sa.Boolean(), nullable=False),
        sa.Column("reason", sa.String(100), nullable=False),
        sa.ForeignKeyConstraint(["run_id"], ["worker_runs.run_id"], ondelete="CASCADE"),
        sa.UniqueConstraint("run_id", "observed_at", "market_id"),
    )
    op.create_index(
        "ix_market_selections_run_selected", "market_selections", ["run_id", "selected"]
    )


def downgrade() -> None:
    op.drop_index("ix_market_selections_run_selected", table_name="market_selections")
    op.drop_table("market_selections")
    op.drop_index("ix_worker_heartbeats_run_id", table_name="worker_heartbeats")
    op.drop_table("worker_heartbeats")
    op.drop_index("ix_worker_runs_worker_id", table_name="worker_runs")
    op.drop_table("worker_runs")
