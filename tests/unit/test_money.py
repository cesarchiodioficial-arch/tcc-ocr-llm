from decimal import Decimal

import pytest

from app.utils.money import parse_money


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("1.234,56", Decimal("1234.56")),
        ("1234.56", Decimal("1234.56")),
        ("R$ 1.200,00", Decimal("1200.00")),
        ("1,234.56", Decimal("1234.56")),
        ("245,90", Decimal("245.90")),
        ("12,5", None),  # 1 casa decimal com vírgula → ambíguo
        (1500.5, Decimal("1500.5")),
        (0, Decimal("0")),
        ("1.234.567,89", Decimal("1234567.89")),
        ("1.234.567", Decimal("1234567")),  # só pontos de milhar
        ("2500", Decimal("2500")),
    ],
)
def test_parse_money(raw, expected):
    assert parse_money(raw) == expected


@pytest.mark.parametrize(
    "raw",
    ["1.234", "1,234", "abc", "", None, "-100", "1,2,3", True, "R$", "12,345", ".", ",", "-5.0"],
)
def test_parse_money_rejects(raw):
    assert parse_money(raw) is None
