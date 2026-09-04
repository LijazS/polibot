from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from decimal import ROUND_CEILING, Decimal

from polibot.domain.models import (
    ExecutionPlan,
    MarketSnapshot,
    OpportunityProposal,
    OrderBook,
    OrderIntent,
    PayoffProof,
    Tradability,
)
from polibot.domain.values import SCALE


@dataclass(frozen=True)
class TakerFeeModel:
    rate: Decimal
    source: str
    observed_version: str

    def fee(self, quantity: Decimal, price: Decimal) -> Decimal:
        if self.rate < 0 or not self.source or not self.observed_version:
            raise ValueError("fee model requires non-negative rate and provenance")
        value = quantity * self.rate * price * (Decimal("1") - price)
        return value.quantize(SCALE, rounding=ROUND_CEILING)


@dataclass(frozen=True)
class BinaryArbConfig:
    maximum_quantity: Decimal
    minimum_net_edge: Decimal
    slippage_rate: Decimal
    execution_risk_buffer: Decimal
    proposal_lifetime: timedelta


@dataclass(frozen=True)
class DepthCost:
    quantity: Decimal
    cost: Decimal
    maximum_price: Decimal
    levels_consumed: int


def walk_asks(book: OrderBook, quantity: Decimal) -> DepthCost | None:
    if quantity <= 0:
        raise ValueError("quantity must be positive")
    remaining = quantity
    cost = Decimal("0")
    maximum_price = Decimal("0")
    levels = 0
    for level in book.asks:
        take = min(remaining, level.quantity)
        if take <= 0:
            continue
        cost += take * level.price
        maximum_price = level.price
        levels += 1
        remaining -= take
        if remaining == 0:
            return DepthCost(quantity, cost, maximum_price, levels)
    return None


class BinaryCompleteSetScanner:
    strategy_id = "binary_complete_set"

    def __init__(self, config: BinaryArbConfig, fee_model: TakerFeeModel | None) -> None:
        self._config = config
        self._fee_model = fee_model

    def evaluate(self, snapshot: MarketSnapshot) -> tuple[OpportunityProposal, ...]:
        market = snapshot.market
        if self._fee_model is None or market.tradability is not Tradability.TRADABLE:
            return ()
        token_by_outcome = {token.outcome: token for token in market.outcome_tokens}
        book_by_token = {book.token_id: book for book in snapshot.books}
        if set(token_by_outcome) != {"YES", "NO"}:
            return ()
        yes_book = book_by_token.get(token_by_outcome["YES"].token_id)
        no_book = book_by_token.get(token_by_outcome["NO"].token_id)
        if yes_book is None or no_book is None or not yes_book.asks or not no_book.asks:
            return ()
        candidates = self._candidate_quantities(yes_book, no_book)
        proposals: list[OpportunityProposal] = []
        for quantity in candidates:
            proposal = self._proposal(snapshot, yes_book, no_book, quantity)
            if proposal is not None:
                proposals.append(proposal)
        return tuple(proposals)

    def _candidate_quantities(self, yes_book: OrderBook, no_book: OrderBook) -> tuple[Decimal, ...]:
        yes_total = sum((level.quantity for level in yes_book.asks), Decimal("0"))
        no_total = sum((level.quantity for level in no_book.asks), Decimal("0"))
        limit = min(yes_total, no_total, self._config.maximum_quantity)
        cumulative: set[Decimal] = {limit}
        for book in (yes_book, no_book):
            total = Decimal("0")
            for level in book.asks:
                total += level.quantity
                if total <= limit:
                    cumulative.add(total)
        return tuple(sorted(value for value in cumulative if value > 0))

    def _proposal(
        self,
        snapshot: MarketSnapshot,
        yes_book: OrderBook,
        no_book: OrderBook,
        quantity: Decimal,
    ) -> OpportunityProposal | None:
        market = snapshot.market
        minimum_size = market.minimum_order_size
        if minimum_size is None or quantity < minimum_size:
            return None
        yes = walk_asks(yes_book, quantity)
        no = walk_asks(no_book, quantity)
        if yes is None or no is None or self._fee_model is None:
            return None
        yes_average = yes.cost / quantity
        no_average = no.cost / quantity
        fees = self._fee_model.fee(quantity, yes_average) + self._fee_model.fee(
            quantity, no_average
        )
        raw_cost = yes.cost + no.cost
        slippage = (raw_cost * self._config.slippage_rate).quantize(SCALE, rounding=ROUND_CEILING)
        all_in_cost = raw_cost + fees + slippage + self._config.execution_risk_buffer
        payout = quantity
        edge = payout - all_in_cost
        if edge < self._config.minimum_net_edge:
            return None
        oldest_book = min(yes_book.received_at, no_book.received_at)
        return OpportunityProposal(
            strategy_id=self.strategy_id,
            market_ids=(market.market_id,),
            event_ids=(market.event_id,) if market.event_id else (),
            observed_at=snapshot.captured_at,
            book_received_at=oldest_book,
            expires_at=oldest_book + self._config.proposal_lifetime,
            market_active=market.active and not market.closed,
            market_tradable=market.tradability is Tradability.TRADABLE,
            restriction_passed=not market.restricted,
            token_mapping_valid=True,
            quantity_rules_valid=quantity >= minimum_size,
            fee_model_known=True,
            metadata_validated=True,
            executable_depth_verified=True,
            all_in_cost=all_in_cost,
            modeled_slippage=slippage,
            expected_net_edge=edge,
            payoff_proof=PayoffProof(
                terminal_state_payouts={"YES": payout, "NO": payout},
                worst_case_payout=payout,
            ),
            execution_plan=ExecutionPlan(
                intents=(
                    OrderIntent(
                        market_id=market.market_id,
                        token_id=yes_book.token_id,
                        side="BUY",
                        price=yes.maximum_price,
                        quantity=quantity,
                    ),
                    OrderIntent(
                        market_id=market.market_id,
                        token_id=no_book.token_id,
                        side="BUY",
                        price=no.maximum_price,
                        quantity=quantity,
                    ),
                ),
                maximum_total_cost=all_in_cost,
                maximum_unmatched_exposure=max(yes.cost, no.cost),
            ),
            evidence={
                "quantity": str(quantity),
                "yes_depth_cost": str(yes.cost),
                "no_depth_cost": str(no.cost),
                "yes_levels_consumed": str(yes.levels_consumed),
                "no_levels_consumed": str(no.levels_consumed),
                "fees": str(fees),
                "slippage": str(slippage),
                "execution_risk_buffer": str(self._config.execution_risk_buffer),
                "fee_source": self._fee_model.source,
                "fee_version": self._fee_model.observed_version,
            },
        )
