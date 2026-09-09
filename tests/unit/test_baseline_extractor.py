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


def test_prefers_labelled_total_over_largest_value():
    # o maior valor é 1.500,00 (base de cálculo), mas o TOTAL é 245,90
    text = (
        "POSTO AVENIDA LTDA\n"
        "Base de calculo ICMS 1.500,00\n"
        "Itens 200,00\n"
        "VALOR TOTAL DA NOTA R$ 245,90\n"
    )
    assert baseline_extract(text).total_value == 245.90


def test_issuer_is_line_near_first_cnpj_not_header():
    text = (
        "DOCUMENTO AUXILIAR DA NOTA FISCAL ELETRONICA\n"
        "SECRETARIA DA FAZENDA DO ESTADO\n"
        "POSTO AVENIDA LTDA\n"
        "CNPJ 12.345.678/0001-95\n"
        "NOTA FISCAL No 12345\n"
    )
    assert baseline_extract(text).issuer_name == "POSTO AVENIDA LTDA"


def test_invoice_number_keeps_leading_zeros():
    text = "NOTA FISCAL Nº 000123\nCNPJ 12.345.678/0001-95\n"
    assert baseline_extract(text).invoice_number == "000123"


def test_falls_back_to_largest_value_without_label():
    text = "Item A 10,00\nItem B 30,50\n40,50\n"
    assert baseline_extract(text).total_value == 40.50
