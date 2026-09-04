from decimal import Decimal
from enum import StrEnum

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class ExecutionMode(StrEnum):
    REPLAY = "replay"
    PAPER = "paper"
    SHADOW = "shadow"
    LIVE = "live"


class Settings(BaseSettings):
    """Runtime configuration. Invalid or incomplete live configuration fails closed."""

    model_config = SettingsConfigDict(env_prefix="POLIBOT_", env_file=".env", extra="ignore")

    execution_mode: ExecutionMode = ExecutionMode.PAPER
    live_trading_enabled: bool = False
    database_url: str = "postgresql+asyncpg://polibot:polibot@localhost:5432/polibot"
    log_level: str = "INFO"
    stale_book_after_seconds: int = Field(default=5, ge=1)
    minimum_net_edge: Decimal = Field(default=Decimal("0.005"), ge=Decimal("0"))
    maximum_order_notional: Decimal = Field(default=Decimal("100"), gt=Decimal("0"))
    maximum_global_exposure: Decimal = Field(default=Decimal("1000"), gt=Decimal("0"))

    @field_validator(
        "minimum_net_edge",
        "maximum_order_notional",
        "maximum_global_exposure",
        mode="before",
    )
    @classmethod
    def reject_float_financial_values(cls, value: object) -> object:
        if isinstance(value, float):
            raise ValueError("financial configuration must not use binary floating-point")
        return value

    @model_validator(mode="after")
    def require_deliberate_live_enablement(self) -> "Settings":
        if self.execution_mode is ExecutionMode.LIVE and not self.live_trading_enabled:
            raise ValueError("LIVE mode requires POLIBOT_LIVE_TRADING_ENABLED=true")
        return self
