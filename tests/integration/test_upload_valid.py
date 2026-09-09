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
    minimal_pdf = b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF"
    response = client.post(
        "/api/v1/documents",
        files={"file": ("nota.pdf", minimal_pdf, "application/pdf")},
    )
    # OCR está stubado → chega a VALIDATION_PENDING
    assert response.status_code == 201
    assert response.json()["mime_type"] == "application/pdf"


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
