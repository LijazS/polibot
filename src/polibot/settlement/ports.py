from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Protocol
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator

from polibot.domain.values import Quantity


class SettlementOperation(StrEnum):
    SPLIT = "split"
    MERGE = "merge"
    REDEEM = "redeem"
    NEGRISK_CONVERT = "negrisk_convert"


class SettlementIntent(BaseModel):
    """A non-broadcast transaction intent with explicit operation semantics."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    intent_id: UUID = Field(default_factory=uuid4)
    operation: SettlementOperation
    condition_id: str
    quantity: Quantity
    yes_token_id: str | None = None
    no_token_id: str | None = None
    index_sets: tuple[int, ...] = ()
    created_at: datetime

    @model_validator(mode="after")
    def validate_operation(self) -> SettlementIntent:
        if not self.condition_id:
            raise ValueError("condition ID is required")
        if self.quantity <= 0:
            raise ValueError("quantity must be positive")
        if self.operation in {SettlementOperation.SPLIT, SettlementOperation.MERGE} and (
            not self.yes_token_id or not self.no_token_id
        ):
            raise ValueError("split/merge require explicit Yes and No token IDs")
        if self.yes_token_id is not None and self.yes_token_id == self.no_token_id:
            raise ValueError("Yes and No tokens must differ")
        if self.operation is SettlementOperation.REDEEM and not self.index_sets:
            raise ValueError("redeem requires explicit index sets")
        return self


class SettlementResult(StrEnum):
    SIMULATED = "simulated"
    REJECTED = "rejected"


class SettlementAdapter(Protocol):
    async def simulate(self, intent: SettlementIntent) -> SettlementResult: ...


class FakeSettlementAdapter:
    """Simulation-only adapter; no RPC, relayer, signer, or contract dependency."""

    def __init__(self) -> None:
        self.intents: list[SettlementIntent] = []

    async def simulate(self, intent: SettlementIntent) -> SettlementResult:
        self.intents.append(intent)
        return SettlementResult.SIMULATED
