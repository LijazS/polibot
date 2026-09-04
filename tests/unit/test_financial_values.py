from decimal import Decimal

import pytest
from pydantic import BaseModel, ValidationError

from polibot.domain.values import Money, Price


class FinancialExample(BaseModel):
    money: Money
    price: Price


def test_decimal_values_are_quantized_deterministically() -> None:
    value = FinancialExample(money="12.1234569", price=Decimal("0.5"))
    assert value.money == Decimal("12.123456")
    assert value.price == Decimal("0.500000")


@pytest.mark.parametrize("field", ["money", "price"])
def test_binary_float_is_rejected(field: str) -> None:
    values: dict[str, object] = {"money": "1", "price": "0.5"}
    values[field] = 0.5
    with pytest.raises(ValidationError, match="binary floating-point"):
        FinancialExample(**values)
