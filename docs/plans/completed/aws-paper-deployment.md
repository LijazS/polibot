# AWS paper deployment through GitHub Actions

Status: completed  
Started: 2026-09-05  
Completed: 2026-09-05

## Objective

Build and exercise a reproducible, manually gated deployment path for PAPER mode using
GitHub OIDC, Terraform, ECR, a dedicated low-cost VPC/EC2 host, local PostgreSQL,
private S3 artifacts/data, CloudWatch, and Systems Manager.

## Identity and deployed result

- AWS account/region: `484632959006` / `us-east-1`
- GitHub repository: `LijazS/polibot`; environment: `paper`; branch: `main`
- Immutable OIDC subject: `repo:LijazS@180333961/polibot@1357427608:environment:paper`
- Successful workflow: `33963697738`
- Instance: `i-0a24009387e20f235`; private IP: `10.40.1.21`
- Commit: `a3545a2638481dc0a66f6b0f71f414fa81910122`
- Image digest: `sha256:ec398861bf5264863af51dfd9e3a7266cc45ec261839dfec83f2af1ea7d26cdd`

## Delivered work

1. Replaced the generic RDS/existing-VPC scaffold with a dedicated PAPER environment.
2. Added no-ingress EC2/SSM, local PostgreSQL, immutable ECR, private S3, monitoring,
   remote locked state, and scoped roles.
3. Added digest deployment, migrations, fail-closed mode health, rollback, and an
   independent secret-safe SSM verification document.
4. Added a manually dispatched GitHub OIDC workflow protected by repository identity,
   environment reviewer, `main` branch policy, account checks, and separate roles.
5. Created and verified the state bucket, roles, environment, and seven non-secret
   variables; no GitHub environment secrets were added.

## Observed verification

- Local and GitHub checks passed: 96 tests, Ruff, format, mypy, Alembic SQL, docs,
  Terraform, Compose, and Docker build.
- Terraform final plan: no changes.
- Security group ingress count: zero; no EC2 key; IMDSv2 required.
- ECR: immutable and AES256 encrypted.
- SSM: online; CloudWatch bootstrap/deployment streams present; status alarm OK.
- `/health`: healthy, execution mode `paper`, `live_trading_enabled=false`.
- App and PostgreSQL containers: running and healthy; app bound to `127.0.0.1` only;
  PostgreSQL has no published port.
- Generated runtime files: root-owned mode `0600`; values were not printed.

## Follow-up gates

Exercise rollback, implement and test PostgreSQL backup/restore, add cost/budget
alerting, and collect sustained PAPER runtime evidence. LIVE remains hard-disabled and
no signer, wallet secret, or authenticated trading transport was deployed.
