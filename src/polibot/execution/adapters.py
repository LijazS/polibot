from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Protocol
from uuid import UUID

from pydantic import BaseModel, ConfigDict, model_validator

from polibot.domain.models import OrderIntent
from polibot.domain.values import Price, Quantity


class OrderType(StrEnum):
    GTC = "GTC"
    GTD = "GTD"
    FOK = "FOK"
    FAK = "FAK"


class SubmissionStatus(StrEnum):
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    UNKNOWN = "unknown"


class ExternalOrderStatus(StrEnum):
    LIVE = "live"
    MATCHED = "matched"
    CANCELLED = "cancelled"
    UNKNOWN = "unknown"


class OrderRequest(BaseModel):
    """Validated unsigned request. It is deliberately not an exchange wire payload."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    intent: OrderIntent
    order_type: OrderType
    post_only: bool = False
    expiration: datetime | None = None

    @model_validator(mode="after")
    def validate_semantics(self) -> OrderRequest:
        if self.order_type is OrderType.GTD and self.expiration is None:
            raise ValueError("GTD requires an expiration")
        if self.order_type is not OrderType.GTD and self.expiration is not None:
            raise ValueError("expiration is only valid for GTD")
        if self.post_only and self.order_type in {OrderType.FOK, OrderType.FAK}:
            raise ValueError("immediate order types cannot be post-only")
        return self


@dataclass(frozen=True)
class SubmissionResult:
    intent_id: UUID
    status: SubmissionStatus
    external_order_id: str | None = None
    filled_quantity: Decimal = Decimal("0")
    reason: str | None = None


@dataclass(frozen=True)
class ExternalOrder:
    external_order_id: str
    intent_id: UUID
    token_id: str
    price: Price
    original_quantity: Quantity
    filled_quantity: Quantity
    status: ExternalOrderStatus


@dataclass(frozen=True)
class ExternalFill:
    fill_id: str
    external_order_id: str
    token_id: str
    price: Price
    quantity: Quantity


@dataclass(frozen=True)
class CancelResult:
    cancelled: tuple[str, ...]
    not_cancelled: dict[str, str]


class ExchangeExecutionAdapter(Protocol):
    """Future write boundary. Production implementation is intentionally absent."""

    async def create_order(self, request: OrderRequest) -> SubmissionResult: ...

    async def cancel_order(self, external_order_id: str) -> CancelResult: ...

    async def cancel_all(self) -> CancelResult: ...

    async def get_order(self, external_order_id: str) -> ExternalOrder | None: ...

    async def get_open_orders(self) -> tuple[ExternalOrder, ...]: ...

    async def get_fills(self) -> tuple[ExternalFill, ...]: ...

    async def heartbeat(self) -> bool: ...


class FakeExchangeAdapter:
    """Deterministic in-memory adapter; it has no HTTP client or signer."""

    def __init__(
        self,
        outcomes: dict[UUID, SubmissionStatus] | None = None,
        fill_quantities: dict[UUID, Decimal] | None = None,
        *,
        heartbeat_ok: bool = True,
        cancel_failures: frozenset[str] = frozenset(),
    ) -> None:
        self._outcomes = outcomes or {}
        self._fill_quantities = fill_quantities or {}
        self._heartbeat_ok = heartbeat_ok
        self._cancel_failures = cancel_failures
        self._orders: dict[str, ExternalOrder] = {}
        self._results: dict[UUID, SubmissionResult] = {}

    async def create_order(self, request: OrderRequest) -> SubmissionResult:
        existing = self._results.get(request.intent.intent_id)
        if existing is not None:
            return existing
        status = self._outcomes.get(request.intent.intent_id, SubmissionStatus.ACCEPTED)
        external_id = (
            f"fake-{request.intent.intent_id}" if status is SubmissionStatus.ACCEPTED else None
        )
        filled = self._fill_quantities.get(request.intent.intent_id, request.intent.quantity)
        if filled > request.intent.quantity:
            raise ValueError("fake fill cannot exceed requested quantity")
        result = SubmissionResult(
            intent_id=request.intent.intent_id,
            status=status,
            external_order_id=external_id,
            filled_quantity=filled if status is SubmissionStatus.ACCEPTED else Decimal("0"),
            reason=None if status is SubmissionStatus.ACCEPTED else status.value,
        )
        self._results[request.intent.intent_id] = result
        if external_id is not None:
            order_status = (
                ExternalOrderStatus.MATCHED
                if filled == request.intent.quantity
                else ExternalOrderStatus.LIVE
            )
            self._orders[external_id] = ExternalOrder(
                external_id,
                request.intent.intent_id,
                request.intent.token_id,
                request.intent.price,
                request.intent.quantity,
                filled,
                order_status,
            )
        return result

    async def cancel_order(self, external_order_id: str) -> CancelResult:
        order = self._orders.get(external_order_id)
        if order is None or external_order_id in self._cancel_failures:
            return CancelResult((), {external_order_id: "not found or injected failure"})
        self._orders[external_order_id] = ExternalOrder(
            order.external_order_id,
            order.intent_id,
            order.token_id,
            order.price,
            order.original_quantity,
            order.filled_quantity,
            ExternalOrderStatus.CANCELLED,
        )
        return CancelResult((external_order_id,), {})

    async def cancel_all(self) -> CancelResult:
        cancelled: list[str] = []
        failures: dict[str, str] = {}
        for order_id, order in tuple(self._orders.items()):
            if order.status is not ExternalOrderStatus.LIVE:
                continue
            result = await self.cancel_order(order_id)
            cancelled.extend(result.cancelled)
            failures.update(result.not_cancelled)
        return CancelResult(tuple(cancelled), failures)

    async def get_order(self, external_order_id: str) -> ExternalOrder | None:
        return self._orders.get(external_order_id)

    async def get_open_orders(self) -> tuple[ExternalOrder, ...]:
        return tuple(o for o in self._orders.values() if o.status is ExternalOrderStatus.LIVE)

    async def get_fills(self) -> tuple[ExternalFill, ...]:
        return tuple(
            ExternalFill(
                f"fill-{order.external_order_id}",
                order.external_order_id,
                order.token_id,
                order.price,
                order.filled_quantity,
            )
            for order in self._orders.values()
            if order.filled_quantity > 0
        )

    async def heartbeat(self) -> bool:
        return self._heartbeat_ok
