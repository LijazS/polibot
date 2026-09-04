# Infrastructure

Local development uses Docker Compose with the application and PostgreSQL. The app
container runs as a non-root user and defaults to paper mode. CI validates only; it
has no secrets or deployment privileges.

AWS is a possible future target with a configurable region (initially evaluate
`eu-west-2`, never encode it as an invariant). Prefer a simple container host, then
managed PostgreSQL and object storage when justified. Use least privilege, managed
secrets, separate state/environments, reviewed plans, monitoring, backups, and tested
rollback. No Lambda core loop, EKS, or geographic-restriction workarounds.

