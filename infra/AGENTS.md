# Infrastructure rules

- Infrastructure code must not deploy automatically or contain secret values.
- Keep region configurable and permissions least-privilege.
- LIVE remains disabled in all examples and defaults.
- Persistent runtimes use hosts/containers, not Lambda; do not add EKS without an ADR.

