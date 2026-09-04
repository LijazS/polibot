# Vanilla NegRisk arbitrage

## Objective

Find an executable portfolio whose payout meets a target in every formally valid
terminal state for less than that guaranteed modeled payout.

## Market prerequisites

Machine-readable, supported vanilla NegRisk structure; complete outcome/token map;
explicit treatment of Other/placeholders and outcome mutability; active markets;
fresh depth; and known current fees/mechanics. Names never establish exclusivity.

## Mathematical model

Minimize depth-aware acquisition cost subject to `payout(state_i) >= target` for
every enumerated valid state. The solver output includes holdings, state payout
matrix, minimum payout, all costs, rounding, and buffer. Unsupported or incomplete
state spaces are infeasible, not opportunities.

## Inputs and opportunity detection

Use validated event/NegRisk metadata, token mappings, normalized books, dynamic
fees/minimums, balances, and health. Build the terminal-state matrix deterministically,
solve, independently verify the solution, then form a proposal with payoff proof.

## Sizing and execution plan

Constrain the optimizer by actual depth and exposure. The execution plan orders legs,
caps cost/slippage and unmatched exposure/duration, expires quickly, and defines
cancel/recovery behavior for each partial portfolio.

## Risk checks

Require supported structure, complete state enumeration, independent payoff
verification, known costs, fresh data, feasible depth/minimums, limits, health,
reconciliation, deduplication, and buffered worst-case edge.

## Failure states

Added/placeholder outcomes, metadata ambiguity, solver/verification disagreement,
book gaps, partial legs, rejections, timeouts, halts, conversion failure, restart,
and settlement mismatch disable or reconcile the path.

## Exit and settlement

Hold the verified portfolio to terminal payout or use only documented, tested
conversion/redemption adapters. An incomplete portfolio is exposed inventory and
follows its pre-approved recovery policy.

## Accounting and backtest requirements

Attribute structural edge, fees, slippage, conversion/settlement, directional
residuals, and operational adjustments separately. Replay outcome-set changes, L2
depth, latency, partial fills, rounding, solver feasibility, and failures.

## Promotion and human intervention

Property tests across generated terminal-state matrices, solver cross-checks,
reconciled replay/paper results, and sustained shadow evidence precede capped V2
live consideration. Humans approve each supported structure class and investigate
model ambiguity or unmatched portfolios.

## Known unknowns

Verify current official NegRisk metadata, augmentation rules, Other behavior,
conversion mechanics, fees, and order constraints before implementation.

