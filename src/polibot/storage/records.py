from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum
from typing import Protocol
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator


class RecordKind(StrEnum):
    EVENT_METADATA = "event_metadata"
    MARKET_METADATA = "market_metadata"
    FEE_METADATA = "fee_metadata"
    REWARD_METADATA = "reward_metadata"
    RAW_MARKET_MESSAGE = "raw_market_message"
    BOOK_SNAPSHOT = "book_snapshot"
    BOOK_CHANGE = "book_change"
    TRADE = "trade"
    PROPOSAL = "proposal"
    RISK_DECISION = "risk_decision"
    SIMULATED_EXECUTION = "simulated_execution"
    POSITION = "position"
    PNL_COMPONENT = "pnl_component"
    RECONCILIATION = "reconciliation"


def _reject_float(value: object, path: str = "payload") -> None:
    if isinstance(value, float):
        raise ValueError(f"{path} contains binary floating-point")
    if isinstance(value, Mapping):
        for key, item in value.items():
            _reject_float(item, f"{path}.{key}")
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        for index, item in enumerate(value):
            _reject_float(item, f"{path}[{index}]")


def canonical_payload(payload: Mapping[str, object]) -> str:
    _reject_float(payload)

    def encode(value: object) -> str:
        if isinstance(value, (Decimal, UUID)):
            return str(value)
        if isinstance(value, datetime):
            if value.tzinfo is None or value.utcoffset() is None:
                raise TypeError("payload datetime must be timezone-aware")
            return value.astimezone(UTC).isoformat()
        raise TypeError(f"unsupported payload value: {type(value).__name__}")

    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        default=encode,
    )


class RecordedEnvelope(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    record_id: UUID = Field(default_factory=uuid4)
    ordinal: int = Field(ge=0)
    kind: RecordKind
    market_id: str | None = None
    token_id: str | None = None
    source_timestamp: datetime
    received_at: datetime
    payload_json: str

    @field_validator("source_timestamp", "received_at")
    @classmethod
    def require_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("record timestamps must be timezone-aware")
        return value.astimezone(UTC)


class Recorder(Protocol):
    async def append(self, record: RecordedEnvelope) -> None: ...

    async def read_all(self) -> tuple[RecordedEnvelope, ...]: ...


class InMemoryRecorder:
    def __init__(self) -> None:
        self._records: list[RecordedEnvelope] = []
        self._ids: set[UUID] = set()

    async def append(self, record: RecordedEnvelope) -> None:
        if record.record_id in self._ids:
            raise ValueError("duplicate record ID")
        self._records.append(record)
        self._ids.add(record.record_id)

    async def read_all(self) -> tuple[RecordedEnvelope, ...]:
        return tuple(self._records)
