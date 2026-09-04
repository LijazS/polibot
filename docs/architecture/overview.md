# Architecture overview

Polibot uses a modular monolith so safety invariants can be enforced without
distributed-state ambiguity. Adapters normalize untrusted external observations.
Pure strategies convert snapshots to proposals. Risk validates proposals against
fresh market state, deterministic economics, exposure, health, and reconciliation.
Only its short-lived approval permits execution. Accounting and audit consume every
transition. Dependency direction points inward toward typed domain contracts.

Replay, paper, and shadow share decision logic; only adapters differ. Live is a V2
adapter set behind explicit configuration and additional controls. This prevents a
backtest/live logic fork while keeping real-world side effects isolated.

