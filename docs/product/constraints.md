# Constraints

- Python 3.12 modular monolith for V1/V2; external I/O behind adapters.
- PostgreSQL is durable state; Parquet is research/archive; Redis requires justification.
- Current official Polymarket contracts must be verified at implementation time.
- Access must comply with platform terms and applicable law; infrastructure must not evade restrictions.
- Secrets never enter source, logs, images, fixtures, or CI.
- Live actions require isolated credentials, low-balance validation, explicit mode,
  healthy reconciliation, and deterministic approval.
- No deployment, signer, or external trading is part of the bootstrap.
- Backtests use L2/depth and execution assumptions, not candle fills or displayed-price certainty.
