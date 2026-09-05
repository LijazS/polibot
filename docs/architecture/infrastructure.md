# Infrastructure

Local development uses Docker Compose with the application and PostgreSQL. The app
container runs as a non-root user and defaults to paper mode. CI validates only; it
has no secrets or deployment privileges.

The PAPER stack targets the explicitly discovered AWS account and `eu-west-2`. It
creates a dedicated low-cost VPC with one public subnet used only for outbound access,
an EC2 host with no inbound rules or SSH key, an immutable ECR repository, a private
encrypted/versioned S3 data and deployment-artifact bucket, SSM administration, and
CloudWatch bootstrap/deployment logs plus an EC2 status alarm. PostgreSQL is a local
Docker service with a named EBS-backed volume and no published port.

GitHub Actions authenticates through the existing account-wide GitHub OIDC provider.
Separate repository/environment-scoped roles divide Terraform from image/deployment
permissions. Terraform state uses a separately bootstrapped encrypted/versioned S3
bucket and native S3 lockfile. Deployment is manual, serialized, protected by the
`paper` GitHub environment, tied to `main`, and uses the exact commit SHA plus the ECR
digest returned after push.

Destruction is also manual, serialized with deployment, protected by the same
environment, restricted to `main`, and requires an exact typed confirmation. Its
explicit destructive Terraform variable permits deletion of the non-empty PAPER S3
and ECR resources only for that destroy plan. The state bucket, state history, OIDC
provider, and GitHub roles remain outside the stack and survive teardown.

## Region assessment

The original `us-east-1` PAPER host was destroyed before the replacement was deployed
in `eu-west-2`. As of 2026-09-05, Polymarket's official
[trading overview](https://docs.polymarket.com/trading/overview) identifies `eu-west-2`
as the primary-server region and says approved KYC/KYB participants can obtain direct
co-location there for the lowest possible latency. The same documentation identifies
`eu-west-1` as the closest non-georestricted region. Its
[geographic restrictions](https://docs.polymarket.com/api-reference/geoblock) must be
checked before any order path is considered.

For public-data PAPER collection, a normal `eu-west-2` EC2 host is expected to reduce
network distance relative to the former `us-east-1` host, but it is not the documented
direct co-location entitlement and exact latency must be measured. For any future
eligible order submission, prefer `eu-west-1` unless Polymarket has explicitly approved
`eu-west-2` co-location for the operator. Cloud placement must never be used to evade
geographic restrictions. This placement is approved only for PAPER/public-data work;
it does not promote or enable an order-submission path.

There is no NAT gateway, load balancer, RDS, Lambda core loop, EKS, SSH, static AWS
key, publicly reachable app/database, or geographic-restriction workaround.
Backups/restores, cost alarms, host replacement, teardown/recreation, and sustained
runtime behavior still require operator exercises.
