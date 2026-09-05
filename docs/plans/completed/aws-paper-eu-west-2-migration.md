# AWS PAPER eu-west-2 migration

Status: Completed
Date: 2026-09-05

## Objective

Move the destroyed PAPER stack from `us-east-1` to `eu-west-2`, retain the existing
remote Terraform backend in `us-east-1`, correct the destroy workflow's non-empty
S3/ECR handling, redeploy through GitHub OIDC, and independently verify safe PAPER
operation.

## Safety boundaries

- Keep execution mode PAPER and LIVE hard-disabled.
- Introduce no Polymarket credentials, wallet signer, inbound access, or static AWS key.
- Treat `eu-west-2` as a public-data PAPER location only. It does not grant direct
  co-location or permission to submit orders, and must not be used to evade geoblocks.
- Preserve the encrypted/versioned Terraform state bucket in `us-east-1`.
- Restrict regional IAM resources to `eu-west-2` after confirming the old stack is gone.
- Keep destruction manual, exact-confirmation-gated, protected, and serialized.

## Work

1. Verify the old state is empty and bootstrap resources survive.
2. Pre-arm Terraform's stateful S3/ECR deletion flags in the protected destroy job.
3. Change stack, IAM policies, workflow validation, GitHub variables, and docs to
   `eu-west-2`, leaving backend region/bucket unchanged.
4. Validate, commit, push, deploy, and approve the protected jobs.
5. Independently verify account/region, isolation, health, PAPER/live flags, immutable
   image identity, secrets permissions, alarm, and a no-change Terraform plan.
6. Update project evidence and move this plan to completed.

## Completion evidence

- Destroy run `33964747292` left zero Terraform state objects and preserved the
  bootstrap backend/OIDC roles.
- The future destroy sequence now plans and applies the two stateful deletion flags
  before producing its saved destroy plan; a read-only target plan showed exactly two
  flag changes.
- IAM role policies and the GitHub `AWS_REGION` variable target `eu-west-2`; the
  backend bucket and `TF_STATE_REGION` remain `us-east-1`.
- Local and GitHub CI validation passed, including 96 tests and Actionlint.
- Deploy run `33976145081` applied 22 resources, built the immutable image, and passed
  the SSM health gate for commit `fec85ec`.
- Independent AWS/SSM checks verified instance `i-03d8810150224343d`, digest
  `sha256:5ceed0cbb63ef41c0abb4b0bb0520a273609c7a6dbd5cdf6d8fc1005d021728a`,
  network isolation, IMDSv2, root-only secrets, PAPER/live-disable health, secured
  storage, alarm `OK`, and a no-change refreshed Terraform plan.
- The host geoblock response is `GB/ENG blocked=true`; the environment is explicitly
  limited to public-data PAPER operation.
