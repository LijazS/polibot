from collections.abc import AsyncIterator
from typing import Protocol

from polibot.domain.models import MarketSnapshot


class MarketDataSource(Protocol):
    """Read-only exchange boundary used by discovery and strategy orchestration."""

    def snapshots(self) -> AsyncIterator[MarketSnapshot]: ...
