from __future__ import annotations

from decimal import ROUND_DOWN, Decimal, InvalidOperation
from typing import Annotated, Any

from pydantic import AfterValidator, BeforeValidator

SCALE = Decimal("0.000001")


def _to_decimal(value: Any) -> Decimal:
    if isinstance(value, (bool, float)):
        raise ValueError(
            "financial values must not use binary floating-point; "
            "provide Decimal, integer, or decimal string"
        )
    if isinstance(value, Decimal):
        result = value
    elif isinstance(value, (int, str)):
        try:
            result = Decimal(value)
        except InvalidOperation as exc:
            raise ValueError("invalid decimal value") from exc
    else:
        raise ValueError("unsupported financial value type")
    if not result.is_finite():
        raise ValueError("financial values must be finite")
    return result.quantize(SCALE, rounding=ROUND_DOWN)


def _non_negative(value: Decimal) -> Decimal:
    if value < 0:
        raise ValueError("value must be non-negative")
    return value


def _valid_price(value: Decimal) -> Decimal:
    if not Decimal("0") <= value <= Decimal("1"):
        raise ValueError("prediction-market price must be between 0 and 1")
    return value


Money = Annotated[Decimal, BeforeValidator(_to_decimal), AfterValidator(_non_negative)]
Quantity = Annotated[Decimal, BeforeValidator(_to_decimal), AfterValidator(_non_negative)]
Price = Annotated[Decimal, BeforeValidator(_to_decimal), AfterValidator(_valid_price)]
SignedMoney = Annotated[Decimal, BeforeValidator(_to_decimal)]
