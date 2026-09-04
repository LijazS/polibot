from __future__ import annotations

import asyncio
import json
from collections.abc import Awaitable, Callable
from decimal import Decimal

import httpx
from pydantic import TypeAdapter

from polibot.discovery.dto import GammaEventDTO, GammaMarketDTO, TokenPairDTO


class PublicDiscoveryError(RuntimeError):
    pass


class GammaDiscoveryClient:
    """Bounded, unauthenticated reads from documented public endpoints only."""

    def __init__(
        self,
        client: httpx.AsyncClient,
        *,
        gamma_base_url: str = "https://gamma-api.polymarket.com",
        clob_base_url: str = "https://clob.polymarket.com",
        attempts: int = 3,
        backoff_seconds: Decimal = Decimal("0.25"),
        sleeper: Callable[[float], Awaitable[None]] = asyncio.sleep,
    ) -> None:
        if attempts < 1 or attempts > 5:
            raise ValueError("attempts must be between 1 and 5")
        self._client = client
        self._gamma_base_url = gamma_base_url.rstrip("/")
        self._clob_base_url = clob_base_url.rstrip("/")
        self._attempts = attempts
        self._backoff_seconds = backoff_seconds
        self._sleeper = sleeper

    @classmethod
    def with_default_transport(cls) -> GammaDiscoveryClient:
        timeout = httpx.Timeout(connect=5.0, read=10.0, write=5.0, pool=5.0)
        return cls(httpx.AsyncClient(timeout=timeout))

    async def aclose(self) -> None:
        await self._client.aclose()

    async def list_markets(
        self, *, limit: int = 100, offset: int = 0
    ) -> tuple[GammaMarketDTO, ...]:
        if not 1 <= limit <= 500 or offset < 0:
            raise ValueError("limit must be 1..500 and offset must be non-negative")
        data = await self._get_json(
            f"{self._gamma_base_url}/markets", params={"limit": limit, "offset": offset}
        )
        return tuple(TypeAdapter(list[GammaMarketDTO]).validate_python(data))

    async def list_events(self, *, limit: int = 100, offset: int = 0) -> tuple[GammaEventDTO, ...]:
        if not 1 <= limit <= 500 or offset < 0:
            raise ValueError("limit must be 1..500 and offset must be non-negative")
        data = await self._get_json(
            f"{self._gamma_base_url}/events", params={"limit": limit, "offset": offset}
        )
        return tuple(TypeAdapter(list[GammaEventDTO]).validate_python(data))

    async def token_pair(self, token_id: str) -> TokenPairDTO:
        if not token_id:
            raise ValueError("token_id is required")
        data = await self._get_json(f"{self._clob_base_url}/markets-by-token/{token_id}")
        return TokenPairDTO.model_validate(data)

    async def _get_json(self, url: str, params: dict[str, int] | None = None) -> object:
        last_error: Exception | None = None
        for attempt in range(self._attempts):
            try:
                response = await self._client.get(url, params=params)
                if response.status_code == 429 or response.status_code >= 500:
                    response.raise_for_status()
                if response.status_code >= 400:
                    raise PublicDiscoveryError(
                        f"public discovery request rejected with HTTP {response.status_code}"
                    )
                return json.loads(response.text, parse_float=Decimal)
            except (httpx.TransportError, httpx.HTTPStatusError) as exc:
                last_error = exc
                if attempt + 1 < self._attempts:
                    await self._sleeper(float(self._backoff_seconds * (2**attempt)))
        raise PublicDiscoveryError(
            "public discovery request failed after bounded retries"
        ) from last_error
