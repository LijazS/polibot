# One-time AWS and GitHub bootstrap

Status: completed and verified 2026-09-05  
Repository: `LijazS/polibot`  
AWS account/region: `484632959006` / `us-east-1`

This procedure creates only the prerequisites that cannot be created by the main
Terraform state: the state bucket, two GitHub OIDC roles, and the protected GitHub
environment/variables. Review every command first. Do not add AWS access keys or any
Polymarket credential. Do not dispatch the deployment workflow until post-bootstrap
verification has been completed.

The working `browser-login` profile currently resolves to the account root ARN. Use a
dedicated administrator identity for the bootstrap if possible, and never use root for
routine deployment. Re-authenticate if needed with:

```powershell
aws login --profile browser-login
aws sts get-caller-identity --profile browser-login
```

The second command must report account `484632959006`. Stop on any other account.

The completed bootstrap used the authenticated `browser-login` root session because
it was the only available administrative identity. Routine workflows do not use that
identity; they can assume only the two OIDC roles below.

## 1. Create the Terraform state bucket

From the repository root, inspect `infra/bootstrap/create-backend.ps1` and its JSON
files, then run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File infra/bootstrap/create-backend.ps1 -Profile browser-login
```

Expected output names bucket `polibot-tfstate-484632959006-us-east-1` and state key
`polibot/paper/terraform.tfstate`. The script refuses to overwrite an accessible
bucket and configures encryption, versioning, bucket-owner enforcement, complete
public-access blocking, and a TLS-only policy.

If the process is interrupted after the bucket has been created, inspect it first and
use `-ResumeExisting` to idempotently finish its security configuration. Never use that
switch for an unverified pre-existing bucket.

Verify:

```powershell
aws s3api get-public-access-block --profile browser-login --bucket polibot-tfstate-484632959006-us-east-1
aws s3api get-bucket-versioning --profile browser-login --bucket polibot-tfstate-484632959006-us-east-1
aws s3api get-bucket-encryption --profile browser-login --bucket polibot-tfstate-484632959006-us-east-1
aws s3api get-bucket-ownership-controls --profile browser-login --bucket polibot-tfstate-484632959006-us-east-1
aws s3api get-bucket-policy --profile browser-login --bucket polibot-tfstate-484632959006-us-east-1
```

## 2. Verify the existing GitHub OIDC provider

Do not create a second provider. Verify the account-wide provider and audience:

```powershell
aws iam get-open-id-connect-provider --profile browser-login --open-id-connect-provider-arn arn:aws:iam::484632959006:oidc-provider/token.actions.githubusercontent.com
```

`ClientIDList` must include `sts.amazonaws.com`.

## 3. Create the two repository/environment-scoped roles

Inspect both trust and permission policies under `infra/bootstrap`, then run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File infra/bootstrap/create-roles.ps1 -Profile browser-login
```

Expected role ARNs:

```text
arn:aws:iam::484632959006:role/polibot-github-infra
arn:aws:iam::484632959006:role/polibot-github-deploy
```

Both trust policies must contain exactly this subject and the standard audience:

```text
repo:LijazS@180333961/polibot@1357427608:environment:paper
sts.amazonaws.com
```

Verify:

```powershell
aws iam get-role --profile browser-login --role-name polibot-github-infra
aws iam get-role-policy --profile browser-login --role-name polibot-github-infra --policy-name polibot-paper-infra
aws iam get-role --profile browser-login --role-name polibot-github-deploy
aws iam get-role-policy --profile browser-login --role-name polibot-github-deploy --policy-name polibot-paper-deploy
```

## 4. Create and protect the GitHub `paper` environment

In GitHub, open **Settings → Environments → New environment**, name it `paper`, and:

1. restrict deployment branches/tags to the `main` branch only;
2. add a required reviewer other than the workflow actor where the repository plan supports it;
3. enable prevention of self-review where available;
4. do not add environment secrets.

GitHub CLI equivalents for environment creation and the custom branch policy are:

```powershell
'{"wait_timer":0,"prevent_self_review":true,"deployment_branch_policy":{"protected_branches":false,"custom_branch_policies":true}}' | gh api --method PUT repos/LijazS/polibot/environments/paper --input -
gh api --method POST repos/LijazS/polibot/environments/paper/deployment-branch-policies -f name=main -f type=branch
```

Add these environment-level Actions variables (not secrets):

| Variable | Exact value |
| --- | --- |
| `AWS_ACCOUNT_ID` | `484632959006` |
| `AWS_REGION` | `us-east-1` |
| `TF_STATE_BUCKET` | `polibot-tfstate-484632959006-us-east-1` |
| `TF_STATE_KEY` | `polibot/paper/terraform.tfstate` |
| `TF_STATE_REGION` | `us-east-1` |
| `AWS_INFRA_ROLE_ARN` | `arn:aws:iam::484632959006:role/polibot-github-infra` |
| `AWS_DEPLOY_ROLE_ARN` | `arn:aws:iam::484632959006:role/polibot-github-deploy` |

GitHub CLI equivalents:

```powershell
gh variable set AWS_ACCOUNT_ID --env paper --body 484632959006
gh variable set AWS_REGION --env paper --body us-east-1
gh variable set TF_STATE_BUCKET --env paper --body polibot-tfstate-484632959006-us-east-1
gh variable set TF_STATE_KEY --env paper --body polibot/paper/terraform.tfstate
gh variable set TF_STATE_REGION --env paper --body us-east-1
gh variable set AWS_INFRA_ROLE_ARN --env paper --body arn:aws:iam::484632959006:role/polibot-github-infra
gh variable set AWS_DEPLOY_ROLE_ARN --env paper --body arn:aws:iam::484632959006:role/polibot-github-deploy
```

Verify with `gh api repos/LijazS/polibot/environments/paper` and
`gh variable list --env paper`. Confirm there are no AWS key secrets.

## 5. Commit and stop for verification

Review the diff, commit it, and push it to `main` through the repository's normal review
process. Do not run **Deploy PAPER to AWS** yet. Report completion of steps 1–4 so the
bootstrap resources, trust, environment protection, variables, and absence of static
credentials can be verified before any Terraform plan/apply or deployment.
