from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from itertools import combinations


@dataclass(frozen=True)
class PayoffInstrument:
    instrument_id: str
    unit_cost: Decimal
    state_payouts: tuple[Decimal, ...]


@dataclass(frozen=True)
class CoverSolution:
    quantities: dict[str, Decimal]
    state_payouts: tuple[Decimal, ...]
    cost: Decimal


def _solve(matrix: list[list[Decimal]], target: list[Decimal]) -> list[Decimal] | None:
    size = len(target)
    augmented = [[*row, target[index]] for index, row in enumerate(matrix)]
    for column in range(size):
        pivot = next((row for row in range(column, size) if augmented[row][column] != 0), None)
        if pivot is None:
            return None
        augmented[column], augmented[pivot] = augmented[pivot], augmented[column]
        divisor = augmented[column][column]
        augmented[column] = [value / divisor for value in augmented[column]]
        for row in range(size):
            if row == column:
                continue
            factor = augmented[row][column]
            augmented[row] = [
                value - factor * pivot_value
                for value, pivot_value in zip(augmented[row], augmented[column], strict=True)
            ]
    return [augmented[row][-1] for row in range(size)]


def solve_minimum_cost_cover(
    state_ids: tuple[str, ...],
    instruments: tuple[PayoffInstrument, ...],
    target_payout: Decimal,
) -> CoverSolution | None:
    if not state_ids or target_payout <= 0:
        raise ValueError("states and a positive target payout are required")
    state_count = len(state_ids)
    if any(
        instrument.unit_cost < 0 or len(instrument.state_payouts) != state_count
        for instrument in instruments
    ):
        raise ValueError("instrument cost/payoff dimensions are invalid")
    best: CoverSolution | None = None
    for basis in combinations(instruments, state_count):
        matrix = [
            [basis[column].state_payouts[row] for column in range(state_count)]
            for row in range(state_count)
        ]
        quantities = _solve(matrix, [target_payout] * state_count)
        if quantities is None or any(quantity < 0 for quantity in quantities):
            continue
        payouts = tuple(
            sum(
                (
                    quantities[column] * basis[column].state_payouts[row]
                    for column in range(state_count)
                ),
                Decimal("0"),
            )
            for row in range(state_count)
        )
        if min(payouts) < target_payout:
            continue
        cost = sum(
            (
                quantity * instrument.unit_cost
                for quantity, instrument in zip(quantities, basis, strict=True)
            ),
            Decimal("0"),
        )
        solution = CoverSolution(
            quantities={
                instrument.instrument_id: quantity
                for instrument, quantity in zip(basis, quantities, strict=True)
                if quantity > 0
            },
            state_payouts=payouts,
            cost=cost,
        )
        if best is None or (solution.cost, sorted(solution.quantities)) < (
            best.cost,
            sorted(best.quantities),
        ):
            best = solution
    return best
