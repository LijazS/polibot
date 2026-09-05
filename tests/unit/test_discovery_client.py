from collections.abc import Awaitable
from decimal import Decimal

import httpx
import pytest

from polibot.discovery.client import GammaDiscoveryClient, PublicDiscoveryError


async def no_sleep(_: float) -> None:
    return None


@pytest.mark.asyncio
async def test_client_uses_public_read_only_market_endpoint() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/markets"
        return httpx.Response(200, json=[{"id": "m1", "orderPriceMinTickSize": 0.01}])

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        client = GammaDiscoveryClient(http_client)
        markets = await client.list_markets(limit=1)
    assert markets[0].id == "m1"
    assert str(markets[0].minimum_tick_size) == "0.01"


@pytest.mark.asyncio
async def test_client_retries_transient_failure_with_a_bound() -> None:
    calls = 0
    sleeps: list[float] = []

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(503)

    def sleeper(delay: float) -> Awaitable[None]:
        sleeps.append(delay)
        return no_sleep(delay)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        client = GammaDiscoveryClient(http_client, attempts=3, sleeper=sleeper)
        with pytest.raises(PublicDiscoveryError, match="bounded retries"):
            await client.list_events(limit=1)
    assert calls == 3
    assert sleeps == [0.25, 0.5]


@pytest.mark.asyncio
async def test_client_does_not_retry_permanent_rejection() -> None:
    calls = 0

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(400)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        client = GammaDiscoveryClient(http_client)
        with pytest.raises(PublicDiscoveryError, match="HTTP 400"):
            await client.list_markets(limit=1)
    assert calls == 1


@pytest.mark.asyncio
async def test_client_reads_dynamic_clob_market_parameters() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/clob-markets/condition"
        return httpx.Response(
            200,
            json={
                "t": [
                    {"t": "token-yes", "o": "Yes"},
                    {"t": "token-no", "o": "No"},
                ],
                "mos": 5,
                "mts": 0.01,
                "mbf": 0,
                "tbf": 0,
                "fd": {"r": 0.04, "e": 2, "to": True},
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        info = await GammaDiscoveryClient(http_client).clob_market_info("condition")
    assert info.minimum_order_size == 5
    assert info.minimum_tick_size == Decimal("0.01")
    assert info.fee_details is not None
    assert info.fee_details.rate == Decimal("0.04")
