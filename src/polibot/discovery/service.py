from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from polibot.discovery.client import GammaDiscoveryClient, PublicDiscoveryError
from polibot.discovery.normalization import (
    InvalidMarketMetadata,
    extract_token_ids,
    normalize_market,
)
from polibot.domain.models import Market


@dataclass(frozen=True)
class DiscoveryFailure:
    market_id: str
    reason: str


@dataclass(frozen=True)
class DiscoveryBatch:
    markets: tuple[Market, ...]
    failures: tuple[DiscoveryFailure, ...]


class DiscoveryService:
    def __init__(self, client: GammaDiscoveryClient) -> None:
        self._client = client

    async def discover_market_page(
        self, *, observed_at: datetime, limit: int = 100, offset: int = 0
    ) -> DiscoveryBatch:
        dtos = await self._client.list_markets(limit=limit, offset=offset)
        markets: list[Market] = []
        failures: list[DiscoveryFailure] = []
        for dto in dtos:
            try:
                token_ids = extract_token_ids(dto)
                if not token_ids:
                    raise InvalidMarketMetadata("market has no token IDs")
                verification = await self._client.token_pair(token_ids[0])
                markets.append(normalize_market(dto, observed_at, verification))
            except (InvalidMarketMetadata, PublicDiscoveryError, ValueError) as exc:
                failures.append(DiscoveryFailure(dto.id, str(exc)))
        return DiscoveryBatch(tuple(markets), tuple(failures))
