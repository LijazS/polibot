# Project status

Last updated: 2026-09-05

## Current milestone

V1 software and the non-live V2 safety scaffold are `TESTED_OFFLINE`. Replay,
paper, and shadow paths are available. LIVE remains deliberately hard-disabled.
Strategy effectiveness and long-running operational behavior are not proven.

## Component status

| Component | Status | Evidence / boundary |
| --- | --- | --- |
| Market discovery and normalization | TESTED_OFFLINE | Strict Gamma/CLOB DTOs, token cross-check, quarantine tests; local public call timed out |
| L2 order book | TESTED_OFFLINE | Snapshot/delta/trade/tick parsing, staleness, invalidation, recovery, bounded reconnect tests |
| Recorder / Parquet / replay | TESTED_OFFLINE | Canonical append-only envelopes, Parquet round trip, stable replay ordering and CLI |
| PostgreSQL / migrations | IMPLEMENTED | Async recorder, constrained schema, Alembic offline SQL; no PostgreSQL service test |
| Binary complete-set arbitrage | TESTED_OFFLINE | Depth-aware Decimal scanner, dynamic fee provenance, payoff proof and property tests |
| Vanilla NegRisk | TESTED_OFFLINE | Explicit terminal states, unsupported ambiguity handling, deterministic Decimal solver |
| Holding Rewards pilot | IMPLEMENTED | Dated observation/reconciliation and separated attribution; actual rewards `PENDING_DATA` |
| Deterministic risk engine | TESTED_OFFLINE | Scoped exposure, staleness, fee/depth/proof, drawdown/error, health/reconciliation gates |
| Paper / shadow runtime | TESTED_OFFLINE | Proposal-risk-simulation-recording integration; no sustained public-data run |
| Accounting / metrics / reports | TESTED_OFFLINE | Separated P&L components, Prometheus output, strategy feasibility summaries |
| Execution state machine | TESTED_OFFLINE | One-use approval, partial/second-leg/unknown/DB-failure paths, PostgreSQL transition journal |
| Wallet / exchange / settlement boundaries | TESTED_OFFLINE | Protocols and deterministic fakes only; no real signer, authenticated transport, or broadcast |
| Reconciliation / kill switches / recovery | TESTED_OFFLINE | State comparison, scoped blockers, rebuild/reconcile/unknown-state restart gate |
| AWS / Terraform | TESTED_OFFLINE | Format and validate pass; no plan/apply or cloud access |
| Shadow market making | TESTED_OFFLINE | Decimal midpoint/microprice/imbalance, inventory skew and shutdowns; fills/P&L `PENDING_DATA` |

## Evidence gates

- `REPLAY_READY`: engineering path and deterministic tests pass.
- `PAPER_READY`: offline simulation path and safety gates pass.
- `SHADOW_READY`: intent-generation path exists, but sustained operation is
  `PENDING_EMPIRICAL_VALIDATION`.
- `TESTED_AGAINST_PUBLIC_API`: not achieved; the only local read-only smoke call timed out.
- `LIVE_READY`: false. There is no production signer, authenticated write adapter, on-chain
  broadcaster, live configuration, or authorization to activate one.

## Known blockers and deferred evidence

- Direct public API runtime validation is blocked by connect timeouts in this environment.
- PostgreSQL, Docker Compose, and sustained WebSocket/runtime behavior need service testing.
- Binary/NegRisk opportunity rates, fill quality, latency sensitivity, reward accrual,
  reconciliation stability, market-making queue/adverse selection, and all profitability
  questions are `PENDING_DATA`.
- Exact NegRisk conversion encoding and ambiguous/augmented structure semantics remain
  unsupported pending sufficient official specification.
- Terraform was validated statically only; network, AMI, backend, monitoring alarms,
  restore, deployment, and security review remain future operator work.

## Recommended next gate

Collect a predefined-duration public-data recording and paper/shadow dataset, then run
the existing replay/report tooling. Do not consider any capped micro-live trial until
reconciliation, restart, cancel/heartbeat, security, and empirical gates are reviewed.
