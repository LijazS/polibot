# Execution

The immutable boundary is `proposal -> risk decision -> approval -> execution`.
Approval identifies exactly one proposal and expires no later than it. The bootstrap
executor supports only replay/paper/shadow and records intent; it has no exchange or
signing dependency.

V2 execution is a durable state machine: `PLANNED`, `RISK_APPROVED`, `SUBMITTING`,
`PARTIALLY_FILLED`, `HEDGING`, `COMPLETE`, `CANCELLED`, `FAILED`, `RECONCILING`, and
`MANUAL_REVIEW_REQUIRED`. It must handle first-leg fills, second-leg rejection,
partial fills, stale economics, cancel failure, timeouts, unknown submission results,
and restart. Idempotency and exchange reconciliation resolve ambiguity; no assumed
atomic fill is allowed. Live work also needs global/strategy kill and cancel-all paths.

