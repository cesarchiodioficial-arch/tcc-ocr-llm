from app.services.baseline_extractor import baseline_extract
from tests.support import SAMPLE_OCR_TEXT


def test_extracts_from_sample_text():
    data = baseline_extract(SAMPLE_OCR_TEXT)
    assert data.cnpj == "12345678000195"
    assert data.issue_date == "2026-01-31"
    assert data.invoice_number == "12345"
    assert data.total_value == 245.90
    assert data.issuer_name == "POSTO AVENIDA LTDA"


def test_missing_fields_return_none():
    data = baseline_extract("documento sem dados fiscais relevantes aqui")
    assert data.cnpj is None
    assert data.issue_date is None
    assert data.total_value is None
    assert data.invoice_number is None


def test_empty_text():
    data = baseline_extract("")
    assert data.model_dump() == {
        "issuer_name": None,
        "cnpj": None,
        "issue_date": None,
        "invoice_number": None,
        "total_value": None,
    }


def test_picks_largest_money_as_total():
    text = "Item A 10,00\nItem B 30,50\nTOTAL 40,50"
    assert baseline_extract(text).total_value == 40.50
