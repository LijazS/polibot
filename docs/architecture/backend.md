# Backend

The backend is async at network and persistence boundaries and deterministic in the
domain. Pydantic models reject unknown fields and float financial inputs. Strategies
receive normalized snapshots and expose only proposal generation. Domain modules do
not depend on HTTP, WebSocket, SQLAlchemy, signing, or framework response objects.

Near-term orchestration should connect discovery, sequence-aware books, recorder,
strategies, risk, simulated execution, and audit with injected ports and an explicit
clock. Background tasks must propagate cancellation and health failures fail closed.

