# Replay and backtesting

Replay consumes ordered recorded observations with an explicit clock and produces
the same normalized snapshots, proposals, risk decisions, and simulated transitions
as online modes. Exports use Parquet with schema/version and source provenance.

Simulation must model L2 depth, partial fills, latency, stale opportunities,
tick/quantity rounding, dynamic fees, slippage, minimums, legging exposure,
disconnects, and settlement mechanics. Maker research additionally models queue
assumptions and adverse selection. Each report discloses assumptions, data gaps, and
P&L components. Displayed historical liquidity is never treated as a guaranteed fill.

