from __future__ import annotations

from collections.abc import Awaitable

import httpx
import pytest

from polibot.market_data.client import (
    ClobSnapshotClient,
    MarketChannelClient,
    MarketDataConnectionError,
    ReconnectPolicy,
    WebSocketConnection,
)
from polibot.market_data.messages import BookMessage

BOOK = (
    '{"event_type":"book","asset_id":"token-yes","market":"condition",'
    '"bids":[],"asks":[],"timestamp":"1","hash":"h"}'
)


class FakeConnection:
    def __init__(self, messages: list[str | Exception]) -> None:
        self.messages = messages
        self.sent: list[str] = []
        self.closed = False

    async def send(self, message: str) -> None:
        self.sent.append(message)

    async def recv(self) -> str:
        value = self.messages.pop(0)
        if isinstance(value, Exception):
            raise value
        return value

    async def close(self) -> None:
        self.closed = True


async def no_sleep(_: float) -> None:
    return None


def connector_for(
    connections: list[FakeConnection],
) -> tuple[list[tuple[str, float]], object]:
    calls: list[tuple[str, float]] = []

    def connector(url: str, timeout: float) -> Awaitable[WebSocketConnection]:
        calls.append((url, timeout))

        async def result() -> WebSocketConnection:
            return connections.pop(0)

        return result()

    return calls, connector


@pytest.mark.asyncio
async def test_market_channel_subscribes_and_parses_snapshot() -> None:
    connection = FakeConnection([BOOK])
    calls, connector = connector_for([connection])
    client = MarketChannelClient(connector=connector, sleeper=no_sleep)  # type: ignore[arg-type]
    stream = client.stream(["token-yes"])
    message = await anext(stream)
    await stream.aclose()
    assert isinstance(message, BookMessage)
    assert calls[0][1] == 5.0
    assert connection.sent == ['{"assets_ids": ["token-yes"], "type": "market"}']
    assert connection.closed


@pytest.mark.asyncio
async def test_market_channel_reconnect_is_bounded() -> None:
    first = FakeConnection([OSError("disconnect")])
    second = FakeConnection([OSError("disconnect")])
    calls, connector = connector_for([first, second])
    client = MarketChannelClient(
        connector=connector,  # type: ignore[arg-type]
        policy=ReconnectPolicy(maximum_reconnects=1),
        sleeper=no_sleep,
    )
    with pytest.raises(MarketDataConnectionError, match="bounded reconnect"):
        await anext(client.stream(["token-yes"]))
    assert len(calls) == 2
    assert first.closed and second.closed


@pytest.mark.asyncio
async def test_rest_snapshot_uses_documented_token_parameter() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/book"
        assert request.url.params["token_id"] == "token-yes"
        return httpx.Response(
            200,
            json={
                "market": "condition",
                "asset_id": "token-yes",
                "timestamp": "1",
                "hash": "h",
                "bids": [],
                "asks": [],
                "min_order_size": "1",
                "tick_size": "0.01",
                "neg_risk": False,
                "last_trade_price": "0.5",
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        message = await ClobSnapshotClient(http_client).get_book("token-yes")
    assert message.event_type == "book"


def test_reconnect_delay_is_bounded() -> None:
    policy = ReconnectPolicy(maximum_reconnects=3, initial_delay_seconds=1, maximum_delay_seconds=2)
    assert policy.delay(1, 0.25) == 1.25
    assert policy.delay(3, 100) == 2
