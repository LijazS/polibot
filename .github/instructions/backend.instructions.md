---
applyTo: "src/**/*.py,tests/**/*.py"
---

# Backend instructions

Use Python 3.12 types and async only at I/O boundaries. Keep domain logic pure and
framework/exchange dictionaries out of it. Financial values use Decimal/fixed-point
with explicit rounding; floats are rejected. Strategies emit proposals only. Only
deterministic risk creates approval, and execution always verifies it. Inject clocks
and adapters, fail closed, preserve idempotency/audit identifiers, and cover success,
rejection, stale/incomplete data, partial failure, and invariants with tests. Keep
persistence behind repositories and update behavior docs with code.

