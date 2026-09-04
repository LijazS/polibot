from collections.abc import Sequence
from typing import Protocol

from polibot.domain.models import MarketSnapshot, OpportunityProposal


class Strategy(Protocol):
    """A pure proposal producer; exchange/order methods are intentionally absent."""

    @property
    def strategy_id(self) -> str: ...

    def evaluate(self, snapshot: MarketSnapshot) -> Sequence[OpportunityProposal]: ...
