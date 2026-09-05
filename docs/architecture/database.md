# Database

PostgreSQL is the durable application store. The initial model records raw and
normalized event envelopes, proposals, risk decisions,
execution transitions, orders, fills, balances, positions, settlement, rewards,
reconciliation, P&L components, strategy runs, and audit events.

Identifiers and source/receipt timestamps must support deterministic reconstruction.
Writes that cross a decision boundary should be transactional and idempotent.
Append-only facts are preferred for audit data. Alembic migrations begin with the
first schema; retention and Parquet export policies must be documented before data
volume work. The baseline migration also creates execution transition, P&L, reward
observation, and reconciliation tables. Financial columns use `NUMERIC(38, 6)`.
Application startup never creates schemas automatically. Redis remains absent.

The worker adds append-only run and market-selection history plus one upserted current
heartbeat per worker identity. High-volume envelopes use a bounded in-process queue and
multi-row PostgreSQL transactions. A full queue rejects the observation, marks recording
degraded, and fails readiness; it is not an unbounded buffer or a silent critical drop.
