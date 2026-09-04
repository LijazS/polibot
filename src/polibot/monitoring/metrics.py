from __future__ import annotations

from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram, generate_latest


class PolibotMetrics:
    def __init__(self) -> None:
        self.registry = CollectorRegistry()
        self.market_messages = Counter(
            "polibot_market_messages_total",
            "Normalized market messages",
            registry=self.registry,
        )
        self.active_subscriptions = Gauge(
            "polibot_active_subscriptions",
            "Current public market-data subscriptions",
            registry=self.registry,
        )
        self.market_data_reconnects = Counter(
            "polibot_market_data_reconnects_total",
            "Market-data reconnect attempts",
            registry=self.registry,
        )
        self.snapshot_recoveries = Counter(
            "polibot_snapshot_recoveries_total",
            "Authoritative snapshot recoveries",
            registry=self.registry,
        )
        self.market_processing_seconds = Histogram(
            "polibot_market_processing_seconds",
            "Normalized market-message processing time",
            registry=self.registry,
        )
        self.proposals = Counter(
            "polibot_proposals_total",
            "Strategy proposals",
            ["strategy"],
            registry=self.registry,
        )
        self.strategy_observations = Counter(
            "polibot_strategy_observations_total",
            "Strategy evaluation observations",
            ["strategy"],
            registry=self.registry,
        )
        self.risk_decisions = Counter(
            "polibot_risk_decisions_total",
            "Risk decisions",
            ["outcome", "reason"],
            registry=self.registry,
        )
        self.simulated_executions = Counter(
            "polibot_simulated_executions_total",
            "Paper and shadow executions",
            ["mode", "status"],
            registry=self.registry,
        )
        self.simulated_fills = Counter(
            "polibot_simulated_fills_total",
            "Simulated fill outcomes",
            ["status"],
            registry=self.registry,
        )
        self.simulated_slippage = Gauge(
            "polibot_simulated_slippage",
            "Latest modeled simulated slippage",
            registry=self.registry,
        )
        self.unmatched_exposure = Gauge(
            "polibot_unmatched_exposure",
            "Current unmatched modeled exposure",
            registry=self.registry,
        )
        self.unmatched_duration_seconds = Gauge(
            "polibot_unmatched_duration_seconds",
            "Current unmatched modeled duration",
            registry=self.registry,
        )
        self.current_exposure = Gauge(
            "polibot_current_exposure",
            "Current modeled collateral exposure",
            registry=self.registry,
        )
        self.stale_books = Gauge(
            "polibot_stale_books",
            "Books currently stale or invalid",
            registry=self.registry,
        )
        self.reconciliation_mismatches = Gauge(
            "polibot_reconciliation_mismatches",
            "Current reconciliation mismatch count",
            registry=self.registry,
        )
        self.pnl = Gauge(
            "polibot_pnl_component",
            "Current separated P&L component",
            ["strategy", "component"],
            registry=self.registry,
        )

    def render(self) -> bytes:
        return generate_latest(self.registry)
