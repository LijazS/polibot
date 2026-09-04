# Rollback runbook

For local bootstrap, stop the application and restore the prior reviewed image; do
not delete the PostgreSQL volume. Before future production changes, record artifact
and migration rollback compatibility, back up durable data, disable new exposure,
cancel safe-to-cancel orders, reconcile exchange/chain state, deploy the prior image,
verify health/accounting, and retain audit evidence. Irreversible migrations require
a forward-recovery plan before release.

