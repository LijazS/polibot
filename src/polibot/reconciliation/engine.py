from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import StrEnum


class DiscrepancyType(StrEnum):
    MATCH = "match"
    TEMPORARY_LAG = "temporary_lag"
    UNKNOWN_ORDER = "unknown_order"
    UNKNOWN_FILL = "unknown_fill"
    BALANCE_MISMATCH = "balance_mismatch"
    POSITION_MISMATCH = "position_mismatch"
    SETTLEMENT_MISMATCH = "settlement_mismatch"
    CRITICAL = "critical"


@dataclass(frozen=True)
class AccountState:
    balances: dict[str, Decimal]
    positions: dict[str, Decimal]
    open_order_ids: frozenset[str]
    fill_ids: frozenset[str]
    settlement_ids: frozenset[str]
    observed_at: datetime


@dataclass(frozen=True)
class Discrepancy:
    kind: DiscrepancyType
    subject: str
    expected: str
    actual: str


@dataclass(frozen=True)
class ReconciliationReport:
    reconciled_at: datetime
    discrepancies: tuple[Discrepancy, ...]

    @property
    def healthy(self) -> bool:
        return all(
            item.kind in {DiscrepancyType.MATCH, DiscrepancyType.TEMPORARY_LAG}
            for item in self.discrepancies
        )


class ReconciliationEngine:
    def compare(
        self,
        expected: AccountState,
        authoritative: AccountState,
        now: datetime,
        *,
        permitted_lag_ids: frozenset[str] = frozenset(),
    ) -> ReconciliationReport:
        items: list[Discrepancy] = []
        self._compare_amounts(
            "balance",
            expected.balances,
            authoritative.balances,
            DiscrepancyType.BALANCE_MISMATCH,
            items,
        )
        self._compare_amounts(
            "position",
            expected.positions,
            authoritative.positions,
            DiscrepancyType.POSITION_MISMATCH,
            items,
        )
        self._compare_ids(
            "order",
            expected.open_order_ids,
            authoritative.open_order_ids,
            permitted_lag_ids,
            DiscrepancyType.UNKNOWN_ORDER,
            items,
        )
        self._compare_ids(
            "fill",
            expected.fill_ids,
            authoritative.fill_ids,
            permitted_lag_ids,
            DiscrepancyType.UNKNOWN_FILL,
            items,
        )
        self._compare_ids(
            "settlement",
            expected.settlement_ids,
            authoritative.settlement_ids,
            permitted_lag_ids,
            DiscrepancyType.SETTLEMENT_MISMATCH,
            items,
        )
        if not items:
            items.append(Discrepancy(DiscrepancyType.MATCH, "account", "matched", "matched"))
        return ReconciliationReport(now, tuple(items))

    @staticmethod
    def _compare_amounts(
        label: str,
        expected: dict[str, Decimal],
        actual: dict[str, Decimal],
        kind: DiscrepancyType,
        items: list[Discrepancy],
    ) -> None:
        for key in sorted(expected.keys() | actual.keys()):
            left = expected.get(key, Decimal("0"))
            right = actual.get(key, Decimal("0"))
            if left != right:
                items.append(Discrepancy(kind, f"{label}:{key}", str(left), str(right)))

    @staticmethod
    def _compare_ids(
        label: str,
        expected: frozenset[str],
        actual: frozenset[str],
        permitted_lag_ids: frozenset[str],
        kind: DiscrepancyType,
        items: list[Discrepancy],
    ) -> None:
        for item_id in sorted(expected ^ actual):
            item_kind = DiscrepancyType.TEMPORARY_LAG if item_id in permitted_lag_ids else kind
            items.append(
                Discrepancy(
                    item_kind,
                    f"{label}:{item_id}",
                    str(item_id in expected),
                    str(item_id in actual),
                )
            )
