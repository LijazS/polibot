# Roadmap

Progress is controlled by evidence-based gates. Feature presence alone does not
promote a strategy or execution mode.

## V1.0 — foundation, recorder, replay, paper strategies

Exit only when discovery/token/status/fee metadata and sequence-aware L2 ingestion
are validated; raw data reproduces normalized state; depth-aware replay assumptions
are disclosed; binary and validated vanilla NegRisk scanners pass unit/property
tests; Holding Rewards observations are captured; deterministic rejection tests
pass; and paper accounting reconciles without unexplained differences.

Engineering state: `TESTED_OFFLINE` on 2026-09-05. Public connectivity, PostgreSQL
service integration, sustained operation, and strategy effectiveness remain evidence
gates; V1 feature completion does not imply profitability.

## V1.1 — sustained shadow validation

Exit only after a defined-duration shadow run has availability and data-quality
evidence, opportunity/executability statistics, modeled legging failures, stable
P&L attribution, and zero unexplained accounting mismatches. Thresholds must be set
in a reviewed plan before the run, not selected afterward.

## V2.0 — guarded micro-live structural execution

Exit only when live remains disabled by default; signer/wallet boundaries receive
focused review; capital, exposure, drawdown, staleness, and error limits fail closed;
the multi-leg state machine survives partial fills, ambiguous responses, restarts,
and reconciliation; kill/cancel controls and runbooks are exercised; and tightly
capped structural execution has controlled evidence. This gate does not promote
market making.

Non-live infrastructure state: `DEPLOYED_PAPER` on 2026-09-05. The state machine,
fake-only boundaries, reconciliation, kill/recovery gates, dedicated AWS PAPER stack,
OIDC workflow, and immutable SSM deployment path exist. AWS/GitHub bootstrap, Terraform
apply, immutable image push, SSM deployment, container health, and PAPER/live-disable
checks are verified. Sustained runtime, backup/restore, and empirical strategy evidence
remain pending. The guarded micro-live exit gate is not met and LIVE remains hard-disabled.

## V2.x — market-making shadow research

Measure spread capture, inventory, adverse selection, fees, rebates, rewards, and
operational failures separately. Live promotion requires its own ADR, quantitative
thresholds, controlled validation, and operator approval.

Shadow quote generation is `TESTED_OFFLINE`; empirical fill, queue, adverse-selection,
inventory, and P&L evidence is `PENDING_DATA`.

## V3 candidates

Live inventory-aware market making, formal cross-market relationship solving,
LLM-assisted candidate discovery followed by deterministic validation, richer
research tooling, and justified multi-wallet support. Rust, ClickHouse, managed
deployment, or Kubernetes require measured need; EKS is not a default destination.
