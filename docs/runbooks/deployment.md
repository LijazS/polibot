# Deployment runbook

No production deployment is authorized during bootstrap. For local validation, copy
safe configuration, keep paper mode, run CI-equivalent checks, build containers, and
verify `/health`. A future production runbook must cover reviewed immutable artifacts,
separate secrets/state, migrations/backups, readiness, explicit mode, exposure caps,
operator approval, monitoring, and post-deploy reconciliation. Never use deployment
location to evade platform restrictions.

