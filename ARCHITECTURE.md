# Architecture

Polibot is a Python 3.12 modular monolith. Stable domain types sit at the center;
network, persistence, exchange, chain, and time concerns remain behind adapters.

```text
Discovery/market-data adapters -> normalized snapshots -> proposal-only strategies
    -> deterministic risk engine -> approval-required execution
    -> accounting/reconciliation -> audit, metrics, health, and durable storage
```

## Trust boundaries

- External API and chain data are untrusted until normalized and validated.
- Strategy output is an untrusted proposal, never authorization.
- Only deterministic risk evaluation creates a short-lived approval.
- Execution verifies approval identity and expiry before acting.
- Wallet/signing is absent in V1 bootstrap and isolated when introduced in V2.
- UI, agents, schedulers, and operators cannot bypass risk.

## Modes and persistence

Replay, paper, and shadow never submit real orders. Live mode is a separately
enabled V2 capability and is unsupported by the bootstrap executor. PostgreSQL is
the intended durable store; Parquet is the intended research/replay archive. Redis
is excluded until a concrete shared ephemeral-state requirement exists.

## Module map

Domain and configuration are dependency roots. Discovery, market data, normalized
books, strategies, risk, execution, settlement, accounting, storage, monitoring,
and API are cohesive modules. A single process may host them initially; splitting
services requires evidence and an ADR.

See [overview](docs/architecture/overview.md),
[backend](docs/architecture/backend.md), [database](docs/architecture/database.md),
[execution](docs/architecture/execution.md), [security](docs/architecture/security.md),
[observability](docs/architecture/observability.md), and
[infrastructure](docs/architecture/infrastructure.md).

