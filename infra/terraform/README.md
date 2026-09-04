# Terraform

Terraform deployment is deferred until the V1 local recorder and replay path are
validated. Future infrastructure must use separate state per environment, a
configurable AWS region, least-privilege roles, managed secrets, reviewed plans,
and documented rollback. This directory deliberately contains no deployable stack.
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
