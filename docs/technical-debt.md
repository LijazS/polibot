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
- The AWS PAPER stack, OIDC workflow, immutable image pipeline, SSM deploy, alarm, and
  health verification are deployed. Rollback, host replacement, sustained operation,
  budget alerting, and database backup/restore still need operator exercises.
- The first PAPER teardown completed after exposing and correcting a stateful
  `force_destroy`/`force_delete` sequencing issue. Re-creation in `eu-west-2` is the
  active infrastructure gate.
- The selected `eu-west-2` placement is only for PAPER public-data collection. Measure
  actual endpoint latency after deployment; never treat ordinary AWS placement as
  direct co-location approval or a geoblock workaround.
- No multi-day dataset exists. Rewards, opportunity frequency, fills, profitability,
  drawdown, reconciliation stability, and shadow-maker results are `PENDING_DATA`.
## AWS PAPER persistence

The low-cost PAPER design keeps PostgreSQL on the EC2 root volume. Terraform host
replacement therefore destroys the database volume. Add an encrypted, tested backup
and restore path before treating the environment as durable or storing irreplaceable
research data. Application rollback also assumes forward migrations remain compatible
with the previous image.
