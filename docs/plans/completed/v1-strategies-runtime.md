# V1 strategies, simulation, accounting, and runtime

Status: completed  
Started: 2026-09-04
Completed: 2026-09-04

## Objective

Complete non-live V1 domain software: depth-aware binary proposals, formal vanilla
NegRisk modeling, reward observations, expanded risk limits, realistic paper
execution, separated accounting, metrics/reporting, and safe orchestration.

## Work

1. Implement depth-walking costs and binary complete-set proposal generation.
2. Expand risk controls for scoped exposure, slippage, quantity, unmatched exposure,
   errors/drawdown, duplicates, health, and reconciliation.
3. Implement explicit vanilla NegRisk state/payoff models and deterministic solver.
4. Implement reward observation/reconciliation without fixed program rates.
5. Implement partial-fill/latency/failure-aware paper simulation and attribution.
6. Add metrics, feasibility report, and cancellation-safe paper/shadow orchestration.
7. Add unit/property/integration tests and update strategy/status documentation.

## Result

Implemented and tested offline. Empirical effectiveness remains `PENDING_DATA`;
no live or public-account execution was performed.

## Safety invariants

- Strategies emit proposals only and include auditable payoff/economic evidence.
- Missing fees, depth, metadata, rules, or terminal states means no proposal.
- Reward income never contributes to guaranteed structural payoff.
- Simulation never implies displayed liquidity was filled.
- LIVE remains hard-disabled.
