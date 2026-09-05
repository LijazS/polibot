# AWS PAPER eu-west-2 migration

Status: Active
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
