# Execution subsystem rules

- A matching, unexpired, unconsumed risk approval is mandatory.
- LIVE is hard-disabled; adapters and fakes must perform no real network writes.
- Unknown external outcomes require reconciliation and must not be retried blindly.
- Use Decimal for financial values and test partial, ambiguous, and restart failures.

