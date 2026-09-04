# Polibot — Codex Master Bootstrap Prompt

You are bootstrapping and preparing a repository named **Polibot**.

This prompt transfers the project context, product intent, architectural principles, strategy scope, safety requirements, and repository-documentation expectations into the codebase. Treat the repository itself as the long-term source of truth after this bootstrap task.

Do **not** try to implement every future trading strategy in one enormous change. Your first job is to create a coherent, production-minded foundation and documentation system for V1/V2, plus the initial safe code scaffold needed to support those phases.

If useful code already exists in the repository, inspect it first and preserve it. Adapt this structure around existing work rather than destructively replacing working code.

Do not ask the user questions unless you are genuinely blocked. Where details are unresolved, make the safest reasonable assumption, document it, and add an explicit open question or ADR candidate.

---

# 1. PROJECT INTENT

Polibot is an automated Polymarket research/trading platform whose primary objective is **capital preservation**, not maximum turnover or high-risk speculation.

The project should focus on low-directional-risk, structurally verifiable strategies and only move from simulation to real execution after realistic validation.

This project must never claim or assume guaranteed profitability.

The target system should eventually operate with little or no day-to-day human intervention, but autonomy must come from deterministic rules, risk controls, reconciliation, and strong operational engineering—not from letting an LLM freely decide what to bet on.

The system should be able to choose **not to trade**. Zero trades can be the correct result when no opportunity passes all safety checks.

Priority order:

1. Correctness
2. Capital safety
3. Deterministic risk controls
4. Auditability/reconciliation
5. Observability
6. Testability
7. Execution quality
8. Profitability
9. Latency optimization

---

# 2. STRATEGIC CONTEXT

The feasibility study for this project identified several strategy classes. The safest and most feasible near-term strategies are structural/mechanical strategies rather than prediction of real-world outcomes.

## A. Binary YES+NO complete-set arbitrage

For a complementary binary market, if executable acquisition of YES and NO plus all costs is below the deterministic terminal/merge value, a structural arbitrage may exist.

Never implement the naive rule:

`YES_ASK + NO_ASK < 1`

Real economics must include:

- executable depth;
- current fees;
- price/quantity rounding;
- slippage;
- order minimums;
- partial fills;
- multi-leg execution latency;
- legging risk;
- market status;
- safety margin;
- split/merge/redeem mechanics where relevant.

Conceptually:

`net_edge = deterministic_value - all_in_cost - execution_risk_buffer`

Only a positive net edge above a configured threshold may become an `OpportunityProposal`.

The largest practical risk is legging risk: one side fills while the other disappears or reprices. Execution and risk systems must explicitly model and control this.

This is a core V1 strategy.

## B. Vanilla NegRisk / mutually-exclusive multi-outcome arbitrage

Model all valid terminal states and search for a portfolio whose payoff is at least a target value in every valid state while its executable acquisition cost is lower.

Conceptually:

Minimize portfolio acquisition cost subject to:

`payout(state_i) >= target_payout`

for every valid terminal state `state_i`.

Linear optimization may be used where appropriate.

Constraints:

- Never infer mutual exclusivity from outcome names alone.
- Use machine-readable event/market metadata and supported mechanics.
- Avoid ambiguous/augmented NegRisk structures until explicitly supported.
- Treat “Other,” placeholder outcomes, and the ability to add outcomes conservatively.
- A proposal must include a deterministic worst-case payoff proof.

This is a core V1 strategy.

## C. Complete-set Holding Rewards pilot

A complete complementary YES+NO set is directionally neutral while intact, and Polymarket may offer Holding Rewards on eligible markets.

This creates a low-directional-risk hypothesis:

`complete set + eligible holding reward program -> possible reward-bearing neutral inventory`

Treat this as an **empirical pilot**, not an assumed guaranteed strategy.

Requirements:

- Dynamically discover current reward eligibility and parameters.
- Never hard-code a historical reward percentage.
- Record observations needed to compare expected and actual rewards.
- Attribute holding rewards separately from trading P&L.
- Start in observational/paper mode and validate with tiny controlled exposure only after the live-execution system exists.
- Do not scale merely because the position is directionally neutral; platform, program, settlement, wallet, and operational risks remain.

This is a core V1 research/pilot strategy.

## D. Inventory-aware market making

Market making can combine spread capture, maker rebates, and liquidity rewards, but introduces inventory risk and adverse selection.

The future design should consider:

- fair value / midpoint / microprice;
- order-book imbalance;
- inventory skew;
- volatility;
- event/news risk;
- time to resolution;
- quote width;
- quote size;
- fill probability;
- adverse selection;
- rebates and liquidity rewards.

P&L must be decomposed into trading edge versus rewards/rebates.

For current V2 scope, market making should be **shadow/research mode only** unless separately promoted after validation.

Do not enable live market making simply because V2 exists.

## E. Cross-market combinatorial arbitrage

Future versions may model logical relationships between distinct markets and use SAT/SMT/LP/MILP techniques to discover portfolios that cannot lose under modeled terminal states.

An LLM may eventually help identify **candidate** market relationships, but must not be trusted to authorize trades.

Required future flow:

`LLM candidate relationship -> deterministic normalized relation -> formal validator/solver -> risk engine -> execution`

This is a later feature, not part of immediate V1 live scope.

## F. Strategies intentionally not prioritized

Do not treat the following as safe default strategies:

- martingale / doubling after losses;
- uncontrolled averaging down;
- near-resolution 98c/99c betting merely because an outcome looks certain;
- LLM-only probability predictions;
- sports/crypto latency racing as the initial business model;
- wash trading;
- self-trading schemes;
- spoofing;
- manipulative reward farming;
- geographic-restriction bypassing.

---

# 3. V1 AND V2 DEFINITIONS FOR THIS REPOSITORY

These labels must be documented exactly enough that future agents do not reinterpret them.

## V1 — Foundation + data + replay + paper/shadow structural strategies

V1 should include:

### Market discovery and metadata
- Polymarket event/market discovery.
- Token mapping.
- Market state/status.
- Resolution/NegRisk metadata required by supported strategies.
- Dynamic fee/reward parameter ingestion.

### Market data
- WebSocket-based order-book ingestion where appropriate.
- Snapshot/re-sync behavior.
- Local normalized L2 book.
- Trades and relevant updates.
- Source timestamps and local receipt timestamps.
- Sequence/update tracking where available.
- Staleness detection.

### Storage
- PostgreSQL for durable application state.
- Redis only if justified for ephemeral/shared state.
- Parquet export/archive for research and replay.
- Clean schemas for markets, tokens, proposals, risk decisions, orders, fills, positions, reconciliations, rewards, and P&L attribution.

### Strategy engines
- binary complete-set arbitrage scanner;
- vanilla NegRisk arbitrage scanner;
- Holding Rewards complete-set pilot/eligibility tracker.

### Risk
- independent deterministic risk engine;
- proposal/approval/rejection domain models;
- exposure limits;
- stale-data protection;
- depth and slippage checks;
- worst-case-payout checks;
- minimum-net-edge threshold;
- legging-risk controls.

### Simulation
- replay engine;
- paper trading;
- realistic execution assumptions;
- partial fills;
- latency assumptions;
- fee/rounding modeling;
- depth-aware sizing;
- failure/disconnect scenarios where practical.

### Accounting/observability
- strategy-specific P&L attribution;
- reward/rebate P&L separated from trading P&L;
- structured logs;
- metrics;
- audit events;
- health/readiness endpoints.

### V1 safety boundary
V1 must default to **no real-money order submission**.

A new clone with default configuration must not be able to submit a real order.

## V2 — Guarded micro-live execution + operational hardening

V2 can add:

- dedicated signing/wallet adapter;
- explicitly enabled live mode;
- small configurable capital limits;
- multi-leg execution state machine;
- partial-fill recovery/hedging policy;
- supported CLOB order types such as FOK/FAK/GTC/GTD/post-only where appropriate;
- heartbeat/cancel-on-failure mechanisms;
- cancel-all and global kill switches;
- split/merge/redeem adapters;
- supported NegRisk conversion adapters;
- order, balance, and position reconciliation;
- idempotency keys;
- crash recovery;
- durable execution audit trail;
- production deployment;
- alerting;
- deployment/rollback/incident runbooks;
- shadow market-making engine and metrics.

### V2 safety boundary

V2 live execution should initially apply only to already-validated low-directional-risk structural strategies and only under strict caps.

Market making remains shadow-mode until separately approved.

---

# 4. LATER ROADMAP

Document but do not prematurely implement:

### V3 candidate features
- live inventory-aware market making after shadow validation;
- broader combinatorial/cross-market solver;
- formal Boolean relationship graph;
- LLM-assisted candidate relationship discovery;
- richer research dashboard;
- strategy allocator;
- multi-wallet/multi-account capabilities if ever justified.

### Possible future infrastructure
- split low-latency execution path into Rust if profiling proves Python insufficient;
- ClickHouse for very large historical datasets;
- ECS or other managed deployment if operational value is clear;
- Kubernetes only when actual scale/organizational needs justify it.

Avoid speculative infrastructure.

---

# 5. TARGET ARCHITECTURE

Prefer a **modular monolith** for V1/V2.

Target conceptual flow:

```text
Polymarket APIs / Polygon
        |
        v
Discovery + Market Data Adapters
        |
        v
Normalized Market State / Order Books
        |
        +-----------------------------+
        |             |               |
        v             v               v
 Binary Arb       NegRisk Arb      Reward Pilot
        \             |               /
         \            |              /
          +---- OpportunityProposal -+
                       |
                       v
                Deterministic
                 Risk Engine
                 /        \
              Reject     Approve
                           |
                           v
                   Execution Engine
                           |
              +------------+------------+
              |                         |
             CLOB                   CTF/NegRisk
              |                         |
              +------------+------------+
                           |
                           v
                Accounting/Reconciliation
                           |
                           v
                 Metrics / Audit / P&L
```

Absolute rule:

**Strategies do not place orders.** They emit proposals.

**Only the risk engine can authorize execution.**

The execution engine must require a valid risk approval.

No agent, UI, strategy, LLM, cron job, or helper function may bypass this path.

---

# 6. PREFERRED TECH STACK

Use this unless existing repository code or a documented ADR provides a better reason.

## Application
- Python 3.12+
- asyncio
- httpx
- WebSockets
- Pydantic
- current official Polymarket client libraries where appropriate
- SQLAlchemy + async PostgreSQL driver or another clearly documented async persistence option
- PostgreSQL
- Redis only if justified
- Polars
- Parquet
- SciPy / OR-Tools / PuLP when optimization requires it
- FastAPI for control/health/admin endpoints if needed
- structured logging
- Prometheus-compatible metrics

## Engineering
- uv or another documented Python dependency manager
- pytest
- Hypothesis for invariants/property tests
- Ruff
- mypy or pyright
- Docker
- Docker Compose
- Terraform
- GitHub Actions

## Deployment
Initial development:
- local Docker Compose.

Initial production target:
- AWS `eu-west-2` if still appropriate for latency to Polymarket infrastructure, but do not treat region as a permanent invariant.
- Prefer simple EC2/container deployment first.
- PostgreSQL can become managed RDS when appropriate.
- S3 for archived Parquet/history.
- CloudWatch and/or Prometheus/Grafana for operations.
- secret management through appropriate AWS services.

Do not use Lambda for the core persistent trading loop.

Do not introduce EKS for V1/V2 unless a documented requirement emerges.

Cloud deployment must never be designed to bypass platform geographic restrictions.

---

# 7. RECOMMENDED APPLICATION STRUCTURE

Create a source layout similar to:

```text
src/polibot/
├── __init__.py
├── config/
├── domain/
├── discovery/
├── market_data/
├── orderbook/
├── strategies/
│   ├── binary_arb/
│   ├── negrisk/
│   ├── holding_rewards/
│   └── market_making/
├── optimizer/
├── risk/
├── execution/
├── wallet/
├── settlement/
├── accounting/
├── backtest/
├── storage/
├── monitoring/
└── api/
```

Also create:

```text
tests/
├── unit/
├── integration/
├── property/
└── fixtures/

infra/
├── terraform/
└── docker/

scripts/
config/
```

Do not create empty complexity just to match the tree. Every package should either have a clear role or be documented as scaffolded for a near-term milestone.

---

# 8. REQUIRED REPOSITORY KNOWLEDGE STRUCTURE

Create and populate:

```text
repo/
│
├── AGENTS.md
├── ARCHITECTURE.md
├── README.md
│
├── docs/
│   ├── PROJECT_STATUS.md
│   ├── ROADMAP.md
│   ├── technical-debt.md
│   │
│   ├── architecture/
│   │   ├── overview.md
│   │   ├── backend.md
│   │   ├── database.md
│   │   ├── infrastructure.md
│   │   ├── security.md
│   │   ├── execution.md
│   │   └── observability.md
│   │
│   ├── product/
│   │   ├── requirements.md
│   │   ├── business-rules.md
│   │   └── constraints.md
│   │
│   ├── strategies/
│   │   ├── overview.md
│   │   ├── binary-complete-set-arbitrage.md
│   │   ├── negrisk-arbitrage.md
│   │   ├── holding-rewards-pilot.md
│   │   └── market-making-shadow.md
│   │
│   ├── research/
│   │   └── feasibility-study.md
│   │
│   ├── decisions/
│   │   ├── ADR-001-modular-monolith.md
│   │   ├── ADR-002-postgresql.md
│   │   ├── ADR-003-deterministic-risk-gate.md
│   │   ├── ADR-004-default-paper-mode.md
│   │   └── README.md
│   │
│   ├── plans/
│   │   ├── active/
│   │   │   └── bootstrap-v1-v2.md
│   │   └── completed/
│   │
│   ├── runbooks/
│   │   ├── deployment.md
│   │   ├── rollback.md
│   │   └── incident-response.md
│   │
│   └── data/
│       ├── market-data.md
│       └── replay-and-backtesting.md
│
├── .github/
│   ├── instructions/
│   │   ├── backend.instructions.md
│   │   ├── frontend.instructions.md
│   │   └── infrastructure.instructions.md
│   │
│   └── workflows/
│       └── ci.yml
```

You may add files when they clearly improve maintainability, but do not remove the core structure above without a documented reason.

`AGENTS.md` must be a concise navigation and policy document, not an encyclopedia. Put detailed product and technical context in `docs/`.

---

# 9. CONTENT REQUIREMENTS FOR KEY DOCUMENTS

## AGENTS.md
It must tell future coding agents:

- project mission;
- V1/V2 boundaries;
- mandatory reading order;
- strategy -> proposal -> risk -> execution rule;
- default paper mode;
- fail-closed behavior;
- Decimal/fixed-point money rule;
- no hard-coded volatile fees/reward rates;
- no direct LLM execution authority;
- testing expectations;
- documentation update rules;
- definition of done.

## ARCHITECTURE.md
Create a concise architecture map with major modules, data flow, trust boundaries, external integrations, execution modes, persistence, observability, and links to deeper docs.

## README.md
Write for a developer joining the project. Include what Polibot is, what it is not, current V1/V2 status, setup, commands, execution modes, repository map, safety warning, and links to docs.

Do not market the bot as guaranteed income.

## PROJECT_STATUS.md
Include current milestone, completed, in progress, blocked/open questions, next 3-5 tasks, and last-updated date.

## ROADMAP.md
Use milestone gates, not vague feature lists.

Example gates:

V1.0:
- ingestion validated;
- replay validated;
- strategy scanners correct;
- risk rejection tests pass;
- paper accounting reconciles.

V1.1:
- sustained shadow run;
- opportunity statistics;
- zero unexplained accounting mismatches.

V2.0:
- live mode exists but disabled by default;
- wallet/signing isolated;
- micro-live structural execution tested;
- kill switches/reconciliation proven;
- runbooks validated.

V2.x:
- shadow market making;
- promote only if predefined validation thresholds pass.

## feasibility-study.md
Capture the project research context:

- structural arbitrage is feasible but simple opportunities can be short-lived and competitive;
- market making is technically feasible but carries inventory/adverse-selection risk;
- NegRisk is attractive when structure is formally valid;
- holding-reward complete-set concept is a pilot hypothesis requiring empirical confirmation;
- LLM directional betting is not the safe core;
- no strategy is guaranteed profitable.

Do not freeze current fee/reward percentages as timeless facts.

## Strategy docs
For every strategy include:

- objective;
- market prerequisites;
- mathematical model;
- inputs;
- opportunity detection;
- sizing;
- execution plan;
- risk checks;
- failure states;
- exit/settlement behavior;
- accounting;
- backtest requirements;
- shadow/live promotion criteria;
- human intervention requirements;
- known unknowns.

---

# 10. DOMAIN MODEL REQUIREMENTS

Design types before real exchange code.

At minimum consider domain models for:

- `Market`
- `Event`
- `OutcomeToken`
- `OrderBook`
- `BookLevel`
- `MarketSnapshot`
- `FeeModel`
- `RewardProgram`
- `OpportunityProposal`
- `PayoffProof`
- `RiskDecision`
- `RiskRejectionReason`
- `ExecutionPlan`
- `OrderIntent`
- `Order`
- `Fill`
- `Position`
- `BalanceSnapshot`
- `ReconciliationResult`
- `PnLComponent`
- `StrategyRun`
- `AuditEvent`

Use explicit identifiers.

Use timezone-aware UTC datetimes.

Use Decimal or fixed-point representations for financial values.

Do not leak raw exchange response dictionaries through the domain layer.

---

# 11. EXECUTION MODES

Define an explicit enum/configuration such as:

- `REPLAY`
- `PAPER`
- `SHADOW`
- `LIVE`

Rules:

### REPLAY
Historical data only. No external trading calls.

### PAPER
Current/live market data may be consumed but no real orders.

### SHADOW
Generate the exact decisions/orders that would have been made and record them, but do not submit.

### LIVE
May submit real actions only after all safety/configuration checks pass.

Default must be PAPER or safer.

`LIVE` must require deliberate configuration and validated credentials.

Never fall back from PAPER/SHADOW into LIVE because configuration is missing.

---

# 12. RISK ENGINE REQUIREMENTS

The risk engine is a first-class subsystem, not helper functions scattered through strategies.

Before approval, it should be able to evaluate:

- market active/tradable;
- metadata fresh enough;
- book fresh enough;
- fee/reward parameters known;
- sufficient depth;
- expected slippage;
- minimum order size;
- position/balance availability;
- per-order notional limit;
- per-market exposure;
- per-event exposure;
- per-strategy exposure;
- global exposure;
- unmatched-leg exposure;
- modeled worst-case payout;
- minimum net edge after buffer;
- current error/health state;
- reconciliation health;
- duplicate/idempotency checks.

A rejection must have machine-readable reasons.

Risk decisions must be auditable.

---

# 13. MULTI-LEG EXECUTION REQUIREMENTS

For structural arbitrage, model execution as a state machine.

Consider states such as:

- `PLANNED`
- `RISK_APPROVED`
- `SUBMITTING`
- `PARTIALLY_FILLED`
- `HEDGING`
- `COMPLETE`
- `CANCELLED`
- `FAILED`
- `RECONCILING`
- `MANUAL_REVIEW_REQUIRED`

Do not assume both legs fill atomically unless the protocol actually guarantees it.

Model first-leg fill, second-leg rejection, partial fill, stale opportunity, cancel failure, network timeout, unknown submission result, and restart/crash during execution.

Use idempotency/reconciliation to resolve ambiguous outcomes.

---

# 14. DATA COLLECTION REQUIREMENTS

The first valuable product is the recorder.

Collect enough data to reproduce decisions.

Where available, preserve:

- event/market IDs;
- condition IDs;
- token IDs;
- source timestamp;
- local receipt timestamp;
- sequence/update identifier;
- bids/asks and depth;
- trades;
- market state;
- fee parameters;
- reward eligibility/parameters;
- strategy observations;
- proposals;
- risk decisions;
- execution transitions;
- orders/fills;
- positions/balances;
- settlement/redeem/merge actions;
- reconciliation;
- P&L.

Provide a clean path for Parquet export and deterministic replay.

---

# 15. BACKTESTING REQUIREMENTS

Do not build a fake candle-level backtest for order-book strategies.

The simulator should eventually support:

- L2 depth;
- partial fills;
- latency assumptions;
- stale opportunities;
- price/quantity rounding;
- fees;
- slippage;
- legging risk;
- minimum order rules;
- maker queue assumptions where relevant;
- disconnect/API-failure scenarios where useful;
- split/merge/redeem mechanics;
- reward/rebate attribution.

Every backtest result should disclose assumptions.

Do not equate historical displayed price with guaranteed executable fill.

---

# 16. P&L ATTRIBUTION

Never report only one total P&L number.

Separate at minimum:

- structural-arbitrage trading P&L;
- spread-capture P&L;
- inventory/directional P&L;
- fees;
- slippage;
- maker rebates;
- liquidity rewards;
- holding rewards;
- operational/reconciliation adjustments.

This prevents a losing trading algorithm from appearing profitable solely because of a temporary incentive program.

---

# 17. SAFETY / SECURITY REQUIREMENTS

Never commit private keys, seed phrases, signing secrets, production credentials, or API secrets.

Create `.env.example` with safe fake values.

Signing/wallet components must be isolated behind interfaces.

Use a dedicated low-balance wallet for any future controlled live validation.

Never log secrets or sensitive headers.

Any critical inconsistency must fail closed.

Provide strategy kill switch, global live-trading kill switch, cancel-all capability when supported, stale-book protection, reconciliation alerts, and health/readiness checks.

Document platform geographic/access restrictions as a compliance constraint. Do not implement VPN/proxy/location workarounds intended to evade them.

Do not implement manipulative activity such as wash trading, spoofing, self-trading for rewards, or fake volume.

---

# 18. INITIAL CODING SCAFFOLD TO CREATE NOW

In this bootstrap task, create a safe but useful foundation.

At minimum:

1. Python package layout.
2. `pyproject.toml`.
3. Typed configuration with execution mode defaulting to PAPER.
4. Domain money/price/quantity primitives using Decimal or fixed-point.
5. Core proposal/risk-decision models.
6. Exchange adapter interfaces/protocols.
7. Strategy interface that can only emit proposals.
8. Risk-engine interface and a minimal implementation that rejects unsafe/incomplete proposals.
9. Execution interface that requires an approval object.
10. Structured logging setup.
11. Health endpoint or health service abstraction.
12. Database configuration/migration skeleton.
13. Dockerfile.
14. `docker-compose.yml` with application + PostgreSQL, and Redis only if currently needed.
15. `.env.example`.
16. CI workflow running lint, type-check, and tests.
17. Unit tests proving:
    - default mode is not LIVE;
    - financial values do not use float;
    - an execution request without risk approval is rejected;
    - stale/invalid/incomplete opportunities are rejected by risk;
    - the strategy boundary emits proposals rather than orders.
18. Documentation structure from this prompt.

It is acceptable for actual Polymarket adapters to begin as interfaces/stubs if current API details require separate implementation tasks.

Do not fake external integration behavior.

Do not submit real orders.

Do not deploy anything in this bootstrap task.

---

# 19. VERSION-SENSITIVE EXTERNAL INFORMATION

Polymarket APIs, SDKs, fees, rewards, eligibility, order semantics, limits, and infrastructure can change.

Therefore:

- Prefer current official documentation when external access is available.
- Record the date/source of version-sensitive research.
- Do not hard-code a number merely because it appeared in an old feasibility discussion.
- Encapsulate external behavior behind adapters.
- Make fee/reward logic configurable/dynamically discoverable where practical.
- Add explicit TODO/open questions where official behavior still needs verification.
- Do not invent undocumented endpoints or capabilities.

---

# 20. CODING QUALITY

Use type hints, small cohesive modules, explicit domain models, deterministic tests, dependency injection at I/O boundaries, clear naming, structured errors, and idempotent operations where execution is involved.

Avoid giant god classes, direct REST calls scattered across strategies, `dict[str, Any]` as permanent domain models, float money math, hidden global mutable state, direct signing inside strategy code, broad `except Exception` swallowing, implicit live-mode behavior, and premature microservices.

---

# 21. DOCUMENTATION / PLANNING WORKFLOW FOR FUTURE AGENTS

Create `AGENTS.md` so future Codex tasks are required to:

1. read project status and roadmap;
2. read relevant architecture/product docs;
3. inspect relevant ADRs;
4. read/create an active plan for non-trivial work;
5. make the smallest coherent implementation;
6. test;
7. update docs;
8. update project status;
9. move completed plans to `completed/`;
10. record technical debt honestly.

For architecture decisions, create ADRs.

For non-trivial features, create a plan before implementation.

Documentation must evolve in the same change as behavior.

---

# 22. GITHUB INSTRUCTIONS

Populate `.github/instructions/backend.instructions.md` with Python architecture, async I/O boundaries, domain purity, Decimal money, testing, persistence, and the no-direct-strategy-execution rule.

Populate `.github/instructions/infrastructure.instructions.md` with Terraform, least privilege, secrets, safe defaults, no production deployment from unreviewed changes, configurable AWS region, no EKS without ADR, state separation, and rollback requirements.

Populate `.github/instructions/frontend.instructions.md` with future principles only: read-only/operational UI by default, no client-side private keys, no hidden execution bypass, dangerous actions require clear operator intent, and data freshness/execution mode must be prominently displayed.

---

# 23. CI EXPECTATIONS

Create a minimal CI workflow for PRs/pushes that runs:

- dependency install;
- Ruff;
- type checking;
- pytest;
- config validation if present.

Do not include live credentials.

Do not make CI capable of placing real trades.

Later deployment workflows must be separate from validation workflows.

---

# 24. ACCEPTANCE CRITERIA FOR THIS BOOTSTRAP TASK

Before finishing, verify:

- repository tree is coherent;
- `AGENTS.md` exists and is concise enough to act as a map/policy file;
- detailed context lives in docs;
- V1 and V2 are unambiguous;
- default execution mode is safe;
- no real-trading implementation is accidentally active;
- risk gate cannot be bypassed by the initial interfaces;
- money types avoid floats;
- documentation covers all strategies and their current status;
- README gives a new developer a clear starting point;
- project status and roadmap are populated;
- active bootstrap plan exists;
- ADRs capture major initial architecture choices;
- CI exists;
- tests exist and pass;
- lint/type checks pass;
- no secrets exist in the repository.

If a check cannot run, explain exactly why.

---

# 25. FINAL RESPONSE FORMAT

When finished, report:

1. What you created.
2. The final top-level repository tree.
3. Important architectural decisions.
4. Safety invariants established.
5. Tests/checks run and exact results.
6. Any unresolved Polymarket API questions that require current official-doc verification.
7. The next 3 recommended implementation tasks for V1.

Do not claim the bot is profitable.

Do not claim a strategy is risk-free.

Do not place any real trade.

Start by inspecting the repository and then execute this bootstrap task.
