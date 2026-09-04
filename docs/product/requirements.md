# Product requirements

## V1

Polibot must discover and normalize markets, tokens, status, NegRisk structure, and
dynamic fee/reward metadata; ingest and recover L2 books with source/receipt timing;
record raw and normalized inputs; replay realistic execution; produce typed binary,
validated NegRisk, and Holding Rewards proposals; independently reject unsafe work;
paper/shadow execute; reconcile accounting; and expose logs, metrics, audit, and health.

V1 must have no enabled real-money order path. Results must disclose execution
assumptions and separate P&L components.

## V2

After V1 gates pass, V2 may add isolated signing, explicit/capped live mode,
multi-leg recovery, supported order semantics, kill/cancel controls, settlement and
conversion adapters, continuous reconciliation, crash recovery, deployment, and
alerting. Only validated structural strategies qualify initially. Market making is
shadow-only until separately promoted.

## Quality attributes

Correctness and capital safety precede profit and latency. Decisions must be
deterministic, reproducible, typed, observable, testable without network access,
and auditable from source observation through P&L.

