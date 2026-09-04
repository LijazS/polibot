# ADR-001: Modular monolith

- Status: Accepted
- Date: 2026-09-04

## Context

V1/V2 need multiple cohesive capabilities but strong consistency and a small team.

## Decision

Use a Python 3.12 modular monolith with explicit internal ports. Split deployable
services only after profiling or operational evidence and another ADR.

## Consequences

Transactions, testing, and audit flow remain simple; module boundaries require
discipline. Kafka, microservices, and Kubernetes are excluded by default.

