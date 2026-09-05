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
| AWS PAPER deployment | DEPLOYED_PAPER | Workflow run `33963697738`; instance `i-0a24009387e20f235`; SHA `a3545a2`; digest `sha256:ec3988...26cdd` |
| AWS PAPER destruction | IMPLEMENTED_NOT_EXERCISED | Manual main-only workflow; exact confirmation, protected plan/apply, OIDC, shared deployment lock, bootstrap preservation |
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
- AWS/GitHub bootstrap and the first PAPER deployment are verified. Terraform reports
  no drift; EC2 and SSM are online; the alarm is OK; app and PostgreSQL containers are
  healthy; the app reports PAPER with live disabled; secret files are root-owned mode
  `0600`; and the host runs the recorded commit by immutable ECR digest.
- The first apply required least-privilege read-policy corrections. All partial state
  was reconciled through remote Terraform state; the final plan reports no changes.
- The single-host local PostgreSQL volume has no deployed backup/restore mechanism;
  host replacement can lose PAPER data until that operational gate is implemented.
- A protected destroy workflow exists but has intentionally not been exercised. It
  permanently removes host-local PostgreSQL, application S3 data, ECR images, logs,
  IAM instance resources, and networking while preserving remote state and OIDC roles.
- Official Polymarket documentation places primary CLOB servers in `eu-west-2`, with
  direct lowest-latency co-location subject to KYC/KYB approval, and identifies
  `eu-west-1` as the closest non-georestricted region. The current `us-east-1` PAPER
  host has not been migrated; any region move needs measured evidence and a data plan.

## Recommended next gate

Run a predefined-duration PAPER recording on the deployed host, exercise host/database
backup and restore, and review cost/log/uptime evidence. Do not consider any capped
micro-live trial until reconciliation, restart, cancel/heartbeat, security, and
empirical gates are reviewed.
