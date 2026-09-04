# AGENTS.md — Polibot

## Mission

Polibot is a capital-preservation-first automated research and trading platform for Polymarket.

The project is intended to discover, simulate, validate, and eventually execute low-directional-risk strategies such as structural arbitrage. It is **not** designed around discretionary gambling, martingale systems, high-leverage speculation, or an LLM guessing event outcomes.

Primary engineering priorities, in order:

1. Correctness
2. Capital safety
3. Deterministic risk controls
4. Auditability and reconciliation
5. Observability
6. Testability
7. Execution quality
8. Profitability
9. Latency optimization

There is no assumption or guarantee of profitability. Treat every strategy as unproven until supported by reproducible data, realistic simulation, shadow operation, and controlled live validation.

## Read before changing code

Before implementing a task, read:

1. `AGENTS.md`
2. `docs/PROJECT_STATUS.md`
3. `docs/ROADMAP.md`
4. `ARCHITECTURE.md`
5. `docs/product/requirements.md`
6. `docs/product/business-rules.md`
7. `docs/product/constraints.md`
8. Relevant files under `docs/architecture/`
9. Relevant ADRs under `docs/decisions/`
10. Relevant strategy/design documentation
11. Any active plan under `docs/plans/active/`

For work spanning multiple modules or changing architecture, create or update an active implementation plan before coding.

Repository documentation is part of the product. Do not allow code and documentation to knowingly diverge.

## Current product scope

### V1 — Foundation + paper/shadow structural strategies

V1 must establish:

- Polymarket market discovery and metadata ingestion.
- CLOB order-book ingestion using WebSockets where appropriate.
- Market/user event handling behind explicit adapters.
- A local normalized order-book representation.
- Raw and normalized market-data recording.
- Historical replay/backtesting infrastructure.
- Dynamic retrieval/modeling of fees, rewards, market status, token IDs, event metadata, and other version-sensitive parameters.
- Binary YES+NO complete-set arbitrage scanner.
- Vanilla NegRisk / mutually-exclusive-outcome arbitrage scanner.
- Complete-set Holding Rewards validation/pilot tooling.
- Deterministic opportunity evaluation.
- Independent deterministic risk engine.
- Paper-trading/shadow execution.
- Accounting and P&L attribution.
- PostgreSQL persistence.
- Redis only where it provides clear operational value.
- Parquet-based historical data export/archive.
- Metrics, structured logs, health checks, and audit records.

V1 must default to **no real-money order submission**.

### V2 — Guarded execution + production hardening

V2 may add, only after V1 validation:

- Dedicated signer/wallet adapter.
- Guarded live execution for already-validated structural strategies.
- Small-capital/capped execution mode.
- Multi-leg execution state machine.
- Partial-fill and legging-risk handling.
- FOK/FAK/GTC/GTD/post-only behavior where supported and appropriate.
- Heartbeat/cancel-on-failure handling.
- Cancel-all / strategy kill switches.
- CTF split/merge/redeem operations behind explicit adapters.
- NegRisk conversion operations behind explicit adapters.
- Continuous balance/position/order reconciliation.
- Durable idempotency and crash recovery.
- AWS deployment and operational runbooks.
- Production monitoring and alerting.
- Shadow-mode inventory-aware market-making research.

Live market making is **not automatically included in V2 live execution**. It must remain shadow-mode until its own validation criteria are satisfied.

### Later / explicitly out of current scope

Do not implement these unless a task explicitly promotes them:

- Live inventory-carrying market making.
- Broad cross-event combinatorial arbitrage.
- LLM-driven market relationship discovery.
- LLM-based probability prediction.
- Sports or crypto latency racing.
- Multi-account orchestration.
- Kubernetes/EKS unless operational scale proves it necessary.
- Direct autonomous capital allocation by an AI agent.

## Core trading architecture rule

Strategies never place orders directly.

Required flow:

`Market Data -> Strategy -> OpportunityProposal -> Risk Engine -> Execution Engine -> Exchange/Chain`

A strategy may only produce an `OpportunityProposal`.

The risk engine is the sole gatekeeper that may authorize execution.

The execution engine must reject any proposal without a valid risk approval.

No LLM, agent, UI action, strategy module, or background worker may bypass the risk engine.

## Capital-safety invariants

### Default-safe operation

- Default execution mode is `replay`, `paper`, or `shadow`.
- Live trading must require explicit configuration.
- Absence, corruption, or ambiguity of a live-trading setting means live trading is disabled.
- A fresh checkout must never be capable of sending a real order without deliberate operator configuration.
- Development/test commands must never silently use production credentials.

### Fail closed

When critical state is missing or inconsistent:

- Do not open new exposure.
- Disable the affected strategy or execution path.
- Cancel outstanding orders when doing so is safe and supported.
- Emit a high-severity audit event.

Examples include stale books, unknown fee configuration, invalid market metadata, unknown token mapping, reconciliation mismatch, signer failure, persistent API errors, sequence gaps, risk-engine outage, and corrupted position state.

### Monetary correctness

- Never use binary floating-point for money, prices, quantities, fees, P&L, or collateral accounting.
- Use `Decimal` with explicit quantization or integer fixed-point representations.
- Rounding policy must be explicit and tested.
- Fee calculations must be version-aware and not copied as permanent constants from old documentation.

### Structural-arbitrage correctness

Never treat `YES ask + NO ask < 1` alone as sufficient proof of executable profit.

Opportunity evaluation must account for, as applicable:

- actual executable depth;
- fees;
- rounding;
- expected slippage;
- partial fills;
- multi-leg latency;
- minimum order sizes;
- token conversion costs;
- current market status;
- resolution/NegRisk structure;
- safety buffer;
- worst-case payout across valid terminal states.

A structural arbitrage proposal must have an explicit payoff proof or equivalent invariant showing the modeled worst-case terminal payout.

### Exposure controls

Support configurable limits for at least:

- global capital at risk;
- strategy exposure;
- market/event exposure;
- per-order notional;
- unmatched multi-leg exposure;
- maximum time an unmatched leg may remain open;
- maximum slippage;
- minimum net expected edge;
- stale-data threshold;
- maximum consecutive execution errors;
- daily realized loss / drawdown guard where applicable.

Risk limits belong in configuration with safe defaults and validation.

## Strategy rules

### Binary complete-set arbitrage

Model executable acquisition/creation of complementary outcomes and compare total all-in cost against deterministic terminal/merge value.

Requirements: depth-aware sizing, fee-aware economics, legging-risk handling, minimum net-edge buffer, explicit partial-fill behavior, and merge/redeem accounting where applicable.

### Vanilla NegRisk arbitrage

Only operate on events whose mutually-exclusive structure has been validated by machine-readable metadata and the supported NegRisk model.

Requirements:

- do not infer exclusivity from names alone;
- explicitly model all valid terminal states;
- exclude ambiguous/augmented structures until supported;
- account for “Other”/placeholder outcomes conservatively;
- prove worst-case payout before approval.

### Holding Rewards complete-set pilot

Treat this as an experiment until live behavior is empirically validated.

Requirements:

- dynamically discover eligibility and reward parameters;
- never assume a historical reward rate remains current;
- distinguish reward P&L from trading P&L;
- record observations needed to reconcile expected vs actual rewards;
- do not scale capital merely because a complete set is directionally neutral.

### Market making

For current V2, market making is research/shadow-mode only unless explicitly promoted.

Model spread capture, inventory skew, volatility, adverse selection, rebates/rewards, event/news risk, and time to resolution.

Never claim “spread = profit.” Report trading P&L separately from reward/rebate income.

## AI / agent boundary

AI may assist with coding, documentation, research summaries, strategy ideation, candidate relationship discovery, debugging, and test generation.

AI must not be trusted as the final authority for order authorization, private-key use, wallet signing policy, position sizing, bypassing deterministic risk rules, or declaring an arbitrage mathematically safe without deterministic verification.

Future LLM-based relationship discovery must follow:

`LLM candidate -> deterministic parser/model -> formal validation -> risk engine -> execution`

## Rejected default strategy patterns

Do not add these as “safe strategies” without an explicit project decision:

- martingale or loss-doubling;
- uncontrolled averaging down;
- wash trading;
- self-trading schemes;
- spoofing or manipulative liquidity;
- reward farming through fake volume;
- geographic restriction bypassing;
- near-resolution “99-cent” trades justified only by apparent certainty;
- LLM-only directional betting;
- unbounded latency racing.

Follow Polymarket market-integrity rules and applicable legal/access restrictions.

Cloud location is an engineering decision, not a mechanism to evade platform restrictions.

## Preferred technical stack

Unless an ADR changes it:

- Python 3.12+
- `asyncio`
- official/current Polymarket client libraries where appropriate
- `httpx`
- WebSockets
- Pydantic
- SQLAlchemy + async PostgreSQL driver, or another documented async persistence choice
- PostgreSQL
- Redis only for justified ephemeral/shared state
- Polars / Parquet for research data
- SciPy / OR-Tools / PuLP as justified for optimization
- FastAPI for control/health/admin APIs if required
- pytest
- Hypothesis for invariant/property tests where valuable
- Ruff
- mypy or pyright
- structured logging
- Prometheus-compatible metrics
- Docker / Docker Compose
- Terraform for cloud infrastructure
- GitHub Actions for CI/CD

Prefer a modular monolith for V1/V2.

Do not introduce microservices, Kafka, Kubernetes, or distributed complexity without evidence that the current architecture cannot meet requirements.

## Target module boundaries

Prefer clear modules resembling:

```text
src/polibot/
  config/
  domain/
  discovery/
  market_data/
  orderbook/
  strategies/
    binary_arb/
    negrisk/
    holding_rewards/
    market_making/
  optimizer/
  risk/
  execution/
  wallet/
  settlement/
  accounting/
  backtest/
  storage/
  monitoring/
  api/
```

Dependency direction should flow toward stable domain interfaces.

Exchange/network/blockchain specifics belong behind adapters.

Domain logic should be testable without network access.

## Data and replay requirements

The project should be able to reconstruct why a decision was made.

Record enough data to reproduce market metadata, token mappings, book snapshots/deltas, timestamps, trades, fee/reward parameters, opportunity proposals, risk decisions, orders/fills, positions/balances, settlements, reconciliations, and P&L components.

Backtests must model execution rather than assume all displayed prices were freely available. Include depth, partial fills, latency assumptions, fee/rounding effects, stale data, slippage, legging risk, queue assumptions for maker strategies, and relevant failures/disconnects.

## P&L and metrics

Always separate:

- structural-arbitrage P&L;
- spread-capture P&L;
- directional/inventory P&L;
- fees;
- slippage;
- maker rebates;
- liquidity rewards;
- holding rewards;
- operational/reconciliation adjustments.

Key safety metrics include net P&L, maximum drawdown, modeled worst-case payout, unmatched-leg exposure/duration, fill rate, slippage, adverse price movement, inventory exposure, capital utilization, stale-book events, API/execution errors, and reconciliation mismatches.

## Secrets and security

Never commit private keys, seed phrases, API/signing secrets, production database credentials, or cloud credentials.

Use environment variables or approved secret stores. Provide `.env.example` with fake values only. Do not log secrets. Redact credentials and sensitive headers from exceptions.

Use a dedicated low-balance trading wallet for controlled live validation.

Signing code requires focused tests and explicit review.

## Documentation rules

The repository docs are the durable system of record.

When behavior or architecture changes, update the relevant documentation in the same change.

Use ADRs for meaningful, durable architectural decisions.

Use `docs/plans/active/` for non-trivial implementation work.

On completion:

- update `docs/PROJECT_STATUS.md`;
- update `docs/ROADMAP.md` when milestone status changes;
- move completed plans to `docs/plans/completed/`;
- record knowingly deferred issues in `docs/technical-debt.md`.

Do not place volatile external facts such as current reward percentages into architectural invariants. Mark them as dynamically discovered or date-stamped observations.

## Engineering workflow

Before coding:

1. Inspect existing code and documentation.
2. Check `docs/PROJECT_STATUS.md`.
3. Check active plans.
4. Identify affected safety invariants.
5. Prefer the smallest coherent change.

During coding:

- keep domain logic deterministic;
- keep I/O behind interfaces;
- write tests with implementation;
- preserve backwards compatibility unless a plan explicitly changes it;
- avoid speculative abstractions.

After coding, run the repository-standard equivalents of:

```bash
ruff check .
mypy src
pytest
```

Also run applicable formatting, type, migration, Docker, and infrastructure validation commands documented by the repo.

Do not claim success if tests were not run. State exactly what was and was not validated.

## Definition of done

A change is done only when:

- implementation is complete;
- relevant unit/integration/property tests exist;
- risk/safety behavior is covered where applicable;
- lint/type/test checks pass or failures are clearly documented;
- documentation matches behavior;
- configuration examples are updated;
- no secrets are introduced;
- failure behavior is defined;
- observability is sufficient to diagnose the change;
- `PROJECT_STATUS.md` reflects the new state for milestone-level work.

For trading/execution changes, additionally require paper/shadow coverage, deterministic risk rejection tests, partial-failure tests, idempotency/recovery tests where relevant, and no default path to live trading.

## Guiding principle

When uncertain between a more profitable implementation and a safer, simpler, auditable implementation, choose the safer implementation and document the trade-off.

For Polibot, **doing nothing is a valid and often correct trading decision**.
