from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from decimal import Decimal
from statistics import median

from polibot.domain.models import PnLComponentType


@dataclass(frozen=True)
class FeasibilityObservation:
    strategy_id: str
    edge: Decimal
    executable_size: Decimal
    approved: bool
    rejection_reason: str | None
    fill_fraction: Decimal
    maximum_exposure: Decimal
    latency_milliseconds: Decimal
    pnl_components: dict[PnLComponentType, Decimal]


@dataclass(frozen=True)
class StrategyFeasibilitySummary:
    observations: int
    approvals: int
    median_edge: Decimal | None
    median_executable_size: Decimal | None
    mean_fill_fraction: Decimal | None
    maximum_exposure: Decimal
    rejection_reasons: dict[str, int]
    pnl_components: dict[PnLComponentType, Decimal]
    latency_samples: tuple[Decimal, ...]


def build_feasibility_report(
    observations: tuple[FeasibilityObservation, ...],
) -> dict[str, StrategyFeasibilitySummary]:
    grouped: dict[str, list[FeasibilityObservation]] = defaultdict(list)
    for observation in observations:
        grouped[observation.strategy_id].append(observation)
    result: dict[str, StrategyFeasibilitySummary] = {}
    for strategy_id, items in grouped.items():
        rejection_reasons = Counter(
            item.rejection_reason for item in items if item.rejection_reason is not None
        )
        components = {kind: Decimal("0") for kind in PnLComponentType}
        for item in items:
            for kind, amount in item.pnl_components.items():
                components[kind] += amount
        result[strategy_id] = StrategyFeasibilitySummary(
            observations=len(items),
            approvals=sum(item.approved for item in items),
            median_edge=median(item.edge for item in items),
            median_executable_size=median(item.executable_size for item in items),
            mean_fill_fraction=(
                sum((item.fill_fraction for item in items), Decimal("0")) / len(items)
            ),
            maximum_exposure=max(item.maximum_exposure for item in items),
            rejection_reasons=dict(rejection_reasons),
            pnl_components=components,
            latency_samples=tuple(item.latency_milliseconds for item in items),
        )
    return result
