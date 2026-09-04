# Settlement subsystem rules

- Produce validated transaction intents only; never broadcast in this repository state.
- Require explicit condition/token identity and Decimal quantities.
- Unknown external state requires reconciliation before any retry.

