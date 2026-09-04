# Security

Trust no external payload until parsed into strict domain models. Redact credentials
and sensitive headers from logs/errors. Secrets belong in environment-specific
secret stores, never source, examples, fixtures, CI, or container layers.

Future wallet/signing code is isolated behind a narrow interface, uses a dedicated
low-balance wallet during validation, and requires focused tests and review. Live
mode needs separate affirmative enablement, validated credentials, reconciliation,
limits, kill switches, and health. Missing or ambiguous state denies exposure and
emits a high-severity audit event. Follow market-integrity and access restrictions.

