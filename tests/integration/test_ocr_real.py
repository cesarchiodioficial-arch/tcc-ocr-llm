"""OCR real do Tesseract — só roda se o Tesseract estiver instalado.

No ambiente sem Tesseract (ex.: host Windows sem instalação), o teste é
ignorado (skip), não falha. Dentro do container Docker ele executa.
"""

import pytest

from app.services import ocr_service
from tests.support import SAMPLE_REFERENCE, make_invoice_png

pytestmark = pytest.mark.ocr_real

_HAS_TESSERACT = ocr_service.tesseract_available()


@pytest.mark.skipif(not _HAS_TESSERACT, reason="Tesseract não instalado neste ambiente")
def test_real_ocr_extracts_text_from_synthetic_invoice(monkeypatch):
    monkeypatch.setenv("OCR_PREPROCESS", "true")
    from app.config import get_settings

    get_settings.cache_clear()

    text, pages, duration_ms = ocr_service.run_ocr(make_invoice_png(), "image/png")
    assert pages == 1
    assert duration_ms >= 0
    assert ocr_service.has_useful_text(text)
    # pelo menos parte dos dados deve aparecer no texto bruto
    digits = "".join(c for c in text if c.isdigit())
    assert SAMPLE_REFERENCE["cnpj"][:6] in digits or "12345" in digits
