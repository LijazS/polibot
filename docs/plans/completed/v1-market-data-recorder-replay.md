# V1 L2 market data, recorder, and replay

Status: completed (`TESTED_OFFLINE`, PostgreSQL runtime pending)  
Started: 2026-09-04  
Completed: 2026-09-04

## Delivered

- Official-shape message DTOs and decimal-preserving parser.
- Fail-closed L2 book with snapshot/delta/trade/tick support, staleness,
  identity/tick/crossed checks, disconnect invalidation, and snapshot recovery.
- Public WebSocket and REST snapshot clients with timeout, heartbeat, and bounded reconnect.
- Canonical append-only envelopes, in-memory and PostgreSQL recorder adapters.
- Seven-table SQLAlchemy schema and reversible Alembic baseline.
- Schema-versioned Parquet archive and deterministic replay engine/CLI with manifest.

## Verification

- Ruff passed after implementation fixes.
- Strict mypy passed for 45 source files after implementation fixes.
- Pytest passed: 52 tests.
- Alembic `upgrade head --sql` produced PostgreSQL DDL without a connection.
- Actual WebSocket, snapshot endpoint, and PostgreSQL service are not environment-tested.

