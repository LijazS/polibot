# ADR-003: Deterministic risk gate

- Status: Accepted
- Date: 2026-09-04

## Context

Strategy, UI, automation, or AI output cannot safely be treated as authorization.

## Decision

Strategies emit immutable proposals. An independent deterministic risk engine alone
creates proposal-bound, expiring approvals. Execution rejects missing, mismatched,
expired, or unsafe approval state.

## Consequences

Risk outcomes are machine-readable and auditable. Additional orchestration cannot
bypass the gate; risk availability is safety-critical and failure denies exposure.

