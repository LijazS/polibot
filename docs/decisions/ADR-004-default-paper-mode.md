# ADR-004: Default paper mode

- Status: Accepted
- Date: 2026-09-04

## Context

A fresh checkout must not create financial side effects.

## Decision

Default to paper. Live requires an explicit mode plus separate affirmative enablement
and future credential/control validation. The bootstrap executor refuses live entirely.

## Consequences

Development, CI, and missing/ambiguous configuration remain safe. Future live work
must add controls without weakening replay/paper/shadow guarantees.

