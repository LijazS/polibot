# Security

Trust no external payload until parsed into strict domain models. Redact credentials
and sensitive headers from logs/errors. Secrets belong in environment-specific
secret stores, never source, examples, fixtures, CI, or container layers.

Wallet, signer, balance, and allowance protocols are isolated behind a narrow
interface. The only implementation is a fake signer that rejects live purpose and
emits an unmistakably invalid `FAKE:` signature. A future reviewed production signer
must use a dedicated low-balance wallet during validation. Live
mode needs separate affirmative enablement, validated credentials, reconciliation,
limits, kill switches, and health. Missing or ambiguous state denies exposure and
emits a high-severity audit event. Follow market-integrity and access restrictions.

Exchange and settlement fakes hold no HTTP/RPC client. Terraform accepts only the
paper environment, provides no host ingress, requires IMDSv2, and encrypts storage.
The EC2 instance role is limited to SSM, pulling the application image, reading its
deployment bundle, archiving history, and writing logs. The database password is
generated once on-host into root-only files; it is absent from Terraform, user data,
GitHub, images, SSM commands, and logs. The application health check fails if PAPER
mode or the live-trading disable flag changes.

GitHub OIDC trust matches the immutable owner/repository IDs and the `paper`
environment subject, not a repository-name wildcard. No static AWS credentials are
stored. Bootstrap is the only manual AWS mutation and must not be performed with the
account root identity for routine use.
