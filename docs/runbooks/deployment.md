# PAPER deployment runbook

The only authorized cloud workflow is `.github/workflows/deploy-paper.yml`, manually
dispatched from `main` after the `paper` environment approval. Complete and verify the
one-time bootstrap runbook first.

Full-stack removal uses only `.github/workflows/destroy-paper.yml`; follow
`docs/runbooks/destruction.md`. Never dispatch it as a rollback mechanism.

The workflow validates tests, formatting, types, migrations, container build, Compose,
shell scripts, documentation, and Terraform. It then assumes the infrastructure role,
plans and applies the PAPER stack, assumes the deployment role, builds the exact Git
commit, pushes an immutable ECR tag, resolves its digest, uploads a SHA-specific bundle,
and deploys through SSM. Concurrent deployments are serialized.

On-host deployment creates a random PostgreSQL password only if root-only runtime files
do not exist, pulls by digest, starts PostgreSQL, applies forward migrations, starts the
app, and verifies `/health` reports `paper` and `live_trading_enabled=false`. A failed
health check attempts application-image rollback. It never deploys a signer, private
Polymarket key, or authenticated trading transport.

After a successful run, inspect the workflow summary and CloudWatch log group
`/polibot/paper/host`. Use SSM rather than SSH for diagnostics. Treat any mode mismatch,
failed migration, unavailable SSM host, reconciliation fault, or unexplained restart as
a failed deployment; do not weaken the checks.

## First deployment evidence

Workflow run `33963697738` deployed commit
`a3545a2638481dc0a66f6b0f71f414fa81910122` to instance
`i-0a24009387e20f235` as ECR digest
`sha256:ec398861bf5264863af51dfd9e3a7266cc45ec261839dfec83f2af1ea7d26cdd`.
Independent SSM verification confirmed both containers healthy, loopback-only app
publishing, no PostgreSQL port, PAPER mode, live disabled, and root-owned `0600`
runtime files. A post-deploy Terraform plan reported no changes.

## eu-west-2 migration evidence

Destroy workflow run `33964747292` removed the original `us-east-1` stack and left
empty remote state while preserving the bootstrap backend and OIDC roles. Deployment
workflow run `33976145081` deployed commit
`fec85ecd23b9b1db3ab260e4a4dbd1bc3f045830` in `eu-west-2` to instance
`i-03d8810150224343d` as ECR digest
`sha256:5ceed0cbb63ef41c0abb4b0bb0520a273609c7a6dbd5cdf6d8fc1005d021728a`.

Independent checks confirmed the documented network isolation, IMDSv2, immutable
image identity, healthy containers and API, PAPER/live-disable flags, root-only secret
files, secured S3/ECR, alarm recovery to `OK`, and a refreshed no-change Terraform
plan. The host geoblock response was `GB/ENG blocked=true`; this environment remains
public-data PAPER only and must not submit orders.
