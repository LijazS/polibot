# Holding Rewards complete-set pilot

## Objective

Measure whether intact complementary inventory on currently eligible markets earns
rewards that remain attractive after acquisition, operations, and settlement costs.

## Market prerequisites

Validated complete-set tokens, fresh market/status data, dynamically observed reward
eligibility and parameters with source/time, supported custody/settlement, and
reconciled balances. No historical rate is assumed current.

## Mathematical model

Expected pilot return equals observed reward accrual estimate minus acquisition,
fees, slippage, settlement, funding, and operational risk allowances. Directional
terminal payout is modeled separately. Uncertain reward income is never used as a
guaranteed payoff in structural risk proof.

## Inputs and opportunity detection

Capture eligibility, parameter/version observations, qualifying-balance rules,
books, costs, program windows, and actual credits. Initially emit observation or
paper proposals only when a complete-set acquisition itself passes structural risk.

## Sizing and execution plan

Pilot size is independently capped and remains small. Acquisition uses the binary
multi-leg plan; holding duration, custody, program-change response, and settlement
are explicit. Neutrality does not waive platform or operational exposure limits.

## Risk checks

Require verified completeness, known costs, fresh reward/status data, conservative
reward value, exposure/drawdown limits, custody and reconciliation health, and a
safe unwind/settlement plan. Unknown eligibility means no reward-dependent trade.

## Failure states

Program change/removal, missing credit, eligibility ambiguity, partial inventory,
wallet or settlement issue, market halt, stale metadata, reconciliation mismatch,
and reward API failure stop scaling and trigger review.

## Exit and settlement

Exit at a declared observation horizon, eligibility change, risk trigger, or normal
merge/redemption/settlement. Preserve evidence linking qualifying inventory to actual
credits and costs.

## Accounting and backtest requirements

Holding rewards are separate from structural trading P&L, fees, slippage, funding,
and adjustments. Historical tests use dated observed rules and mark missing accrual
data; they cannot manufacture rewards from a timeless constant.

## Promotion and human intervention

Observation and paper validation precede any tiny V2 controlled exposure. Promotion
requires reconciled expected-versus-actual credits over predefined windows. Humans
approve capital and halt on unexplained credits, eligibility, or balance differences.

## Known unknowns

Verify current official eligibility discovery, accrual calculation, payment timing,
qualifying custody, program changes, exclusions, and data endpoints.

