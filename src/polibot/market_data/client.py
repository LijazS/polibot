from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator, Awaitable, Callable, Sequence
from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol, cast

import httpx
from websockets.asyncio.client import connect

from polibot.market_data.messages import BookMessage, NormalizedMarketMessage, parse_market_message


class MarketDataConnectionError(RuntimeError):
    pass


class WebSocketConnection(Protocol):
    async def send(self, message: str) -> None: ...

    async def recv(self) -> str: ...

    async def close(self) -> None: ...


class WebSocketConnector(Protocol):
    def __call__(self, url: str, open_timeout: float) -> Awaitable[WebSocketConnection]: ...


async def default_connector(url: str, open_timeout: float) -> WebSocketConnection:
    connection = await connect(url, open_timeout=open_timeout, ping_interval=None)
    return cast(WebSocketConnection, connection)


@dataclass(frozen=True)
class ReconnectPolicy:
    maximum_reconnects: int = 5
    initial_delay_seconds: float = 0.25
    maximum_delay_seconds: float = 4.0

    def delay(self, failure_number: int, jitter: float) -> float:
        if not 1 <= failure_number <= self.maximum_reconnects:
            raise ValueError("failure_number outside reconnect policy")
        base = min(
            self.initial_delay_seconds * (2 ** (failure_number - 1)),
            self.maximum_delay_seconds,
        )
        return float(min(base + max(0.0, jitter), self.maximum_delay_seconds))


class MarketChannelClient:
    """Public market-channel reader with bounded reconnect and explicit heartbeat."""

    def __init__(
        self,
        *,
        connector: WebSocketConnector = default_connector,
        url: str = "wss://ws-subscriptions-clob.polymarket.com/ws/market",
        connect_timeout: float = 5.0,
        heartbeat_seconds: float = 10.0,
        policy: ReconnectPolicy | None = None,
        sleeper: Callable[[float], Awaitable[None]] = asyncio.sleep,
        jitter: Callable[[], float] = lambda: 0.0,
    ) -> None:
        self._connector = connector
        self._url = url
        self._connect_timeout = connect_timeout
        self._heartbeat_seconds = heartbeat_seconds
        self._policy = policy or ReconnectPolicy()
        self._sleeper = sleeper
        self._jitter = jitter

    async def stream(self, asset_ids: Sequence[str]) -> AsyncIterator[NormalizedMarketMessage]:
        if not asset_ids or any(not asset_id for asset_id in asset_ids):
            raise ValueError("at least one non-empty asset ID is required")
        failures = 0
        while failures <= self._policy.maximum_reconnects:
            connection: WebSocketConnection | None = None
            try:
                connection = await self._connector(self._url, self._connect_timeout)
                subscription = json.dumps({"assets_ids": list(asset_ids), "type": "market"})
                await connection.send(subscription)
                while True:
                    try:
                        raw = await asyncio.wait_for(
                            connection.recv(), timeout=self._heartbeat_seconds
                        )
                    except TimeoutError:
                        await connection.send("PING")
                        continue
                    if raw == "PONG":
                        continue
                    yield parse_market_message(raw)
            except asyncio.CancelledError:
                raise
            except (OSError, TimeoutError, ValueError) as exc:
                failures += 1
                if failures > self._policy.maximum_reconnects:
                    raise MarketDataConnectionError(
                        "market channel exhausted bounded reconnect policy"
                    ) from exc
                await self._sleeper(self._policy.delay(failures, self._jitter()))
            finally:
                if connection is not None:
                    await connection.close()


class ClobSnapshotClient:
    def __init__(
        self,
        client: httpx.AsyncClient,
        base_url: str = "https://clob.polymarket.com",
    ) -> None:
        self._client = client
        self._base_url = base_url.rstrip("/")

    async def get_book(self, token_id: str) -> BookMessage:
        if not token_id:
            raise ValueError("token_id is required")
        response = await self._client.get(f"{self._base_url}/book", params={"token_id": token_id})
        if response.status_code >= 400:
            raise MarketDataConnectionError(
                f"book snapshot request failed with HTTP {response.status_code}"
            )
        payload = json.loads(response.text, parse_float=Decimal)
        if not isinstance(payload, dict):
            raise MarketDataConnectionError("book snapshot response must be an object")
        payload["event_type"] = "book"
        return BookMessage.model_validate(payload)
