# Inventory-aware market making (shadow)

## Objective

Estimate whether two-sided quoting can produce durable risk-adjusted spread capture
after adverse selection, inventory, fees, failures, and incentives. Current scope is
research/shadow only.

## Market prerequisites

Fresh sequence-consistent L2/trade data, active status, known tick/minimum/fee and
rebate/reward rules, sufficient activity, volatility/event-risk measures, and a
validated fair-value method. Live quoting is not permitted by V2 status alone.

## Mathematical model

Quotes derive from midpoint/microprice or another tested estimate, widened for
volatility and event risk and skewed by inventory. Expected value separates spread
capture, adverse selection, inventory mark/realization, fees, rebates, liquidity
rewards, and operational loss. Spread is not profit.

## Inputs and opportunity detection

Use books, trades, imbalance, volatility, time to resolution, inventory, fills,
current incentives, status, and health. Shadow decisions record exact quote price,
size, lifespan, reason, and counterfactual execution assumptions.

## Sizing and execution plan

Inventory, quote, market/event, and global caps dominate sizing. Plans define
post-only behavior only if verified, refresh/cancel cadence, stale protection,
one-sided exposure response, and event/news shutdown.

## Risk checks

Require data/metadata freshness, supported order semantics, inventory and loss caps,
price bands, health/reconciliation, self-trade prevention, kill switch, cancel-all,
and conservative queue/fill assumptions.

## Failure states

Stale/gapped books, toxic flow, volatility spikes, event news, inventory limit,
one-sided fills, cancel/heartbeat failure, unknown orders, disconnect, incentive
change, self-trade risk, and reconciliation mismatch stop quoting.

## Exit and settlement

Shadow positions follow modeled inventory reduction and settlement. Any future live
design must define controlled unwind without assuming liquidity and halt before
resolution/news risk exceeds thresholds.

## Accounting and backtest requirements

Report spread, directional/inventory, adverse movement, fees, slippage, rebates,
liquidity rewards, and adjustments separately. Replay L2 events with queue model,
latency, cancels, partial fills, disconnects, regime shifts, and sensitivity ranges.

## Promotion and human intervention

Predefined shadow duration and thresholds, out-of-sample evidence, reconciled
counterfactual fills, and stress tests are required. Live promotion needs its own
ADR and explicit operator decision. Humans handle incidents and inventory exceptions.

## Known unknowns

Verify current official maker order semantics, self-trade controls, queue behavior,
rebates/rewards, cancellation/heartbeat facilities, limits, and market-integrity rules.
