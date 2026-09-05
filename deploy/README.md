# PAPER deployment bundle

These files are uploaded by the protected GitHub workflow to a private, SHA-specific
S3 prefix and executed through Systems Manager. The deployment accepts only immutable
ECR digest URIs, creates the PostgreSQL password once on the instance, runs Alembic,
and starts PostgreSQL plus separate API and worker services. It verifies PAPER/LIVE
safety, a current worker heartbeat, and readiness before success. API and worker roll
back together when a compatible previous image and SHA exist.

Database migrations are not automatically downgraded during image rollback. A release
with a backward-incompatible migration requires a reviewed forward-recovery plan.

`post-deploy-verification-commands.json` is a secret-safe SSM parameter document for
independent checks of runtime health, mode flags, secret-file permissions, deployed
SHA/digest, and container health. It prints no credential values.
