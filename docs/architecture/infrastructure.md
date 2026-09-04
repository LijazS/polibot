# Infrastructure

Local development uses Docker Compose with the application and PostgreSQL. The app
container runs as a non-root user and defaults to paper mode. CI validates only; it
has no secrets or deployment privileges.

The Terraform scaffold defines a private persistent EC2 host, encrypted RDS
PostgreSQL with managed master password/backups/deletion protection, encrypted and
versioned S3 archive, CloudWatch log group, and narrowly scoped host IAM. The region
is configurable; `eu-west-2` is a candidate default based on official server-location
documentation, never permission to access the platform. Only paper/shadow environment
values validate. No apply was performed, state backend selected, or secret supplied.

Future operations still require reviewed networking/AMI, remote encrypted state,
alarms, restore exercises, image scanning, and rollback. No Lambda core loop, EKS,
or geographic-restriction workaround is present.
