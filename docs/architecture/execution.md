# Execution

The immutable boundary is `proposal -> risk decision -> approval -> execution`.
Approval identifies exactly one proposal and expires no later than it. The bootstrap
executor supports only replay/paper/shadow and records intent. LIVE construction is
hard-rejected. Strategies cannot import or receive an exchange adapter or signer.

V2 execution is a durable state machine: `PLANNED`, `RISK_APPROVED`, `SUBMITTING`,
`PARTIALLY_FILLED`, `HEDGING`, `COMPLETE`, `CANCELLED`, `FAILED`, `RECONCILING`,
`UNKNOWN_EXTERNAL_STATE`, and `MANUAL_REVIEW_REQUIRED`. The implemented coordinator
persists each transition through an optional PostgreSQL journal before advancing
in-memory state and consumes each proposal exactly once. It handles first-leg fills,
second-leg rejection,
partial fills, stale economics, cancel failure, timeouts, unknown submission results,
and restart gates. An ambiguous result stops in `UNKNOWN_EXTERNAL_STATE`; it cannot
be retried and must enter reconciliation/manual review. The exchange port models
create/cancel/cancel-all/query/fills/heartbeat and has only a deterministic fake.

Kill switches cover global, strategy, market, event, and health scopes. Recovery
requires durable state restoration, healthy reconciliation, rebuilt books for every
affected market, and zero unresolved external executions before new execution.
