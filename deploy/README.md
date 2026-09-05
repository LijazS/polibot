# PAPER deployment bundle

These files are uploaded by the protected GitHub workflow to a private, SHA-specific
S3 prefix and executed through Systems Manager. The deployment accepts only immutable
ECR digest URIs, creates the PostgreSQL password once on the instance, runs Alembic
before application startup, verifies `/health` reports PAPER with live disabled, and
rolls the application image back on failure when a previous image exists.

Database migrations are not automatically downgraded during image rollback. A release
with a backward-incompatible migration requires a reviewed forward-recovery plan.

