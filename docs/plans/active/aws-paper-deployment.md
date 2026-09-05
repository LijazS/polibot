# AWS paper deployment through GitHub Actions

Status: active  
Started: 2026-09-05

## Objective

Build a reproducible, manually gated deployment path for PAPER mode using GitHub
OIDC, Terraform, ECR, a dedicated low-cost VPC/EC2 host, local PostgreSQL, private
S3 artifacts/data, CloudWatch, and Systems Manager. Stop before manual bootstrap
or any AWS/GitHub mutation.

## Discovered deployment identity

- AWS account: `484632959006`
- AWS region: `us-east-1` from the working `browser-login` profile
- GitHub repository: `LijazS/polibot` (`main`, public)
- Repository numeric ID: `1357427608`; owner numeric ID: `180333961`
- Environment OIDC subject: `repo:LijazS@180333961/polibot@1357427608:environment:paper`
- Existing GitHub OIDC provider has audience `sts.amazonaws.com`; deployment roles
  and Polibot resources do not yet exist.

## Work

1. Replace the generic RDS/existing-VPC scaffold with a dedicated paper environment.
2. Add ECR, private S3 data/artifacts, SSM-only EC2, local PostgreSQL, monitoring,
   least-privilege instance permissions, and remote S3 state configuration.
3. Add immutable deployment bundle, health/mode verification, and rollback scripts.
4. Add a manually dispatched, protected GitHub Actions OIDC workflow with wrong-account checks.
5. Add exact state/OIDC/role/environment/variable bootstrap artifacts and runbook.
6. Validate locally, update architecture/runbooks/status, then stop at the manual gate.

## Current gate

Implementation and available local static validation are complete; Docker validation
remains mandatory in CI because Docker is unavailable on this workstation. The state
bucket, OIDC roles, and protected GitHub environment/variables were created and verified
after explicit operator authorization. The plan remains active until workflow plan/apply,
deployment, and post-deploy verification are observed.

## Safety invariants

- No AWS or GitHub mutation occurs during implementation/discovery.
- No static AWS keys, SSH, inbound application port, or public database.
- Instance bootstrap contains no runtime secret; PostgreSQL credentials are generated
  once on-host into root-only files.
- Images deploy by captured ECR digest from the exact Git commit.
- PAPER and `LIVE_TRADING_ENABLED=false` are checked before and after deployment.
- No production Polymarket signer or authenticated trading credential is deployed.
