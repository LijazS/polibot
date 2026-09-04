# Incident response

1. Stop new exposure with the global kill control; confirm mode and affected scope.
2. Preserve logs, raw events, identifiers, timestamps, configuration version, and alerts.
3. Cancel outstanding orders when safe/supported; never assume cancellation succeeded.
4. Reconcile exchange orders/fills, balances, positions, chain actions, and local state.
5. Escalate unmatched exposure and ambiguous submissions for manual review.
6. Restore only after cause, state, limits, and data freshness are understood.
7. Document timeline, capital impact, corrective tests, and promotion-gate consequences.

The bootstrap has no live orders or cancel API. This runbook becomes executable as
V2 controls are implemented and tested.

