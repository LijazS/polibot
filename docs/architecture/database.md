# Database

PostgreSQL is the durable application store. The planned model records markets,
events, tokens, raw observations, normalized snapshots, proposals, risk decisions,
execution transitions, orders, fills, balances, positions, settlement, rewards,
reconciliation, P&L components, strategy runs, and audit events.

Identifiers and source/receipt timestamps must support deterministic reconstruction.
Writes that cross a decision boundary should be transactional and idempotent.
Append-only facts are preferred for audit data. Alembic migrations begin with the
first schema; retention and Parquet export policies must be documented before data
volume work. Redis is not part of the bootstrap.

