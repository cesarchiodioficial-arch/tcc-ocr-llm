import pytest

from app.utils.dates import is_valid_date, parse_date, to_iso


@pytest.mark.parametrize(
    ("raw", "iso"),
    [
        ("2026-01-31", "2026-01-31"),
        ("31/01/2026", "2026-01-31"),
        ("31-01-2026", "2026-01-31"),
        ("31.01.2026", "2026-01-31"),
        ("2026/01/31", "2026-01-31"),
    ],
)
def test_formats_normalize_to_iso(raw, iso):
    assert to_iso(raw) == iso
    assert is_valid_date(raw) is True


@pytest.mark.parametrize("raw", ["31/02/2026", "2026-13-01", "not a date", "", None, "45/45/4545"])
def test_invalid_dates(raw):
    assert parse_date(raw) is None
    assert is_valid_date(raw) is False


@pytest.mark.parametrize("raw", ["01/01/1990", "01/01/2200"])
def test_year_out_of_range(raw):
    assert is_valid_date(raw) is False


def test_br_priority_day_first():
    # 03/04/2026 deve ser 3 de abril (dd/mm), não 4 de março
    assert to_iso("03/04/2026") == "2026-04-03"
