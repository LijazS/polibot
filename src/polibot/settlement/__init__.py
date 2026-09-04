"""Settlement adapter interfaces (V2 implementation pending)."""

from polibot.settlement.ports import (
    FakeSettlementAdapter,
    SettlementAdapter,
    SettlementIntent,
    SettlementOperation,
    SettlementResult,
)

__all__ = [
    "FakeSettlementAdapter",
    "SettlementAdapter",
    "SettlementIntent",
    "SettlementOperation",
    "SettlementResult",
]
