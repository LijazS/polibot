# Market data

Persist raw payloads or lossless envelopes before/alongside normalization so adapter
bugs can be investigated. Capture event, market, condition and token identifiers;
status and structure; source and local receipt timestamps; sequence/update IDs;
book snapshots/deltas and depth; trades; fee/reward observations; and adapter version.

Snapshot recovery must detect gaps, pause affected proposals, obtain a trusted new
snapshot, and only resume after buffered updates reconcile. Unknown sequencing or
stale books fail closed. Retention, compression, partitioning, and current stream
semantics remain implementation-plan decisions.

