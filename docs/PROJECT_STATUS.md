# Project status

Last updated: 2026-09-05

## Current milestone

V1 software, the continuous PAPER worker, and the non-live V2 safety scaffold are
`TESTED_OFFLINE`. Replay, paper, and shadow paths are available. LIVE remains
deliberately hard-disabled. Worker deployment, strategy effectiveness, and long-running
operational behavior are not yet proven.

## Component status

| Component | Status | Evidence / boundary |
| --- | --- | --- |
| Market discovery and normalization | TESTED_OFFLINE | Strict Gamma/CLOB DTOs, token cross-check, quarantine tests; local public call timed out |
| L2 order book | TESTED_OFFLINE | Snapshot/delta/trade/tick parsing, staleness, invalidation, recovery, bounded reconnect tests |
| Recorder / Parquet / replay | TESTED_OFFLINE | Bounded batch recording/backpressure, canonical envelopes, Parquet round trip, stable replay ordering and CLI |
| PostgreSQL / migrations | IMPLEMENTED | Worker run/heartbeat/selection schema and batch recorder; Alembic offline SQL, no local service test |
| Binary complete-set arbitrage | TESTED_OFFLINE | Depth-aware Decimal scanner, dynamic fee provenance, payoff proof and property tests |
| Vanilla NegRisk | TESTED_OFFLINE | Explicit terminal states, unsupported ambiguity handling, deterministic Decimal solver |
| Holding Rewards pilot | IMPLEMENTED | Dated observation/reconciliation and separated attribution; actual rewards `PENDING_DATA` |
| Deterministic risk engine | TESTED_OFFLINE | Scoped exposure, staleness, fee/depth/proof, drawdown/error, health/reconciliation gates |
| Continuous PAPER worker | TESTED_OFFLINE | Separate process, bounded discovery, REST recovery, WebSocket reconnect, durable heartbeat/readiness, binary risk/paper pipeline; deployment pending |
| Paper / shadow runtime | TESTED_OFFLINE | Proposal-risk-depth simulation-recording integration; no sustained public-data run |
| Accounting / metrics / reports | TESTED_OFFLINE | Separated P&L components, Prometheus output, strategy feasibility summaries |
| Execution state machine | TESTED_OFFLINE | One-use approval, partial/second-leg/unknown/DB-failure paths, PostgreSQL transition journal |
| Wallet / exchange / settlement boundaries | TESTED_OFFLINE | Protocols and deterministic fakes only; no real signer, authenticated transport, or broadcast |
| Reconciliation / kill switches / recovery | TESTED_OFFLINE | State comparison, scoped blockers, rebuild/reconcile/unknown-state restart gate |
| AWS PAPER deployment | DEPLOYED_PAPER | `eu-west-2` run `33976145081`; instance `i-03d8810150224343d`; SHA `fec85ec`; digest `sha256:5ceed0...1728a` |
| AWS PAPER destruction | EXERCISED | Run `33964747292`; exact confirmation, protected plan/apply, OIDC, shared deployment lock, empty final state |
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
- This workstation has no Docker executable and its local AWS token is expired. The
  authorized GitHub OIDC deployment/CI path must perform container and cloud checks.
- Binary/NegRisk opportunity rates, fill quality, latency sensitivity, reward accrual,
  reconciliation stability, market-making queue/adverse selection, and all profitability
  questions are `PENDING_DATA`.
- Exact NegRisk conversion encoding and ambiguous/augmented structure semantics remain
  unsupported pending sufficient official specification.
- AWS/GitHub bootstrap and the first PAPER deployment were verified. The original
  `us-east-1` stack was subsequently destroyed under workflow run `33964747292`; its
  state was emptied before the replacement apply, and the bootstrap state bucket/OIDC
  roles remained in place.
- The first apply required least-privilege read-policy corrections. All partial state
  was reconciled through remote Terraform state; the final plan reports no changes.
- The single-host local PostgreSQL volume has no deployed backup/restore mechanism;
  host replacement can lose PAPER data until that operational gate is implemented.
- The protected destroy workflow was exercised. It permanently removed host-local
  PostgreSQL, application S3 data, ECR images, logs, IAM instance resources, and
  networking while preserving the remote-state bucket and OIDC roles.
- Official Polymarket documentation places primary CLOB servers in `eu-west-2`, with
  direct lowest-latency co-location subject to KYC/KYB approval, and identifies
  `eu-west-1` as the closest non-georestricted region. The replacement `eu-west-2`
  host is deployed for PAPER/public-data use only. Its geoblock check reports
  `GB/ENG blocked=true`, so it is not authorized for order submission.
- The `eu-west-2` deployment reports healthy EC2/system checks, SSM online, no inbound
  security-group rules or SSH key, IMDSv2 required, healthy app/PostgreSQL containers,
  loopback-only port 8000, no PostgreSQL port, PAPER mode, LIVE false, root-owned `0600`
  secret files, immutable AES256 ECR, private encrypted/versioned S3, alarm `OK`, and
  a refreshed no-change Terraform plan. One CLOB `/time` request took approximately
  0.04 seconds; this is an observation, not a latency benchmark.

## Recommended next gate

Deploy the continuous worker through GitHub OIDC, require increasing market-message,
strategy-cycle, and database counters, then run a predefined-duration PAPER recording.
Exercise host/database backup and restore and review cost/log/uptime evidence. Do not
consider any capped micro-live trial until every empirical and safety gate is reviewed.
