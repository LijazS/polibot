# AWS PAPER destroy workflow

Status: Completed
Date: 2026-09-05

## Objective

Add a manually dispatched, protected Terraform destroy workflow for the deployed
PAPER stack. Destruction must require an exact typed confirmation, use the existing
GitHub OIDC infrastructure role and remote state, serialize against deployment, and
preserve the separately bootstrapped Terraform state bucket and GitHub OIDC roles.

## Safety boundaries

- Never dispatch the workflow as part of implementation or verification.
- Restrict execution to `main`, AWS account `484632959006`, and environment `paper`.
- Keep LIVE hard-disabled and introduce no credentials.
- Make deletion of the versioned application-data bucket and non-empty ECR repository
  explicit only in the destroy invocation; normal Terraform applies remain protective.
- Document that EC2-local PostgreSQL data, S3 application/history objects, logs, and
  ECR images are permanently deleted by the workflow.
- Keep the remote state bucket, state history, GitHub environment, OIDC provider, and
  GitHub roles outside the destroy target so the stack can be audited or recreated.

## Work

1. Add an exact-confirmation, protected plan/apply destroy workflow.
2. Add an opt-in Terraform variable for destructive cleanup during destroy only.
3. Grant the infrastructure role only the additional S3 object/version deletion
   permissions required to empty the PAPER data bucket.
4. Update deployment, rollback, infrastructure, and status documentation.
5. Validate formatting, Terraform, YAML, JSON, docs, tests, and a no-change normal plan.

## Completion evidence

- Terraform formatting and validation passed with AWS provider v6.63.0.
- A remote normal plan reported no changes.
- A read-only destroy preview reported `0 to add, 0 to change, 22 to destroy`; no
  destroy apply was run.
- The deployed infrastructure-role policy allows application-bucket version listing
  and object/version deletion while state-object deletion remains denied.
- Actionlint v1.7.12 and YAML parsing passed for all workflows.
- Ruff, formatting, mypy, 96 pytest tests, compileall, Alembic offline SQL, JSON parsing,
  documentation links, and `git diff --check` passed.
