# ADR-006: PAPER AWS deployment through GitHub OIDC

Status: Accepted  
Date: 2026-09-05

## Decision

Deploy only PAPER mode from a manually dispatched, protected GitHub Actions workflow.
Use GitHub OIDC with separate infrastructure and deployment IAM roles whose trust is
bound to the repository's immutable owner/repository IDs and `paper` environment.

Use Terraform for a dedicated `us-east-1` VPC, one SSM-only EC2 host, immutable ECR,
private S3 data/artifacts, CloudWatch, and scoped instance IAM. Run PostgreSQL locally
on the EC2 root volume. Store Terraform state in a manually bootstrapped S3 bucket with
encryption, versioning, public-access blocking, TLS enforcement, and native lockfiles.

Deploy the exact commit as an immutable ECR digest through SSM. Generate the database
password on the host. Require the application health response to prove PAPER mode and
live trading disabled.

## Consequences

There are no static AWS keys, SSH ingress, public app/database, NAT gateway, RDS, load
balancer, or Kubernetes cost. The single host and local database are inexpensive and
simple but form one failure domain. Host replacement can lose data unless backups are
implemented and exercised. Forward migrations must be compatible with the prior image.

The OIDC provider and bootstrap roles/state bucket are prerequisites outside Terraform
state. They require a one-time reviewed administrator action. AWS APIs that cannot be
resource-scoped retain `Resource: *`; names, account/region checks, role separation,
exact pass-role, environment trust, and Terraform configuration constrain their use.

## Rejected alternatives

- Static AWS access keys in GitHub.
- SSH keys or inbound port 22.
- Public application or PostgreSQL ports.
- RDS, NAT gateway, load balancer, EKS, and multi-service topology for this validation gate.
- Mutable image tags as the deployed identity.
- Automatic deployment on push.
