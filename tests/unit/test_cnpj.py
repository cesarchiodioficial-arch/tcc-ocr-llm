import pytest

from app.utils.cnpj import format_cnpj, is_valid_cnpj, normalize_cnpj


@pytest.mark.parametrize(
    "value",
    ["12345678000195", "12.345.678/0001-95", "11.222.333/0001-81", "11444777000161"],
)
def test_valid_cnpjs(value):
    assert is_valid_cnpj(value) is True


@pytest.mark.parametrize(
    "value",
    [
        "12345678000199",  # dígitos verificadores errados
        "12345678000",  # curto
        "123456780001999",  # longo
        "00000000000000",  # sequência repetida
        "11111111111111",
        "",
        None,
        "abcdefghijklmn",
    ],
)
def test_invalid_cnpjs(value):
    assert is_valid_cnpj(value) is False


def test_normalize_strips_mask():
    assert normalize_cnpj("12.345.678/0001-95") == "12345678000195"
    assert normalize_cnpj(None) is None
    assert normalize_cnpj("---") is None


def test_format_cnpj():
    assert format_cnpj("12345678000195") == "12.345.678/0001-95"
    assert format_cnpj("123") is None
