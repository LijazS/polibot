# Database migrations

Alembic owns all durable schema changes. The initial migration creates append-only
recording, proposal/risk, execution transition, P&L, reward observation, and
reconciliation tables with UTC-aware columns, explicit financial precision,
uniqueness constraints, foreign keys, and query-driven indexes.

Generate SQL without connecting to a database with `alembic upgrade head --sql`.
Production paths run reviewed migrations; application startup never calls
`metadata.create_all()`.
