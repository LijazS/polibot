# PAPER rollback runbook

The host records current and previous immutable ECR digest URIs under
`/opt/polibot/state`. A failed deployment automatically invokes
`/opt/polibot/bin/rollback.sh` when a previous image exists. The script pulls that
digest, restarts only the application, and requires healthy PAPER-mode output.

For an operator-initiated rollback, open a Systems Manager session or Run Command and
run `sudo /opt/polibot/bin/rollback.sh`. Do not expose SSH or port 8000. Inspect
`/var/log/polibot-deploy.log` and `/polibot/paper/host` afterward.

Database migrations are not downgraded. Every migration must therefore remain backward
compatible with the prior application image or carry a reviewed forward-recovery plan.
The local PostgreSQL volume is retained across application rollbacks but is deleted with
the EC2 root volume if Terraform destroys/replaces the instance; backup and restore are
an open operational gate. This PAPER stack contains no real orders to cancel.
