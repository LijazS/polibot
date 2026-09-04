# Business rules

1. Strategies emit `OpportunityProposal`; they never place orders.
2. Only the risk engine creates approvals; execution validates them.
3. Missing, stale, inconsistent, unhealthy, or unverified critical state rejects new exposure.
4. Money, prices, quantities, fees, and P&L never use binary floating point.
5. Structural proposals include executable depth, all costs, buffer, and a worst-case payoff proof.
6. Exclusivity comes from validated machine-readable structure, never outcome names.
7. Fees, rewards, eligibility, limits, and order semantics are dynamically sourced/versioned.
8. Default mode is paper; live requires deliberate, validated configuration.
9. P&L components remain separate; temporary incentives cannot hide trading losses.
10. Zero trades is valid when no proposal passes every control.
11. No manipulation, restriction bypass, martingale, or LLM-only authorization is permitted.

