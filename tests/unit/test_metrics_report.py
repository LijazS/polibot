from decimal import Decimal

from polibot.backtest import FeasibilityObservation, build_feasibility_report
from polibot.domain.models import PnLComponentType
from polibot.monitoring import PolibotMetrics


def test_metrics_are_prometheus_compatible() -> None:
    metrics = PolibotMetrics()
    metrics.proposals.labels(strategy="binary").inc()
    output = metrics.render().decode()
    assert 'polibot_proposals_total{strategy="binary"} 1.0' in output


def test_feasibility_report_separates_strategy_and_pnl_components() -> None:
    report = build_feasibility_report(
        (
            FeasibilityObservation(
                strategy_id="binary",
                edge=Decimal("0.02"),
                executable_size=Decimal("10"),
                approved=True,
                rejection_reason=None,
                fill_fraction=Decimal("0.5"),
                maximum_exposure=Decimal("5"),
                latency_milliseconds=Decimal("100"),
                pnl_components={PnLComponentType.FEES: Decimal("-0.1")},
            ),
        )
    )
    assert set(report) == {"binary"}
    assert report["binary"].pnl_components[PnLComponentType.FEES] == Decimal("-0.1")
    assert report["binary"].mean_fill_fraction == Decimal("0.5")
