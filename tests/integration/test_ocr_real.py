"""OCR real do Tesseract + conversão real de PDF (Poppler).

Só roda se Tesseract e Poppler estiverem instalados (dentro do container
Docker). No host sem essas ferramentas, os testes são ignorados (skip),
não falham.
"""

import pytest

from app.services import ocr_service
from tests.support import (
    SAMPLE_REFERENCE,
    make_invoice_pdf,
    make_invoice_png,
)

pytestmark = pytest.mark.ocr_real

_HAS_TESSERACT = ocr_service.tesseract_available()


def _has_poppler() -> bool:
    try:
        ocr_service.run_ocr(make_invoice_pdf(1), "application/pdf")
        return True
    except ocr_service.OcrError as exc:
        if "Poppler" in str(exc):
            return False
        return True
    except Exception:  # noqa: BLE001
        return True


@pytest.mark.skipif(not _HAS_TESSERACT, reason="Tesseract não instalado neste ambiente")
def test_real_ocr_extracts_text_from_synthetic_invoice(monkeypatch):
    monkeypatch.setenv("OCR_PREPROCESS", "true")
    from app.config import get_settings

    get_settings.cache_clear()

    text, pages, duration_ms = ocr_service.run_ocr(make_invoice_png(), "image/png")
    assert pages == 1
    assert duration_ms >= 0
    assert ocr_service.has_useful_text(text)
    digits = "".join(c for c in text if c.isdigit())
    assert SAMPLE_REFERENCE["cnpj"][:6] in digits or "12345" in digits


@pytest.mark.skipif(
    not (_HAS_TESSERACT and _has_poppler()),
    reason="Tesseract ou Poppler ausentes",
)
def test_real_ocr_single_page_pdf():
    text, pages, _ = ocr_service.run_ocr(make_invoice_pdf(1), "application/pdf")
    assert pages == 1
    assert ocr_service.has_useful_text(text)


@pytest.mark.skipif(
    not (_HAS_TESSERACT and _has_poppler()),
    reason="Tesseract ou Poppler ausentes",
)
def test_real_ocr_multipage_pdf_counts_pages():
    text, pages, _ = ocr_service.run_ocr(make_invoice_pdf(3), "application/pdf")
    assert pages == 3
    assert "POSTO AVENIDA" in text.upper() or "12345" in text


@pytest.mark.skipif(not _has_poppler(), reason="Poppler ausente")
def test_corrupt_pdf_raises_corrupt_file_error():
    corrupt = b"%PDF-1.4\n" + b"nao eh um pdf de verdade " * 20
    with pytest.raises(ocr_service.CorruptFileError):
        ocr_service.run_ocr(corrupt, "application/pdf")
