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
    maximum_strategy_exposure: Decimal = Field(default=Decimal("500"), gt=Decimal("0"))
    maximum_market_exposure: Decimal = Field(default=Decimal("100"), gt=Decimal("0"))
    maximum_event_exposure: Decimal = Field(default=Decimal("250"), gt=Decimal("0"))
    maximum_unmatched_exposure: Decimal = Field(default=Decimal("25"), ge=Decimal("0"))
    maximum_unmatched_duration_seconds: int = Field(default=5, ge=1)
    maximum_slippage: Decimal = Field(default=Decimal("5"), ge=Decimal("0"))
    paper_initial_capital: Decimal = Field(default=Decimal("5000"), gt=Decimal("0"))
    paper_execution_latency_ms: int = Field(default=250, ge=0, le=60_000)
    worker_id: str = Field(default="polibot-paper-worker", min_length=1, max_length=100)
    worker_max_binary_markets: int = Field(default=25, ge=1, le=100)
    worker_max_negrisk_events: int = Field(default=0, ge=0, le=25)
    worker_discovery_page_size: int = Field(default=25, ge=1, le=500)
    worker_market_refresh_seconds: int = Field(default=300, ge=30)
    worker_heartbeat_seconds: int = Field(default=10, ge=2, le=60)
    worker_strategy_cycle_seconds: int = Field(default=1, ge=1, le=60)
    worker_recorder_batch_size: int = Field(default=250, ge=1, le=5000)
    worker_recorder_flush_seconds: int = Field(default=2, ge=1, le=60)
    worker_recorder_queue_size: int = Field(default=10_000, ge=100, le=1_000_000)
    worker_maximum_quantity: Decimal = Field(default=Decimal("25"), gt=Decimal("0"))
    worker_slippage_rate: Decimal = Field(default=Decimal("0.001"), ge=Decimal("0"))
    worker_execution_risk_buffer: Decimal = Field(default=Decimal("0.01"), ge=Decimal("0"))
    worker_proposal_lifetime_ms: int = Field(default=750, ge=50, le=10_000)
    gamma_base_url: str = "https://gamma-api.polymarket.com"
    clob_base_url: str = "https://clob.polymarket.com"
    clob_websocket_url: str = "wss://ws-subscriptions-clob.polymarket.com/ws/market"
    application_version: str = Field(default="0.1.0", min_length=1, max_length=50)
    git_sha: str = Field(default="unknown", min_length=1, max_length=64)

    @field_validator(
        "minimum_net_edge",
        "maximum_order_notional",
        "maximum_global_exposure",
        "maximum_strategy_exposure",
        "maximum_market_exposure",
        "maximum_event_exposure",
        "maximum_unmatched_exposure",
        "maximum_slippage",
        "paper_initial_capital",
        "worker_maximum_quantity",
        "worker_slippage_rate",
        "worker_execution_risk_buffer",
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
