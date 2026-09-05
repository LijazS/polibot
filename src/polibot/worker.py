from __future__ import annotations

import asyncio
import hashlib
import json
import random
import shutil
import signal
from collections.abc import Callable
from contextlib import suppress
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any
from uuid import uuid4

import httpx
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker

from polibot.config import ExecutionMode, Settings
from polibot.discovery import DiscoveryService, GammaDiscoveryClient
from polibot.domain.models import Market, MarketSnapshot, Tradability
from polibot.execution import ExecutionRejected
from polibot.execution.paper import PaperExecutionSimulator, SimulationStatus
from polibot.market_data import ClobSnapshotClient, MarketChannelClient
from polibot.market_data.messages import (
    BestBidAskMessage,
    BookMessage,
    LastTradeMessage,
    NormalizedMarketMessage,
    PriceChangeMessage,
    TickSizeChangeMessage,
)
from polibot.monitoring import PolibotMetrics, configure_logging
from polibot.orderbook import BookState, InvalidBookUpdate, NormalizedOrderBook
from polibot.risk import DeterministicRiskEngine, RiskContext, RiskLimits
from polibot.storage import (
    BatchedPostgresRecorder,
    MarketSelection,
    RecordedEnvelope,
    RecorderBackpressure,
    RecordKind,
    WorkerStateStore,
    WorkerStatus,
    build_engine,
    canonical_payload,
)
from polibot.strategies.binary_arb import BinaryArbConfig, BinaryCompleteSetScanner, TakerFeeModel


class UnsafeWorkerConfiguration(RuntimeError):
    pass


def _configuration_fingerprint(settings: Settings) -> str:
    safe_values = {
        key: value
        for key, value in settings.model_dump(mode="json").items()
        if key
        not in {
            "database_url",
            "gamma_base_url",
            "clob_base_url",
            "clob_websocket_url",
        }
    }
    encoded = json.dumps(safe_values, sort_keys=True, separators=(",", ":")).encode()
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def select_binary_markets(
    markets: tuple[Market, ...], maximum: int
) -> tuple[tuple[Market, ...], tuple[MarketSelection, ...]]:
    selected: list[Market] = []
    decisions: list[MarketSelection] = []
    for market in markets:
        reason = "selected"
        choose = True
        if market.tradability is not Tradability.TRADABLE:
            choose, reason = False, f"tradability_{market.tradability.value}"
        elif market.neg_risk:
            choose, reason = False, "negrisk_requires_validated_event_structure"
        elif market.condition_id is None or len(market.outcome_tokens) != 2:
            choose, reason = False, "invalid_binary_identity"
        elif len(selected) >= maximum:
            choose, reason = False, "selection_limit"
        if choose:
            selected.append(market)
        decisions.append(
            MarketSelection(
                market_id=market.market_id,
                condition_id=market.condition_id,
                selected=choose,
                reason=reason,
            )
        )
    return tuple(selected), tuple(decisions)


class ContinuousPaperWorker:
    def __init__(
        self,
        *,
        settings: Settings,
        discovery: DiscoveryService,
        discovery_client: GammaDiscoveryClient,
        snapshots: ClobSnapshotClient,
        market_channel: MarketChannelClient,
        state_store: WorkerStateStore,
        recorder: BatchedPostgresRecorder,
        metrics: PolibotMetrics,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        if settings.execution_mode not in {ExecutionMode.PAPER, ExecutionMode.SHADOW}:
            raise UnsafeWorkerConfiguration("continuous worker supports PAPER/SHADOW only")
        if settings.live_trading_enabled:
            raise UnsafeWorkerConfiguration("live trading must be disabled for the worker")
        self.settings = settings
        self.discovery = discovery
        self.discovery_client = discovery_client
        self.snapshots = snapshots
        self.market_channel = market_channel
        self.state_store = state_store
        self.recorder = recorder
        self.metrics = metrics
        self.clock = clock
        now = clock()
        self.status = WorkerStatus(
            worker_id=settings.worker_id,
            run_id=str(uuid4()),
            started_at=now,
            last_heartbeat_at=now,
            execution_mode=settings.execution_mode.value,
            application_version=settings.application_version,
            git_sha=settings.git_sha,
            paper_initial_capital=settings.paper_initial_capital,
            paper_current_capital=settings.paper_initial_capital,
        )
        self.books: dict[str, NormalizedOrderBook] = {}
        self.markets: dict[str, Market] = {}
        self.market_by_token: dict[str, Market] = {}
        self.fees: dict[str, TakerFeeModel] = {}
        self._ordinal = 0
        self._stop = asyncio.Event()
        self._heartbeat_task: asyncio.Task[None] | None = None
        self._risk = DeterministicRiskEngine(
            RiskLimits(
                stale_book_after=timedelta(seconds=settings.stale_book_after_seconds),
                minimum_net_edge=settings.minimum_net_edge,
                maximum_order_notional=settings.maximum_order_notional,
                maximum_global_exposure=settings.maximum_global_exposure,
                maximum_strategy_exposure=settings.maximum_strategy_exposure,
                maximum_market_exposure=settings.maximum_market_exposure,
                maximum_event_exposure=settings.maximum_event_exposure,
                maximum_unmatched_exposure=settings.maximum_unmatched_exposure,
                maximum_unmatched_duration=timedelta(
                    seconds=settings.maximum_unmatched_duration_seconds
                ),
                maximum_slippage=settings.maximum_slippage,
            )
        )
        self._simulator = PaperExecutionSimulator(
            settings.execution_mode,
            timedelta(milliseconds=settings.paper_execution_latency_ms),
        )

    def request_stop(self) -> None:
        self._stop.set()

    def connection_changed(self, connected: bool) -> None:
        self.status.websocket_connected = connected
        self.metrics.websocket_connected.set(1 if connected else 0)
        if not connected:
            self.status.ready = False
            for book in self.books.values():
                book.mark_disconnected()

    def reconnecting(self) -> None:
        self.status.reconnect_count += 1
        self.metrics.market_data_reconnects.inc()

    async def run(self) -> None:
        await self.recorder.start()
        await self.state_store.start_run(
            self.status,
            configuration_fingerprint=_configuration_fingerprint(self.settings),
            strategies_json=canonical_payload(
                {
                    "binary_complete_set": True,
                    "vanilla_negrisk": False,
                    "holding_rewards_observation": False,
                }
            ),
            selection_policy_json=canonical_payload(
                {
                    "order": "volume24hr_desc",
                    "maximum_binary_markets": self.settings.worker_max_binary_markets,
                    "maximum_negrisk_events": self.settings.worker_max_negrisk_events,
                }
            ),
        )
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop(), name="worker-heartbeat")
        try:
            while not self._stop.is_set():
                try:
                    await self._collection_cycle()
                except asyncio.CancelledError:
                    raise
                except Exception as exc:
                    self.status.current_status = "degraded"
                    self.status.ready = False
                    self.status.last_error = f"{type(exc).__name__}: {exc}"[:2000]
                    await self._save_heartbeat()
                    try:
                        await asyncio.wait_for(self._stop.wait(), timeout=5)
                    except TimeoutError:
                        continue
        finally:
            self.status.current_status = "stopping"
            self.status.ready = False
            self.status.websocket_connected = False
            if self._heartbeat_task is not None:
                self._heartbeat_task.cancel()
                await asyncio.gather(self._heartbeat_task, return_exceptions=True)
            try:
                await self.recorder.close()
            finally:
                now = self.clock()
                self.status.last_heartbeat_at = now
                await self.state_store.save_heartbeat(self.status)
                await self.state_store.stop_run(self.status.run_id, now)

    async def _collection_cycle(self) -> None:
        now = self.clock()
        batch = await self.discovery.discover_market_page(
            observed_at=now,
            limit=self.settings.worker_discovery_page_size,
        )
        selected, selections = select_binary_markets(
            batch.markets, self.settings.worker_max_binary_markets
        )
        failure_selections = tuple(
            MarketSelection(item.market_id, None, False, f"invalid_metadata:{item.reason}"[:100])
            for item in batch.failures
        )
        await self.state_store.record_selections(
            self.status.run_id, now, selections + failure_selections
        )
        self.status.markets_discovered = len(batch.markets) + len(batch.failures)
        self.status.markets_selected = len(selected)
        self.metrics.markets_discovered.set(self.status.markets_discovered)
        self.metrics.markets_selected.set(self.status.markets_selected)
        self.metrics.markets_rejected.set(
            self.status.markets_discovered - self.status.markets_selected
        )
        if not selected:
            raise RuntimeError("discovery selected no supported binary markets")
        await self._prepare_markets(selected, now)
        asset_ids = tuple(self.market_by_token)
        self.status.markets_subscribed = len(asset_ids)
        self.metrics.active_subscriptions.set(len(asset_ids))
        self.status.current_status = "running"
        try:
            async with asyncio.timeout(self.settings.worker_market_refresh_seconds):
                async for message in self.market_channel.stream(asset_ids):
                    if self._stop.is_set():
                        break
                    await self._process_message(message, self.clock())
        except TimeoutError:
            return

    async def _prepare_markets(self, markets: tuple[Market, ...], observed_at: datetime) -> None:
        self.books.clear()
        self.markets.clear()
        self.market_by_token.clear()
        self.fees.clear()
        for market in markets:
            if market.condition_id is None:
                continue
            try:
                info = await self.discovery_client.clob_market_info(market.condition_id)
                expected_tokens = {token.outcome: token.token_id for token in market.outcome_tokens}
                observed_tokens = {token.outcome.upper(): token.token_id for token in info.tokens}
                if observed_tokens != expected_tokens:
                    raise ValueError("CLOB market info token mapping disagrees with verification")
                if (
                    market.minimum_tick_size != info.minimum_tick_size
                    or market.minimum_order_size != info.minimum_order_size
                ):
                    raise ValueError("Gamma and CLOB tick/minimum metadata disagree")
                rate = (
                    info.fee_details.rate
                    if info.fee_details is not None
                    else Decimal(info.taker_base_fee_bps) / Decimal("10000")
                )
                fee = TakerFeeModel(rate, "clob_market_info", observed_at.isoformat())
                self.fees[market.market_id] = fee
                self.markets[market.market_id] = market
                await self._record(
                    RecordKind.MARKET_METADATA,
                    market.model_dump(mode="json"),
                    market.market_id,
                    None,
                    observed_at,
                    observed_at,
                )
                await self._record(
                    RecordKind.FEE_METADATA,
                    {
                        "condition_id": market.condition_id,
                        "rate": rate,
                        "maker_base_fee_bps": info.maker_base_fee_bps,
                        "taker_base_fee_bps": info.taker_base_fee_bps,
                        "source": "clob_market_info",
                    },
                    market.market_id,
                    None,
                    observed_at,
                    observed_at,
                )
                for token in market.outcome_tokens:
                    book = NormalizedOrderBook(
                        market.condition_id, token.token_id, info.minimum_tick_size
                    )
                    self.books[token.token_id] = book
                    self.market_by_token[token.token_id] = market
                    snapshot = await self.snapshots.get_book(token.token_id)
                    received_at = self.clock()
                    book.apply_snapshot(snapshot, received_at)
                    await self._record_message(snapshot, received_at)
                    self.metrics.snapshot_recoveries.inc()
            except (ValueError, InvalidBookUpdate, RecorderBackpressure) as exc:
                self.status.last_error = f"market {market.market_id} excluded: {exc}"[:2000]
                for token in market.outcome_tokens:
                    self.books.pop(token.token_id, None)
                    self.market_by_token.pop(token.token_id, None)
                self.markets.pop(market.market_id, None)
                self.fees.pop(market.market_id, None)
        active_market_ids = {market.market_id for market in self.market_by_token.values()}
        self.status.markets_selected = len(active_market_ids)
        self.metrics.markets_selected.set(self.status.markets_selected)
        if not self.books:
            raise RuntimeError("no selected market produced authoritative books and fees")
        self._refresh_book_health(self.clock())

    async def _process_message(
        self, message: NormalizedMarketMessage, received_at: datetime
    ) -> None:
        await self._record_message(message, received_at)
        self.status.messages_received += 1
        self.metrics.market_messages.inc()
        affected: set[str] = set()
        try:
            if isinstance(message, BookMessage):
                affected.add(message.asset_id)
                book = self.books.get(message.asset_id)
                if book is not None:
                    book.apply_snapshot(message, received_at)
            elif isinstance(message, PriceChangeMessage):
                affected.update(change.asset_id for change in message.price_changes)
                for token_id in affected:
                    book = self.books.get(token_id)
                    if book is not None:
                        book.apply_price_change(message, received_at)
            elif isinstance(message, TickSizeChangeMessage):
                affected.add(message.asset_id)
                book = self.books.get(message.asset_id)
                if book is not None:
                    book.apply_tick_change(message, received_at)
            elif isinstance(message, LastTradeMessage):
                affected.add(message.asset_id)
                book = self.books.get(message.asset_id)
                if book is not None:
                    book.apply_last_trade(message, received_at)
            elif isinstance(message, BestBidAskMessage):
                affected.add(message.asset_id)
        except InvalidBookUpdate:
            for token_id in affected:
                await self._recover_book(token_id)
        self._refresh_book_health(received_at)
        affected_markets = {
            self.market_by_token[token].market_id
            for token in affected
            if token in self.market_by_token
        }
        for market_id in affected_markets:
            await self._evaluate_market(market_id, received_at)

    async def _recover_book(self, token_id: str) -> None:
        book = self.books.get(token_id)
        if book is None:
            return
        book.invalidate()
        snapshot = await self.snapshots.get_book(token_id)
        received_at = self.clock()
        book.apply_snapshot(snapshot, received_at)
        await self._record_message(snapshot, received_at)
        self.metrics.snapshot_recoveries.inc()

    def _refresh_book_health(self, now: datetime) -> None:
        maximum_age = timedelta(seconds=self.settings.stale_book_after_seconds)
        for book in self.books.values():
            book.refresh_staleness(now, maximum_age)
        healthy = sum(book.state is BookState.READY for book in self.books.values())
        self.status.books_healthy = healthy
        self.status.books_stale = len(self.books) - healthy
        self.metrics.active_books.set(len(self.books))
        self.metrics.healthy_books.set(healthy)
        self.metrics.stale_books.set(self.status.books_stale)
        self.status.ready = (
            self.status.websocket_connected
            and healthy >= 2
            and not self.recorder.degraded
            and self.status.markets_selected > 0
        )

    async def _evaluate_market(self, market_id: str, now: datetime) -> None:
        market = self.markets.get(market_id)
        fee = self.fees.get(market_id)
        if market is None or fee is None or not self.status.ready:
            return
        token_books = tuple(
            self.books[token.token_id].snapshot()
            for token in market.outcome_tokens
            if token.token_id in self.books and self.books[token.token_id].state is BookState.READY
        )
        if len(token_books) != 2:
            return
        snapshot = MarketSnapshot(market=market, books=token_books, captured_at=now)
        scanner = BinaryCompleteSetScanner(
            BinaryArbConfig(
                maximum_quantity=self.settings.worker_maximum_quantity,
                minimum_net_edge=self.settings.minimum_net_edge,
                slippage_rate=self.settings.worker_slippage_rate,
                execution_risk_buffer=self.settings.worker_execution_risk_buffer,
                proposal_lifetime=timedelta(milliseconds=self.settings.worker_proposal_lifetime_ms),
            ),
            fee,
        )
        self.status.strategy_evaluations += 1
        self.status.last_strategy_cycle = now
        self.metrics.strategy_observations.labels(strategy=scanner.strategy_id).inc()
        for proposal in scanner.evaluate(snapshot):
            self.status.opportunities_detected += 1
            self.metrics.proposals.labels(strategy=proposal.strategy_id).inc()
            await self._record(
                RecordKind.PROPOSAL,
                proposal.model_dump(mode="json"),
                market.market_id,
                None,
                proposal.observed_at,
                now,
            )
            context = RiskContext(
                current_global_exposure=Decimal("0"),
                system_healthy=self.status.ready and not self.recorder.degraded,
            )
            decision = self._risk.evaluate(proposal, context, now)
            reason = (
                "none"
                if decision.approved
                else ",".join(item.value for item in decision.rejection_reasons)
            )
            self.metrics.risk_decisions.labels(
                outcome="approved" if decision.approved else "rejected", reason=reason
            ).inc()
            await self._record(
                RecordKind.RISK_DECISION,
                decision.model_dump(mode="json"),
                market.market_id,
                None,
                now,
                now,
            )
            if decision.approval is None:
                continue
            self.status.risk_approvals += 1
            try:
                result = self._simulator.execute(proposal, decision.approval, token_books, now)
            except ExecutionRejected as exc:
                self.status.last_error = f"paper execution rejected: {exc}"[:2000]
                continue
            self.status.paper_executions += 1
            self.metrics.simulated_executions.labels(
                mode=self.settings.execution_mode.value, status=result.status.value
            ).inc()
            for fill in result.fills:
                self.metrics.simulated_fills.labels(
                    status="filled" if fill.quantity > 0 else "unfilled"
                ).inc()
            await self._record(
                RecordKind.SIMULATED_EXECUTION,
                {
                    "proposal_id": result.proposal_id,
                    "status": result.status.value,
                    "fills": [
                        {
                            "fill_id": fill.fill_id,
                            "intent_id": fill.intent_id,
                            "token_id": fill.token_id,
                            "quantity": fill.quantity,
                            "cost": fill.cost,
                            "average_price": fill.average_price,
                        }
                        for fill in result.fills
                    ],
                    "unmatched_exposure": result.unmatched_exposure,
                    "unmatched_duration_seconds": Decimal(
                        str(result.unmatched_duration.total_seconds())
                    ),
                    "assumptions": list(result.assumptions),
                    "execution_latency_ms": self.settings.paper_execution_latency_ms,
                },
                market.market_id,
                None,
                now,
                now,
            )
            if result.status is SimulationStatus.COMPLETE:
                await self._account_complete(proposal, market.market_id, now)

    async def _account_complete(self, proposal: Any, market_id: str, now: datetime) -> None:
        fees = Decimal(proposal.evidence.get("fees", "0"))
        slippage = Decimal(proposal.evidence.get("slippage", "0"))
        risk_buffer = Decimal(proposal.evidence.get("execution_risk_buffer", "0"))
        gross = proposal.expected_net_edge + fees + slippage + risk_buffer
        self.status.paper_gross_pnl += gross
        self.status.paper_fees += fees
        self.status.paper_slippage += slippage
        self.status.paper_net_pnl += proposal.expected_net_edge
        self.status.paper_current_capital = (
            self.status.paper_initial_capital + self.status.paper_net_pnl
        )
        self.metrics.pnl.labels(strategy=proposal.strategy_id, component="gross_edge").set(
            float(self.status.paper_gross_pnl)
        )
        self.metrics.pnl.labels(strategy=proposal.strategy_id, component="fees").set(
            float(self.status.paper_fees)
        )
        self.metrics.pnl.labels(strategy=proposal.strategy_id, component="slippage").set(
            float(self.status.paper_slippage)
        )
        self.metrics.pnl.labels(strategy=proposal.strategy_id, component="net_paper").set(
            float(self.status.paper_net_pnl)
        )
        for component, amount in (
            ("gross_structural_edge", gross),
            ("fees", -fees),
            ("slippage", -slippage),
            ("execution_risk_buffer", -risk_buffer),
            ("net_paper_pnl", proposal.expected_net_edge),
        ):
            await self._record(
                RecordKind.PNL_COMPONENT,
                {
                    "strategy": proposal.strategy_id,
                    "proposal_id": proposal.proposal_id,
                    "component": component,
                    "amount": amount,
                },
                market_id,
                None,
                now,
                now,
            )

    async def _record_message(
        self, message: NormalizedMarketMessage, received_at: datetime
    ) -> None:
        market = self.market_by_token.get(getattr(message, "asset_id", ""))
        market_id = market.market_id if market is not None else getattr(message, "market", None)
        token_id = getattr(message, "asset_id", None)
        if isinstance(message, PriceChangeMessage):
            token_id = None
        kind = (
            RecordKind.BOOK_SNAPSHOT
            if isinstance(message, BookMessage)
            else RecordKind.BOOK_CHANGE
            if isinstance(message, (PriceChangeMessage, TickSizeChangeMessage, BestBidAskMessage))
            else RecordKind.TRADE
        )
        timestamp = datetime(1970, 1, 1, tzinfo=UTC) + timedelta(
            milliseconds=int(Decimal(message.timestamp))
        )
        await self._record(
            kind,
            {
                "schema_version": "polymarket-market-channel-2026-09-05",
                "message": message.model_dump(mode="json"),
            },
            market_id,
            token_id,
            timestamp,
            received_at,
        )

    async def _record(
        self,
        kind: RecordKind,
        payload: dict[str, object],
        market_id: str | None,
        token_id: str | None,
        source_timestamp: datetime,
        received_at: datetime,
    ) -> None:
        self._ordinal += 1
        await self.recorder.append(
            RecordedEnvelope(
                ordinal=self._ordinal,
                kind=kind,
                market_id=market_id,
                token_id=token_id,
                source_timestamp=source_timestamp,
                received_at=received_at,
                payload_json=canonical_payload(payload),
            )
        )

    async def _heartbeat_loop(self) -> None:
        while True:
            try:
                await self._save_heartbeat()
            except Exception as exc:
                self.status.database_errors += 1
                self.status.current_status = "degraded"
                self.status.ready = False
                self.status.last_error = f"heartbeat persistence failed: {exc}"[:2000]
            await asyncio.sleep(self.settings.worker_heartbeat_seconds)

    async def _save_heartbeat(self) -> None:
        now = self.clock()
        self._refresh_book_health(now) if self.books else None
        self.status.last_heartbeat_at = now
        self.status.recorder_queue_depth = self.recorder.queue_depth
        self.status.recorder_dropped_events = self.recorder.dropped_events
        self.status.database_errors = max(
            self.status.database_errors, self.recorder.database_errors
        )
        disk = shutil.disk_usage("/")
        self.status.disk_used_percent = (
            Decimal(disk.used) * Decimal("100") / Decimal(disk.total)
        ).quantize(Decimal("0.001"))
        self.status.database_size_bytes = await self.state_store.database_size_bytes()
        self.metrics.recorder_queue_depth.set(self.status.recorder_queue_depth)
        self.metrics.recorder_batches.set(self.recorder.batches_written)
        self.metrics.recorder_drops.set(self.status.recorder_dropped_events)
        self.metrics.database_errors.set(self.status.database_errors)
        self.metrics.disk_used_percent.set(float(self.status.disk_used_percent))
        self.metrics.database_size_bytes.set(self.status.database_size_bytes)
        if self.status.disk_used_percent >= Decimal("85"):
            self.status.current_status = "degraded"
            self.status.ready = False
            self.status.last_error = "disk usage reached the 85% safety threshold"
        await self.state_store.save_heartbeat(self.status)


async def run_worker(settings: Settings | None = None) -> None:
    runtime_settings = settings or Settings()
    if (
        runtime_settings.execution_mode is ExecutionMode.LIVE
        or runtime_settings.live_trading_enabled
    ):
        raise UnsafeWorkerConfiguration("worker refuses LIVE configuration")
    configure_logging(runtime_settings.log_level)
    engine: AsyncEngine = build_engine(runtime_settings.database_url)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    timeout = httpx.Timeout(connect=5.0, read=15.0, write=5.0, pool=5.0)
    http_client = httpx.AsyncClient(timeout=timeout)
    discovery_client = GammaDiscoveryClient(
        http_client,
        gamma_base_url=runtime_settings.gamma_base_url,
        clob_base_url=runtime_settings.clob_base_url,
    )
    metrics = PolibotMetrics()
    recorder = BatchedPostgresRecorder(
        sessions,
        batch_size=runtime_settings.worker_recorder_batch_size,
        flush_seconds=runtime_settings.worker_recorder_flush_seconds,
        queue_size=runtime_settings.worker_recorder_queue_size,
    )
    worker_ref: list[ContinuousPaperWorker] = []
    channel = MarketChannelClient(
        url=runtime_settings.clob_websocket_url,
        jitter=lambda: random.uniform(0, 0.25),
        connection_changed=lambda connected: worker_ref[0].connection_changed(connected),
        reconnecting=lambda: worker_ref[0].reconnecting(),
    )
    worker = ContinuousPaperWorker(
        settings=runtime_settings,
        discovery=DiscoveryService(discovery_client),
        discovery_client=discovery_client,
        snapshots=ClobSnapshotClient(http_client, runtime_settings.clob_base_url),
        market_channel=channel,
        state_store=WorkerStateStore(sessions),
        recorder=recorder,
        metrics=metrics,
    )
    worker_ref.append(worker)
    loop = asyncio.get_running_loop()
    for name in ("SIGINT", "SIGTERM"):
        if hasattr(signal, name):
            with suppress(NotImplementedError):
                loop.add_signal_handler(getattr(signal, name), worker.request_stop)
    try:
        await worker.run()
    finally:
        await http_client.aclose()
        await engine.dispose()


def main() -> None:
    asyncio.run(run_worker())


if __name__ == "__main__":
    main()
