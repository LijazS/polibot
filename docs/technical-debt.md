# Technical debt and deliberate deferrals

- PostgreSQL mappings, migrations, recorder, and execution-transition journal exist
  but have not run against a PostgreSQL service in this environment.
- The continuous runtime orchestrates one proposal path; production-grade subscription
  scheduling, backpressure, durable consumer offsets, and database/stream health probes
  need a sustained public-data test.
- Public Gamma/CLOB smoke validation timed out locally. All network integration is
  official-schema fixture/mock tested, not `TESTED_AGAINST_PUBLIC_API`.
- Paper fills model taker depth, injected failures, and partial fills, but execution
  latency, tick/quantity rounding, queue position, adverse selection, and opportunity
  lifetime need calibration from recorded data.
- The V2 exchange and settlement layers intentionally contain only fakes. Exact
  NegRisk conversion encoding remains unsupported; authenticated account/user stream,
  production signing, and broadcasting are outside the approved boundary.
- The PostgreSQL execution journal is append/load capable, but full restart hydration
  and transactional persistence of proposal, approval, transition, and exposure in
  one unit of work require service-backed design and tests before live consideration.
- Terraform needs a reviewed backend, VPC endpoints/NAT policy, immutable image
  pipeline, alarms, restore exercise, deployment controls, and security review. It was
  validated but never planned or applied.
- No multi-day dataset exists. Rewards, opportunity frequency, fills, profitability,
  drawdown, reconciliation stability, and shadow-maker results are `PENDING_DATA`.
