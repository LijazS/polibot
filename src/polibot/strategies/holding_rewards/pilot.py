from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator

from polibot.domain.values import Money, SignedMoney


class RewardObservation(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    observation_id: UUID = Field(default_factory=uuid4)
    market_id: str
    position_quantity: Money
    observed_at: datetime
    eligible: bool
    parameters: dict[str, str]
    provenance: str
    expected_reward: Money | None = None
    actual_reward: Money | None = None

    @field_validator("observed_at")
    @classmethod
    def aware_timestamp(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("reward observation timestamp must be timezone-aware")
        return value.astimezone(UTC)

    @property
    def difference(self) -> SignedMoney | None:
        if self.expected_reward is None or self.actual_reward is None:
            return None
        return self.actual_reward - self.expected_reward


class HoldingRewardPilot:
    """Records sourced observations; it never invents eligibility or a reward rate."""

    def observe(
        self,
        *,
        market_id: str,
        position_quantity: Decimal,
        observed_at: datetime,
        eligible: bool | None,
        parameters: dict[str, str] | None,
        provenance: str | None,
        expected_reward: Decimal | None = None,
        actual_reward: Decimal | None = None,
    ) -> RewardObservation | None:
        if eligible is None or parameters is None or not provenance:
            return None
        return RewardObservation(
            market_id=market_id,
            position_quantity=position_quantity,
            observed_at=observed_at,
            eligible=eligible,
            parameters=parameters,
            provenance=provenance,
            expected_reward=expected_reward,
            actual_reward=actual_reward,
        )
