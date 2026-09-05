# PAPER infrastructure destruction

`.github/workflows/destroy-paper.yml` is the only supported full-stack destruction
path. It is manual, restricted to `main`, protected by the `paper` GitHub environment,
serialized with deployment, authenticated through GitHub OIDC, and bound to the
expected AWS account and remote Terraform state.

## Permanent data loss

The workflow permanently deletes the PAPER EC2 host and its local PostgreSQL volume,
all versions in the application/history S3 bucket, every image in the PAPER ECR
repository, CloudWatch application logs and alarm, IAM instance role/profile, and
PAPER networking. Back up any required research or database data before approval.

The separately bootstrapped Terraform state bucket and its version history, GitHub
environment/variables, AWS GitHub OIDC provider, and GitHub infrastructure/deployment
roles are not in the PAPER Terraform state and are intentionally preserved. They let
an operator audit the final state or recreate the stack with the deployment workflow.

## Run the workflow

From GitHub Actions, select **Destroy PAPER AWS infrastructure**, choose `main`, enter
the exact case-sensitive confirmation `DESTROY-POLIBOT-PAPER`, and dispatch it. The
equivalent CLI request is:

```powershell
gh workflow run destroy-paper.yml --ref main -f confirmation=DESTROY-POLIBOT-PAPER
```

Review the destroy-plan log and approve the protected apply only after confirming the
account, region, backend key, and complete list of deletions. The apply job creates a
targeted saved plan that records `force_destroy=true` and `force_delete=true` for the
application bucket and ECR repository in Terraform state. This is necessary because
destroy planning alone retains their prior state values. It then creates a fresh saved
destroy plan, prints it, applies that exact plan, and fails if Terraform state is not
empty afterward.

Do not run raw local `terraform destroy`: it bypasses the repository/environment
checks and the documented audit trail. Do not remove the bootstrap state bucket or
OIDC roles as part of routine stack destruction.

## Recreate

After a successful destroy, manually run **Deploy PAPER to AWS** from `main` and pass
the normal `paper` environment approval. The preserved remote backend supports a
clean Terraform apply. Application/database data is not restored unless a separate
backup was created and its restore procedure was validated.
