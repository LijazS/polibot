---
applyTo: "infra/**,Dockerfile,docker-compose.yml,.github/workflows/**"
---

# Infrastructure instructions

Use Terraform for reviewed infrastructure, least privilege, encrypted managed
secrets, and separate state/credentials per environment. Region is configurable.
Defaults and CI are non-live and contain no credentials or deployment authority.
Never deploy unreviewed changes. Plan migrations, backup, rollback, observability,
and reconciliation. Do not introduce EKS without an ADR and measured need. Cloud
location must not evade legal or platform access restrictions.

