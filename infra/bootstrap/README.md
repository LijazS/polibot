# One-time manual bootstrap

These reviewed artifacts create only the S3 Terraform state bucket and two GitHub
OIDC roles. They are intentionally outside the main Terraform state because those
resources must exist before GitHub can initialize that state.

Nothing in this directory is executed automatically. Review the JSON and follow
`docs/runbooks/aws-github-bootstrap.md`. The scripts fail on an unexpected account
and refuse to overwrite an existing bucket or role.

The AWS OIDC provider already exists in account `484632959006` with audience
`sts.amazonaws.com`; do not create a duplicate. The current authenticated CLI identity
is the account root. Prefer a dedicated administrative identity for bootstrap and do
not use the root identity for routine deployment.

