# V1 continuous PAPER worker

Status: Active  
Started: 2026-09-05

## Goal

Run a separately restartable, continuous worker on the existing PAPER host. It consumes
only public Polymarket data, maintains fail-closed books, records reproducible inputs,
evaluates the existing binary strategy through deterministic risk, and simulates all
execution. No authenticated trading or chain-write adapter is in scope.

## Safety invariants

- Startup rejects LIVE mode and any enabled live-trading flag.
- Strategies receive only validated, current books and produce proposals only.
- Missing or stale metadata, fees, books, recorder health, or WebSocket connectivity
  prevents approvals.
- Recorder queues are bounded; backpressure degrades readiness and is visible.
- The worker image contains no signer, private key, authenticated order client, or
  transaction broadcaster.
- API and worker remain reachable only on the host/internal Compose networks.

## Work

1. Add validated worker configuration and current public API metadata adapters.
2. Add worker-run, heartbeat, and market-selection persistence with a migration.
3. Add a bounded batch recorder and continuous discovery/snapshot/WebSocket worker.
4. Connect normalized books to binary proposals, deterministic risk, realistic paper
   depth simulation, separated counters, and durable evidence.
5. Add internal status/readiness and read-only CLI reporting.
6. Deploy API and worker from the same immutable image and strengthen verification.
7. Add offline tests plus an optional public-data smoke test; update operations/docs.

## Exit checks

- Ruff, formatting, mypy, pytest, migration SQL, docs, Docker build/Compose, Terraform.
- Short public-data worker smoke test if network conditions permit.
- GitHub Actions deployment and SSM/status/database counter verification if access is
  available. Empirical strategy validation remains `PENDING_DATA`.
