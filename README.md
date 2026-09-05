# Polibot

Polibot is a capital-preservation-first platform for researching, replaying, and
paper/shadow testing structurally verifiable Polymarket strategies. It is not a
guaranteed-income product, an outcome-prediction agent, or a default-live bot.

The current implementation provides public-data adapters, normalized fail-closed L2
books, recording/replay, depth-aware binary and vanilla NegRisk proposal scanners,
reward observations, deterministic risk, paper/shadow simulation, accounting,
metrics, a non-live V2 state machine, reconciliation/recovery controls, fake-only
wallet/exchange/settlement boundaries, and shadow market-making research.

## Safety boundary

The required flow is:

`market data -> strategy -> OpportunityProposal -> risk -> execution`

Strategies cannot place orders. The executor requires a matching, unexpired risk
approval. Every executor refuses `LIVE` mode. Configuration defaults to
`paper`, and ambiguous or missing critical information must fail closed.

## Developer setup

Python 3.12 or newer is required.

```bash
python -m venv .venv
# Activate the environment for your shell.
python -m pip install -e ".[dev]"
ruff check .
mypy src
pytest
uvicorn polibot.api.app:app --reload
```

For the local API and PostgreSQL:

```bash
docker compose up --build
```

Apply migrations before starting the local API and worker:

```bash
docker compose up -d postgres
docker compose run --rm app alembic upgrade head
docker compose up -d app worker
```

The internal endpoints are `GET /health`, `GET /ready`, `GET /status`, and
`GET /metrics`. `polibot status`, `polibot markets`, `polibot opportunities`,
`polibot paper-pnl`, `polibot worker-runs`, `polibot books --stale`, and
`polibot report daily` are read-only operational commands. Redis is intentionally
absent because the worker uses bounded in-process queues and PostgreSQL durability.

## Execution modes

- `replay`: historical inputs only; no external trading calls.
- `paper`: current data may be used; orders are simulated. This is the default.
- `shadow`: records exact intended decisions without submitting them.
- `live`: represented for future design but hard-disabled by every current executor.

## Repository map

- `src/polibot/domain`: stable typed financial and trading models.
- `src/polibot/risk`: deterministic approval/rejection boundary.
- `src/polibot/execution`: approval-enforcing simulation, state machine, safety controls,
  fake exchange boundary, and PostgreSQL transition journal.
- `src/polibot/market_data`: read-only adapter contracts.
- `src/polibot/strategies`: proposal-only strategy contracts and scoped packages.
- `docs`: product, architecture, strategy, data, decisions, plans, and runbooks.
- `tests`: safety-focused unit, integration, and property tests.
- `infra`: Docker assets and a statically validated, non-live AWS Terraform scaffold.

Start with [PROJECT_STATUS](docs/PROJECT_STATUS.md), [ROADMAP](docs/ROADMAP.md), and
[ARCHITECTURE](ARCHITECTURE.md). External APIs, fees, rewards, eligibility, limits,
and order semantics must be verified against current official sources before their
implementation. Never put real secrets in `.env.example` or source control.
