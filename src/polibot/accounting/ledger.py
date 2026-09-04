from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from polibot.domain.models import PnLComponent, PnLComponentType


@dataclass(frozen=True)
class PnLSummary:
    by_component: dict[PnLComponentType, Decimal]
    net: Decimal


class AccountingLedger:
    def __init__(self) -> None:
        self._components: list[PnLComponent] = []

    def record(self, component: PnLComponent) -> None:
        self._components.append(component)

    def components(self) -> tuple[PnLComponent, ...]:
        return tuple(self._components)

    def summary(self) -> PnLSummary:
        separated = {kind: Decimal("0") for kind in PnLComponentType}
        for component in self._components:
            separated[component.component_type] += component.amount
        return PnLSummary(separated, sum(separated.values(), Decimal("0")))
