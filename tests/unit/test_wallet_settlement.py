from datetime import datetime
from decimal import Decimal

import pytest
from pydantic import ValidationError

from polibot.settlement import FakeSettlementAdapter, SettlementIntent, SettlementOperation
from polibot.wallet import FakeSigner, SigningRequest


@pytest.mark.asyncio
async def test_fake_signer_rejects_live_purpose(now: datetime) -> None:
    signer = FakeSigner()
    signature = await signer.sign(SigningRequest("shadow", "abc", now))
    assert signature.value == "FAKE:abc"
    with pytest.raises(PermissionError):
        await signer.sign(SigningRequest("live", "abc", now))


@pytest.mark.asyncio
async def test_settlement_is_simulation_only(now: datetime) -> None:
    intent = SettlementIntent(
        operation=SettlementOperation.MERGE,
        condition_id="condition",
        quantity=Decimal("2"),
        yes_token_id="yes",
        no_token_id="no",
        created_at=now,
    )
    adapter = FakeSettlementAdapter()
    assert (await adapter.simulate(intent)).value == "simulated"
    assert adapter.intents == [intent]


def test_settlement_requires_explicit_token_mapping(now: datetime) -> None:
    with pytest.raises(ValidationError, match="Yes and No"):
        SettlementIntent(
            operation=SettlementOperation.SPLIT,
            condition_id="condition",
            quantity=Decimal("1"),
            created_at=now,
        )
