from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ExternalModel(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)


class GammaMarketDTO(ExternalModel):
    id: str
    question: str | None = None
    condition_id: str | None = Field(default=None, alias="conditionId")
    question_id: str | None = Field(default=None, alias="questionID")
    slug: str | None = None
    outcomes: object = None
    clob_token_ids: object = Field(default=None, alias="clobTokenIds")
    active: bool = False
    closed: bool = False
    restricted: bool = False
    enable_order_book: bool = Field(default=False, alias="enableOrderBook")
    accepting_orders: bool = Field(default=False, alias="acceptingOrders")
    neg_risk: bool = Field(default=False, alias="negRisk")
    minimum_tick_size: object = Field(default=None, alias="orderPriceMinTickSize")
    minimum_order_size: object = Field(default=None, alias="orderMinSize")
    maker_base_fee: object = Field(default=None, alias="makerBaseFee")
    taker_base_fee: object = Field(default=None, alias="takerBaseFee")
    fees_enabled: bool | None = Field(default=None, alias="feesEnabled")
    start_date: str | None = Field(default=None, alias="startDate")
    end_date: str | None = Field(default=None, alias="endDate")
    events: tuple[GammaEventRefDTO, ...] = ()


class GammaEventRefDTO(ExternalModel):
    id: str


class GammaEventDTO(ExternalModel):
    id: str
    slug: str | None = None
    title: str
    start_date: str | None = Field(default=None, alias="startDate")
    end_date: str | None = Field(default=None, alias="endDate")
    active: bool = False
    closed: bool = False
    restricted: bool = False
    neg_risk: bool = Field(default=False, alias="negRisk")
    markets: tuple[GammaMarketDTO, ...] = ()


class TokenPairDTO(ExternalModel):
    condition_id: str
    primary_token_id: str
    secondary_token_id: str


class FeeObservationDTO(ExternalModel):
    fees_enabled: bool
    maker_base_fee: Decimal | None = None
    taker_base_fee: Decimal | None = None
