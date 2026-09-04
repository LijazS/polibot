from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from polibot.domain.models import OpportunityProposal


class KillScope(StrEnum):
    GLOBAL = "global"
    STRATEGY = "strategy"
    MARKET = "market"
    EVENT = "event"
    HEALTH = "health"


@dataclass
class KillSwitchRegistry:
    global_reason: str | None = None
    strategy_reasons: dict[str, str] = field(default_factory=dict)
    market_reasons: dict[str, str] = field(default_factory=dict)
    event_reasons: dict[str, str] = field(default_factory=dict)
    health_reasons: set[str] = field(default_factory=set)

    def activate(self, scope: KillScope, key: str, reason: str) -> None:
        if scope is KillScope.GLOBAL:
            self.global_reason = reason
        elif scope is KillScope.STRATEGY:
            self.strategy_reasons[key] = reason
        elif scope is KillScope.MARKET:
            self.market_reasons[key] = reason
        elif scope is KillScope.EVENT:
            self.event_reasons[key] = reason
        else:
            self.health_reasons.add(reason)

    def clear(self, scope: KillScope, key: str) -> None:
        if scope is KillScope.GLOBAL:
            self.global_reason = None
        elif scope is KillScope.STRATEGY:
            self.strategy_reasons.pop(key, None)
        elif scope is KillScope.MARKET:
            self.market_reasons.pop(key, None)
        elif scope is KillScope.EVENT:
            self.event_reasons.pop(key, None)
        else:
            self.health_reasons.discard(key)

    def blockers(self, proposal: OpportunityProposal) -> tuple[str, ...]:
        reasons: list[str] = []
        if self.global_reason:
            reasons.append(f"global:{self.global_reason}")
        if proposal.strategy_id in self.strategy_reasons:
            reasons.append(f"strategy:{self.strategy_reasons[proposal.strategy_id]}")
        reasons.extend(
            f"market:{self.market_reasons[market_id]}"
            for market_id in proposal.market_ids
            if market_id in self.market_reasons
        )
        reasons.extend(
            f"event:{self.event_reasons[event_id]}"
            for event_id in proposal.event_ids
            if event_id in self.event_reasons
        )
        reasons.extend(f"health:{reason}" for reason in sorted(self.health_reasons))
        return tuple(reasons)


@dataclass
class RecoveryGate:
    durable_state_restored: bool = False
    reconciliation_healthy: bool = False
    rebuilt_market_ids: set[str] = field(default_factory=set)
    unresolved_execution_ids: set[str] = field(default_factory=set)

    def permit(self, proposal: OpportunityProposal) -> tuple[bool, tuple[str, ...]]:
        reasons: list[str] = []
        if not self.durable_state_restored:
            reasons.append("durable_state_not_restored")
        if not self.reconciliation_healthy:
            reasons.append("reconciliation_unhealthy")
        missing = sorted(set(proposal.market_ids) - self.rebuilt_market_ids)
        if missing:
            reasons.append(f"books_not_rebuilt:{','.join(missing)}")
        if self.unresolved_execution_ids:
            reasons.append("unknown_external_execution_state")
        return not reasons, tuple(reasons)
