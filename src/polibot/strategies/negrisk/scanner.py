from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import ROUND_CEILING, Decimal

from polibot.domain.models import (
    ExecutionPlan,
    OpportunityProposal,
    OrderBook,
    OrderIntent,
    PayoffProof,
)
from polibot.domain.values import SCALE
from polibot.optimizer import PayoffInstrument, solve_minimum_cost_cover
from polibot.strategies.binary_arb import TakerFeeModel, walk_asks


@dataclass(frozen=True)
class NegRiskOutcome:
    outcome_id: str
    market_id: str
    yes_token_id: str
    no_token_id: str


@dataclass(frozen=True)
class NegRiskStructure:
    event_id: str
    outcomes: tuple[NegRiskOutcome, ...]
    structure_verified: bool
    augmented: bool
    other_outcome_defined: bool
    outcome_set_closed: bool

    @property
    def supported(self) -> bool:
        ids = [outcome.outcome_id for outcome in self.outcomes]
        tokens = [
            token
            for outcome in self.outcomes
            for token in (outcome.yes_token_id, outcome.no_token_id)
        ]
        return (
            self.structure_verified
            and not self.augmented
            and self.other_outcome_defined
            and self.outcome_set_closed
            and len(ids) >= 2
            and len(ids) == len(set(ids))
            and len(tokens) == len(set(tokens))
        )


@dataclass(frozen=True)
class NegRiskConfig:
    target_payout: Decimal
    minimum_net_edge: Decimal
    slippage_rate: Decimal
    execution_risk_buffer: Decimal
    proposal_lifetime: timedelta


class NegRiskScanner:
    strategy_id = "vanilla_negrisk"

    def __init__(self, config: NegRiskConfig, fee_model: TakerFeeModel | None) -> None:
        self._config = config
        self._fee_model = fee_model

    def evaluate(
        self,
        structure: NegRiskStructure,
        books: tuple[OrderBook, ...],
        observed_at: datetime,
    ) -> tuple[OpportunityProposal, ...]:
        if not structure.supported or self._fee_model is None:
            return ()
        book_by_token = {book.token_id: book for book in books}
        instruments: list[PayoffInstrument] = []
        execution_prices: dict[str, Decimal] = {}
        outcome_count = len(structure.outcomes)
        for outcome_index, outcome in enumerate(structure.outcomes):
            for token_id, is_yes in (
                (outcome.yes_token_id, True),
                (outcome.no_token_id, False),
            ):
                book = book_by_token.get(token_id)
                if book is None:
                    return ()
                depth = walk_asks(book, self._config.target_payout)
                if depth is None:
                    return ()
                payouts = tuple(
                    Decimal("1") if (state == outcome_index) is is_yes else Decimal("0")
                    for state in range(outcome_count)
                )
                instruments.append(PayoffInstrument(token_id, depth.cost / depth.quantity, payouts))
                execution_prices[token_id] = depth.maximum_price
        solution = solve_minimum_cost_cover(
            tuple(outcome.outcome_id for outcome in structure.outcomes),
            tuple(instruments),
            self._config.target_payout,
        )
        if solution is None:
            return ()
        instrument_by_id = {item.instrument_id: item for item in instruments}
        fees = sum(
            (
                self._fee_model.fee(quantity, instrument_by_id[token_id].unit_cost)
                for token_id, quantity in solution.quantities.items()
            ),
            Decimal("0"),
        )
        slippage = (solution.cost * self._config.slippage_rate).quantize(
            SCALE, rounding=ROUND_CEILING
        )
        all_in = solution.cost + fees + slippage + self._config.execution_risk_buffer
        edge = min(solution.state_payouts) - all_in
        if edge < self._config.minimum_net_edge:
            return ()
        oldest_book = min(book.received_at for book in books)
        intents = tuple(
            OrderIntent(
                market_id=next(
                    outcome.market_id
                    for outcome in structure.outcomes
                    if token_id in {outcome.yes_token_id, outcome.no_token_id}
                ),
                token_id=token_id,
                side="BUY",
                price=execution_prices[token_id],
                quantity=quantity,
            )
            for token_id, quantity in sorted(solution.quantities.items())
        )
        proposal = OpportunityProposal(
            strategy_id=self.strategy_id,
            market_ids=tuple(outcome.market_id for outcome in structure.outcomes),
            event_ids=(structure.event_id,),
            observed_at=observed_at,
            book_received_at=oldest_book,
            expires_at=oldest_book + self._config.proposal_lifetime,
            market_active=True,
            market_tradable=True,
            restriction_passed=True,
            token_mapping_valid=True,
            quantity_rules_valid=True,
            fee_model_known=True,
            metadata_validated=structure.supported,
            executable_depth_verified=True,
            all_in_cost=all_in,
            modeled_slippage=slippage,
            expected_net_edge=edge,
            payoff_proof=PayoffProof(
                terminal_state_payouts={
                    outcome.outcome_id: payout
                    for outcome, payout in zip(
                        structure.outcomes, solution.state_payouts, strict=True
                    )
                },
                worst_case_payout=min(solution.state_payouts),
            ),
            execution_plan=ExecutionPlan(
                intents=intents,
                maximum_total_cost=all_in,
                maximum_unmatched_exposure=max(
                    quantity * execution_prices[token_id]
                    for token_id, quantity in solution.quantities.items()
                ),
            ),
            evidence={
                "solver": "decimal_finite_vertex_cover",
                "target_payout": str(self._config.target_payout),
                "fees": str(fees),
                "slippage": str(slippage),
                "execution_risk_buffer": str(self._config.execution_risk_buffer),
                "fee_source": self._fee_model.source,
                "fee_version": self._fee_model.observed_version,
            },
        )
        return (proposal,)
