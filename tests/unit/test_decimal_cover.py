from decimal import Decimal

from polibot.optimizer import PayoffInstrument, solve_minimum_cost_cover


def test_decimal_solver_finds_lower_cost_cover_without_float() -> None:
    instruments = (
        PayoffInstrument("yes-a", Decimal("0.20"), (Decimal("1"), Decimal("0"))),
        PayoffInstrument("yes-b", Decimal("0.30"), (Decimal("0"), Decimal("1"))),
        PayoffInstrument("no-a", Decimal("0.80"), (Decimal("0"), Decimal("1"))),
        PayoffInstrument("no-b", Decimal("0.70"), (Decimal("1"), Decimal("0"))),
    )
    solution = solve_minimum_cost_cover(("a", "b"), instruments, Decimal("1"))
    assert solution is not None
    assert solution.quantities == {"yes-a": Decimal("1"), "yes-b": Decimal("1")}
    assert solution.cost == Decimal("0.50")
    assert min(solution.state_payouts) == Decimal("1")


def test_solver_rejects_incomplete_payoff_dimension() -> None:
    instruments = (PayoffInstrument("bad", Decimal("1"), (Decimal("1"),)),)
    try:
        solve_minimum_cost_cover(("a", "b"), instruments, Decimal("1"))
    except ValueError as exc:
        assert "dimensions" in str(exc)
    else:
        raise AssertionError("invalid payoff dimensions must fail")
