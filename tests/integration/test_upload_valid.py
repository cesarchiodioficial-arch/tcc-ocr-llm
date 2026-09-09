"""Fluxo completo: upload → OCR (stub) → LLM (fake baseline) → validação → persistência."""

from tests.support import make_invoice_png


def test_full_flow_reaches_validation_pending(client, stub_ocr, repo, reference):
    response = client.post(
        "/api/v1/documents",
        files={"file": ("nota.png", make_invoice_png(), "image/png")},
    )
    assert response.status_code == 201
    body = response.json()

    assert body["status"] == "VALIDATION_PENDING"
    assert body["ocr_text"]
    assert body["extracted_data"]["cnpj"] == reference["cnpj"]
    assert body["extracted_data"]["issue_date"] == reference["issue_date"]
    assert body["extracted_data"]["invoice_number"] == reference["invoice_number"]
    assert body["extracted_data"]["total_value"] == reference["total_value"]

    # metadados de processamento
    assert body["processing"]["ocr_duration_ms"] >= 0
    assert body["processing"]["total_duration_ms"] >= 0
    assert body["llm"]["provider"] == "fake"
    assert body["llm"]["attempts"] == 1

    # validação sistêmica presente
    checks = body["validation"]["field_checks"]
    assert checks["cnpj"]["valid"] is True
    assert body["validation"]["validated"] is False

    # persistido no Mongo
    stored = repo.get(body["_id"])
    assert stored["status"] == "VALIDATION_PENDING"


def test_pdf_upload_accepted_header(client, stub_ocr):
    from tests.support import make_invoice_pdf

    response = client.post(
        "/api/v1/documents",
        files={"file": ("nota.pdf", make_invoice_pdf(1), "application/pdf")},
    )
    # OCR está stubado → chega a VALIDATION_PENDING
    assert response.status_code == 201
    assert response.json()["mime_type"] == "application/pdf"


def test_multipage_pdf_records_source_pages(client, monkeypatch):
    """`source_pages` do OCR chega até a resposta da API (P-11)."""
    from tests.support import SAMPLE_OCR_TEXT, make_invoice_pdf

    monkeypatch.setattr(
        "app.services.pipeline.ocr_service.run_ocr",
        lambda data, mime: (SAMPLE_OCR_TEXT, 3, 9),
    )
    body = client.post(
        "/api/v1/documents",
        files={"file": ("nota.pdf", make_invoice_pdf(3), "application/pdf")},
    ).json()
    assert body["source_pages"] == 3
    assert body["processing"]["ocr_duration_ms"] == 9


def test_jpeg_upload_accepted(client, stub_ocr):
    import io

    from PIL import Image

    buffer = io.BytesIO()
    Image.new("RGB", (200, 120), "white").save(buffer, format="JPEG")
    response = client.post(
        "/api/v1/documents",
        files={"file": ("nota.jpg", buffer.getvalue(), "image/jpeg")},
    )
    assert response.status_code == 201
    assert response.json()["mime_type"] == "image/jpeg"


def test_flow_with_realistic_llm_json_response(client, stub_ocr):
    """LLM devolve JSON cru (formato do provedor real), não o baseline (P-18)."""
    from app.api.deps import get_llm_client
    from app.services.llm.fake_client import FakeLLMClient

    canned = (
        '```json\n{"issuer_name": "Posto Avenida LTDA", "cnpj": "12.345.678/0001-95", '
        '"issue_date": "31/01/2026", "invoice_number": "012345", "total_value": "245,90"}\n```'
    )
    client.app.dependency_overrides[get_llm_client] = lambda: FakeLLMClient(canned, model="gpt-x")

    body = client.post(
        "/api/v1/documents",
        files={"file": ("nota.png", make_invoice_png(), "image/png")},
    ).json()

    assert body["status"] == "VALIDATION_PENDING"
    # a aplicação faz parsing do markdown, normaliza data/cnpj/valor e valida
    assert body["extracted_data"]["cnpj"] == "12345678000195"
    assert body["extracted_data"]["issue_date"] == "2026-01-31"
    assert body["extracted_data"]["total_value"] == 245.90
    assert body["extracted_data"]["invoice_number"] == "012345"
    assert body["validation"]["field_checks"]["cnpj"]["valid"] is True
    assert body["llm"]["model"] == "gpt-x"
