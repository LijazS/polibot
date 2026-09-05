# Observability

Every observation and decision carries stable identifiers and UTC source/receipt
times. Structured logs must include mode, strategy/run, proposal, approval, market,
and execution identifiers where relevant without secrets. Audit events record risk
rejections, approvals, state transitions, health degradation, reconciliation, and
operator actions.

Metrics must cover freshness/sequence gaps, API errors, opportunity funnel, rejection
reasons, worst-case payout, exposure, unmatched-leg duration, fills, slippage,
drawdown, reconciliation mismatches, and separated P&L components. Readiness must
fail when a dependency required for safe operation is unhealthy; liveness must not
conceal a failed trading path.

`/health` proves a current database-backed heartbeat and safe mode; `/ready` additionally
requires public connectivity, strategy-readable books, and healthy recording. `/status`
exposes discovery, subscription, message, book, strategy, risk, paper, queue, database,
and disk counters. Worker container health requires a current durable heartbeat, so a
live container cannot masquerade as a functioning worker.
