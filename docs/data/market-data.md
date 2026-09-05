# Market data

Persist raw payloads or lossless envelopes before/alongside normalization so adapter
bugs can be investigated. Capture event, market, condition and token identifiers;
status and structure; source and local receipt timestamps; sequence/update IDs;
book snapshots/deltas and depth; trades; fee/reward observations; and adapter version.

Snapshot recovery must detect gaps, pause affected proposals, obtain a trusted new
snapshot, and only resume after buffered updates reconcile. Unknown sequencing or
stale books fail closed. Retention, compression, partitioning, and current stream
semantics remain implementation-plan decisions.

Implemented message support follows the official 2026-09-04 documentation record:
book snapshot, price change, last trade, and tick-size change. The REST snapshot
endpoint is the recovery authority. WebSocket reconnect is bounded with capped
exponential backoff and the documented 10-second client ping default.

## Continuous retention boundary

The worker keeps recent operational/raw envelopes in PostgreSQL and reports database
size plus container-visible disk use. At 85% disk use it becomes degraded and not
ready, preventing new paper decisions. The existing Parquet format is the historical
export target; use coarse daily partitions such as
`raw/orderbook/date=YYYY-MM-DD/part-*.parquet`, optionally in the private application
data bucket, rather than millions of tiny files.

Automatic deletion is disabled: source rows must not be removed until an archive has
been written, checksummed, read back, copied to durable storage, and recorded in an
archive manifest. Until verified rotation is implemented, operators must monitor
`/status` and stop collection before the threshold rather than delete evidence.
