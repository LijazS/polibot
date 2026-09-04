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

Exchange and settlement fakes hold no HTTP/RPC client. Terraform accepts only paper
or shadow environments, provides no public host ingress, requires IMDSv2, encrypts
storage, and uses RDS-managed password generation. Secret values are absent.
