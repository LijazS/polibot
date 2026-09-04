from datetime import timedelta

import pytest

from polibot.execution.adapters import FakeExchangeAdapter, OrderRequest, OrderType


def test_order_type_semantics(valid_proposal, now) -> None:
    intent = valid_proposal.execution_plan.intents[0]
    with pytest.raises(ValueError, match="GTD requires"):
        OrderRequest(intent=intent, order_type=OrderType.GTD)
    with pytest.raises(ValueError, match="cannot be post-only"):
        OrderRequest(intent=intent, order_type=OrderType.FOK, post_only=True)
    request = OrderRequest(
        intent=intent,
        order_type=OrderType.GTD,
        expiration=now + timedelta(minutes=1),
        post_only=True,
    )
    assert request.expiration is not None


@pytest.mark.asyncio
async def test_fake_adapter_idempotency_cancel_and_heartbeat(valid_proposal) -> None:
    adapter = FakeExchangeAdapter()
    request = OrderRequest(
        intent=valid_proposal.execution_plan.intents[0], order_type=OrderType.GTC
    )
    first = await adapter.create_order(request)
    second = await adapter.create_order(request)
    assert first == second
    assert await adapter.heartbeat()
    assert first.external_order_id is not None
    cancelled = await adapter.cancel_order(first.external_order_id)
    assert cancelled.cancelled == (first.external_order_id,)
