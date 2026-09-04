import json
from datetime import UTC, datetime
from pathlib import Path

import httpx
import pytest

from polibot.discovery import DiscoveryService, GammaDiscoveryClient
from polibot.domain.models import Tradability

FIXTURE = Path(__file__).parents[1] / "fixtures" / "gamma_market.json"


@pytest.mark.asyncio
async def test_public_shape_to_verified_domain_pipeline() -> None:
    market_payload = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/markets":
            return httpx.Response(200, json=[market_payload])
        if request.url.path == "/markets-by-token/token-yes":
            return httpx.Response(
                200,
                json={
                    "condition_id": "0xcondition",
                    "primary_token_id": "token-yes",
                    "secondary_token_id": "token-no",
                },
            )
        return httpx.Response(404)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        service = DiscoveryService(GammaDiscoveryClient(http_client))
        result = await service.discover_market_page(
            observed_at=datetime(2026, 9, 4, tzinfo=UTC), limit=1
        )
    assert not result.failures
    assert len(result.markets) == 1
    assert result.markets[0].tradability is Tradability.TRADABLE


@pytest.mark.asyncio
async def test_pipeline_quarantines_bad_market_without_aborting_page() -> None:
    market_payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    market_payload["clobTokenIds"] = "not-json"

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/markets"
        return httpx.Response(200, json=[market_payload])

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        service = DiscoveryService(GammaDiscoveryClient(http_client))
        result = await service.discover_market_page(
            observed_at=datetime(2026, 9, 4, tzinfo=UTC), limit=1
        )
    assert not result.markets
    assert result.failures[0].market_id == "market-123"
    assert "not valid JSON" in result.failures[0].reason
