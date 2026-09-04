# Polibot

Polibot is a capital-preservation-first platform for researching, replaying, and
paper/shadow testing structurally verifiable Polymarket strategies. It is not a
guaranteed-income product, an outcome-prediction agent, or a default-live bot.

The current bootstrap provides typed domain models, strict decimal financial
values, an independent deterministic risk gate, a simulated executor, health and
logging foundations, PostgreSQL configuration, tests, and project documentation.
It does not contain a Polymarket adapter, signer, wallet, or real-order path.

## Safety boundary

The required flow is:

`market data -> strategy -> OpportunityProposal -> risk -> execution`

Strategies cannot place orders. The executor requires a matching, unexpired risk
approval. The bootstrap executor refuses `LIVE` mode. Configuration defaults to
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

The health endpoint is `GET /health`. Redis is intentionally not included because
the bootstrap has no justified use for it.

## Execution modes

- `replay`: historical inputs only; no external trading calls.
- `paper`: current data may be used; orders are simulated. This is the default.
- `shadow`: records exact intended decisions without submitting them.
- `live`: reserved for guarded V2; unsupported by the bootstrap executor.

## Repository map

- `src/polibot/domain`: stable typed financial and trading models.
- `src/polibot/risk`: deterministic approval/rejection boundary.
- `src/polibot/execution`: approval-enforcing simulated execution.
- `src/polibot/market_data`: read-only adapter contracts.
- `src/polibot/strategies`: proposal-only strategy contracts and scoped packages.
- `docs`: product, architecture, strategy, data, decisions, plans, and runbooks.
- `tests`: safety-focused unit tests plus integration/property placeholders.
- `infra`: explicitly deferred container/Terraform evolution.

Start with [PROJECT_STATUS](docs/PROJECT_STATUS.md), [ROADMAP](docs/ROADMAP.md), and
[ARCHITECTURE](ARCHITECTURE.md). External APIs, fees, rewards, eligibility, limits,
and order semantics must be verified against current official sources before their
implementation. Never put real secrets in `.env.example` or source control.

