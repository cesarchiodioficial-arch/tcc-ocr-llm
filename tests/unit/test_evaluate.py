"""Testes da lógica de avaliação (Experimento A × B) — sem OCR/LLM reais."""

from app.models.schemas import ExtractedFields
from scripts.evaluate import DocResult, _canonical, _compare, _summary_block

REF = {
    "issuer_name": "POSTO AVENIDA LTDA",
    "cnpj": "12345678000195",
    "issue_date": "2026-01-31",
    "invoice_number": "12345",
    "total_value": "245.90",
}


def test_compare_all_correct():
    got = ExtractedFields(
        issuer_name="Posto Avenida LTDA",
        cnpj="12.345.678/0001-95",
        issue_date="31/01/2026",
        invoice_number="12345",
        total_value=245.90,
    )
    r = _compare(REF, got, "n.png", "B_ocr_llm", 100, success=True)
    assert r.evaluated == 5
    assert r.correct == 5
    assert r.corrections_needed == 0
    assert r.accuracy == 100.0


def test_compare_counts_missing_and_incorrect_as_corrections_needed():
    got = ExtractedFields(cnpj="99999999999999", issue_date=None)
    r = _compare(REF, got, "n.png", "A_ocr_only", 50, success=True)
    assert r.evaluated == 5
    assert r.missing >= 1
    assert r.incorrect >= 1
    assert r.corrections_needed == r.missing + r.incorrect


def test_reference_without_value_is_not_evaluated():
    ref = {**REF, "invoice_number": ""}
    got = ExtractedFields(invoice_number=None)
    r = _compare(ref, got, "n.png", "A_ocr_only", 10, success=True)
    assert r.evaluated == 4  # invoice_number sem referência não conta


def test_summary_block_has_success_rate():
    subset = [
        DocResult("a", "B_ocr_llm", correct=5, evaluated=5, success=True),
        DocResult("b", "B_ocr_llm", correct=2, evaluated=5, missing=3,
                  corrections_needed=3, success=False),
    ]
    text = "\n".join(_summary_block(subset))
    assert "taxa de documentos processados com sucesso" in text
    assert "50.0%" in text  # 1 de 2
    assert "correções necessárias" in text


def test_canonical_normalizes():
    assert _canonical("cnpj", "12.345.678/0001-95") == "12345678000195"
    assert _canonical("issue_date", "31/01/2026") == "2026-01-31"
    assert _canonical("total_value", "245,90") == 245.90
    assert _canonical("issuer_name", "  ACME  ") == "acme"
    assert _canonical("cnpj", "") is None
