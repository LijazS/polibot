# Binary complete-set arbitrage

## Objective

Acquire complementary YES and NO claims only when executable all-in cost plus a
risk buffer is below deterministic terminal/merge value.

## Market prerequisites

Validated complementary token mapping, active/tradable status, fresh L2 depth,
known current fees/ticks/minimums, supported settlement mechanics, balances, and no
sequence or reconciliation fault.

## Mathematical model

For quantity `q`, prove both valid terminal states pay at least `q`. Compute each
leg from consumed depth, then `net_edge = worst_case_payout - all_in_cost - buffer`.
All-in cost includes fees, rounding, slippage, conversion/settlement costs where
applicable, and conservative legging assumptions. `YES ask + NO ask < 1` is not proof.

## Inputs and opportunity detection

Use normalized books, market/token metadata, fee models, minimum/tick rules, health,
and exposure. Walk both books for matched quantity, build a state-indexed payoff
proof, and emit a proposal only above the configured minimum edge.

## Sizing and execution plan

Size to the minimum verified depth across legs and all configured exposure limits.
The plan declares leg order, order semantics, maximum cost/slippage, unmatched
exposure and duration, expiry, cancellation, and partial-fill response. No atomicity
is assumed.

## Risk checks

Require fresh/complete metadata and books, payoff proof, known fees, sufficient
balance/depth, limits, positive buffered edge, system health, reconciliation health,
deduplication, and an acceptable worst case after partial-fill policy.

## Failure states

Sequence gap, stale book, disappearing depth, first-leg-only fill, rejection,
timeout/unknown submission, cancel failure, market halt, fee change, restart, and
settlement mismatch fail closed and may require hedge, reconcile, or manual review.

## Exit and settlement

Keep the complete set through valid settlement or merge/redeem through a separately
verified adapter. Partial inventory follows the approved recovery policy; it is not
silently treated as neutral.

## Accounting and backtest requirements

Separate structural edge, fees, slippage, legging/inventory P&L, settlement, and
operational adjustments. Replay L2 depth with latency, partial fills, minimums,
rounding, dynamic fees, failures, and split/merge/redeem assumptions.

## Promotion and human intervention

Unit/property proof tests, reproducible replay, reconciled paper operation, and a
sustained shadow gate precede any capped V2 live trial. Humans set limits, approve
promotion, investigate unmatched legs/reconciliation, and control kill switches.

## Known unknowns

The offline implementation walks actual displayed depth, applies a provenance-bearing
dynamic fee model and buffers, evaluates cumulative quantities, and emits a terminal
state proof. Property tests cover the guaranteed-payout inequality. Current live
liquidity, end-to-end fill behavior, settlement cost, and opportunity frequency remain
`PENDING_DATA`.
