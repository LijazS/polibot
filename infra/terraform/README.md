# Terraform environments

`environments/paper` is the only deployable stack. It targets AWS account
`484632959006` in `us-east-1`, fails on a different account, and permits only the
`paper` environment value.

The stack creates a dedicated VPC, one public subnet for outbound connectivity, an
EC2 host with no inbound security-group rules or SSH key, an immutable ECR repository,
a private encrypted/versioned S3 data bucket, SSM access, and CloudWatch logs/alarm.
PostgreSQL runs locally in Docker on the host and is not exposed. There is no NAT
gateway, load balancer, RDS database, Kubernetes cluster, or live-trading credential.

The S3 backend is partial by design. GitHub Actions supplies its bucket, key, and
region after the one-time bootstrap in `infra/bootstrap`; S3 native lockfiles are
enabled and DynamoDB locking is not used. Follow `docs/runbooks/aws-github-bootstrap.md`.

No Terraform apply has been performed as part of repository implementation.
# Non-live AWS scaffold

This root module prepares a private persistent EC2 host, encrypted RDS PostgreSQL,
an encrypted/versioned S3 Parquet archive, narrowly scoped IAM, and CloudWatch logs.
It accepts only `paper` or `shadow` as the environment and writes
`POLIBOT_LIVE_TRADING_ENABLED=false` on the host.

It intentionally does not contain credentials, a funded wallet, a trading signer,
automatic deployment, or remote-state configuration. Supply reviewed VPC/subnet and
immutable AMI inputs, add an approved state backend, and run a security review before
any future apply. Region is configurable; the default is only a candidate based on
the official server-location documentation, not an access entitlement.
