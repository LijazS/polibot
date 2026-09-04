from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Protocol


@dataclass(frozen=True)
class SigningRequest:
    purpose: str
    payload_digest: str
    expires_at: datetime


@dataclass(frozen=True)
class Signature:
    signer_id: str
    value: str


class Signer(Protocol):
    async def sign(self, request: SigningRequest) -> Signature: ...


class Wallet(Protocol):
    async def address(self) -> str: ...


class BalanceProvider(Protocol):
    async def balance(self, asset: str) -> Decimal: ...


class AllowanceProvider(Protocol):
    async def allowance(self, asset: str, spender: str) -> Decimal: ...


class FakeSigner:
    """Test-only signer whose output cannot authorize any external transaction."""

    async def sign(self, request: SigningRequest) -> Signature:
        if request.purpose not in {"test", "paper", "shadow"}:
            raise PermissionError("fake signer only permits non-live purposes")
        return Signature("fake-signer", f"FAKE:{request.payload_digest}")


class FakeWallet:
    async def address(self) -> str:
        return "0x0000000000000000000000000000000000000000"


class FakeBalanceAllowanceProvider:
    def __init__(self, balances: dict[str, Decimal] | None = None) -> None:
        self._balances = balances or {}

    async def balance(self, asset: str) -> Decimal:
        return self._balances.get(asset, Decimal("0"))

    async def allowance(self, asset: str, spender: str) -> Decimal:
        del spender
        return self._balances.get(asset, Decimal("0"))
