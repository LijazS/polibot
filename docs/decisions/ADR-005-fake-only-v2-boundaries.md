# ADR-005: Keep V2 external write boundaries fake-only

Status: Accepted  
Date: 2026-09-05

## Context

Execution, wallet, and settlement interfaces are needed to test state transitions,
idempotency, reconciliation, and recovery. Real authentication, signing, order
submission, and transaction broadcasting are outside the approved master-task boundary.

## Decision

Define narrow typed ports and deterministic in-memory fakes. Do not provide a
production signer, credential loader, authenticated write transport, or blockchain
broadcaster. All execution coordinators reject LIVE at construction. Unknown results
enter reconciliation and cannot be retried through the state machine.

## Consequences

V2 safety behavior can be exercised offline without any ability to move capital.
Future real integration requires a separate ADR, explicit operator authorization,
current protocol verification, threat review, service-backed persistence/recovery
tests, and unchanged deterministic risk gating.

## Rejected alternatives

- A dormant but functional live adapter: creates an unnecessary activation hazard.
- Signing inside strategies or execution plans: violates separation of authority.
- Blind retry after timeout: risks duplicate financial intent.

