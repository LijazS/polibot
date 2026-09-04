# ADR-002: PostgreSQL durable state

- Status: Accepted
- Date: 2026-09-04

## Context

Decisions, executions, accounting, and reconciliation need transactional,
queryable, durable history.

## Decision

Use PostgreSQL through an async adapter. Use Parquet for research/archive. Add Redis
only for a demonstrated ephemeral/shared-state need.

## Consequences

Schema and migration discipline are required. Raw high-volume data needs planned
retention/export; Redis is not operational overhead during bootstrap.

