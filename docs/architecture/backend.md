# Backend

The backend is async at network and persistence boundaries and deterministic in the
domain. Pydantic models reject unknown fields and float financial inputs. Strategies
receive normalized snapshots and expose only proposal generation. Domain modules do
not depend on HTTP, WebSocket, SQLAlchemy, signing, or framework response objects.

Near-term orchestration should connect discovery, sequence-aware books, recorder,
strategies, risk, simulated execution, and audit with injected ports and an explicit
clock. Background tasks must propagate cancellation and health failures fail closed.

Discovery uses strict external DTOs and parses JSON numbers as `Decimal`. Gamma
outcome/token arrays are not trusted to assign token identity: normalization requires
the documented CLOB market-by-token response identifying primary Yes and secondary
No tokens. Invalid markets are quarantined without aborting a discovery page.

Market data parses documented snapshot, price-change, last-trade, and tick-change
messages. No conventional sequence is assumed. A book is strategy-readable only
after a valid snapshot; disconnect, stale time, out-of-order time, invalid tick,
identity mismatch, or crossed state invalidates it until a fresh snapshot.
