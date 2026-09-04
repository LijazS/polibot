# Technical debt and deliberate deferrals

- Domain coverage is broad but persistence mappings are intentionally absent until
  ingestion/replay access patterns are designed.
- Risk limits currently cover the bootstrap subset only; market/event/strategy,
  unmatched-leg duration, slippage, error-count, balance, and drawdown controls are
  required before execution work.
- Health checks are synchronous abstractions and have no database/stream probes yet.
- The simulated executor records only a deterministic receipt string; durable audit
  and idempotency arrive with the execution schema.
- No Prometheus metrics, Parquet writer, Alembic configuration, or adapter fixtures exist.
- API models need current official-document verification before implementation.

