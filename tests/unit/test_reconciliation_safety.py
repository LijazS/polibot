from datetime import datetime
from decimal import Decimal

from polibot.execution.safety import KillScope, KillSwitchRegistry, RecoveryGate
from polibot.reconciliation import AccountState, DiscrepancyType, ReconciliationEngine


def _state(now: datetime, *, balance: str = "10", orders=frozenset()) -> AccountState:
    return AccountState(
        balances={"pUSD": Decimal(balance)},
        positions={"yes": Decimal("1")},
        open_order_ids=orders,
        fill_ids=frozenset(),
        settlement_ids=frozenset(),
        observed_at=now,
    )


def test_balance_mismatch_is_unhealthy(now: datetime) -> None:
    report = ReconciliationEngine().compare(_state(now), _state(now, balance="9"), now)
    assert not report.healthy
    assert report.discrepancies[0].kind is DiscrepancyType.BALANCE_MISMATCH


def test_explicit_temporary_lag_is_healthy(now: datetime) -> None:
    report = ReconciliationEngine().compare(
        _state(now, orders=frozenset({"o1"})),
        _state(now),
        now,
        permitted_lag_ids=frozenset({"o1"}),
    )
    assert report.healthy
    assert report.discrepancies[0].kind is DiscrepancyType.TEMPORARY_LAG


def test_kill_switches_and_recovery_fail_closed(valid_proposal) -> None:
    switches = KillSwitchRegistry()
    switches.activate(KillScope.MARKET, "market-1", "stale book")
    assert switches.blockers(valid_proposal) == ("market:stale book",)
    recovery = RecoveryGate(durable_state_restored=True, reconciliation_healthy=True)
    allowed, reasons = recovery.permit(valid_proposal)
    assert not allowed and reasons == ("books_not_rebuilt:market-1",)
    recovery.rebuilt_market_ids.add("market-1")
    assert recovery.permit(valid_proposal) == (True, ())
