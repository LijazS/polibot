from sqlalchemy import DateTime, Numeric

from polibot.storage import schema as storage_schema  # noqa: F401
from polibot.storage.database import Base


def test_expected_durable_tables_are_registered() -> None:
    assert set(Base.metadata.tables) == {
        "recorded_events",
        "proposals",
        "risk_decisions",
        "execution_transitions",
        "pnl_components",
        "reward_observations",
        "reconciliations",
        "worker_runs",
        "worker_heartbeats",
        "market_selections",
    }


def test_financial_columns_have_explicit_decimal_precision() -> None:
    columns = [
        Base.metadata.tables["proposals"].c.all_in_cost,
        Base.metadata.tables["proposals"].c.expected_net_edge,
        Base.metadata.tables["pnl_components"].c.amount,
        Base.metadata.tables["worker_heartbeats"].c.paper_current_capital,
        Base.metadata.tables["worker_heartbeats"].c.paper_net_pnl,
    ]
    for column in columns:
        assert isinstance(column.type, Numeric)
        assert (column.type.precision, column.type.scale) == (38, 6)


def test_persisted_timestamps_are_timezone_aware() -> None:
    column = Base.metadata.tables["recorded_events"].c.source_timestamp
    assert isinstance(column.type, DateTime)
    assert column.type.timezone is True
