import os
from datetime import UTC, datetime

import httpx
import pytest

from polibot.discovery import DiscoveryService, GammaDiscoveryClient
from polibot.market_data import ClobSnapshotClient, MarketChannelClient

pytestmark = [
    pytest.mark.public_api,
    pytest.mark.skipif(
        os.getenv("POLIBOT_RUN_PUBLIC_API_TESTS") != "1",
        reason="explicit public API smoke opt-in is required",
    ),
]


@pytest.mark.asyncio
async def test_public_discovery_snapshot_and_websocket_are_read_only() -> None:
    timeout = httpx.Timeout(connect=10, read=20, write=5, pool=5)
    async with httpx.AsyncClient(timeout=timeout) as client:
        discovery_client = GammaDiscoveryClient(client, attempts=2)
        batch = await DiscoveryService(discovery_client).discover_market_page(
            observed_at=datetime.now(UTC), limit=10
        )
        assert batch.markets
        market = batch.markets[0]
        token_id = market.outcome_tokens[0].token_id
        book = await ClobSnapshotClient(client).get_book(token_id)
        assert book.asset_id == token_id
        stream = MarketChannelClient().stream([token_id])
        message = await anext(stream)
        await stream.aclose()
        assert message.market == market.condition_id
