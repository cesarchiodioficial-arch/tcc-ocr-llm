"""Caminhos de falha: nunca reportar sucesso quando o processamento falhou."""

from app.api.deps import get_llm_client
from app.services.llm.fake_client import FakeLLMClient
from tests.support import make_invoice_png


def _create(client):
    return client.post(
        "/api/v1/documents",
        files={"file": ("nota.png", make_invoice_png(), "image/png")},
    )


def test_ocr_without_text_marks_failed(client, monkeypatch, repo):
    monkeypatch.setattr(
        "app.services.pipeline.ocr_service.run_ocr",
        lambda data, mime: ("   ", 1, 3),
    )
    response = _create(client)
    assert response.status_code == 201  # recurso criado
    body = response.json()
    assert body["status"] == "FAILED"
    assert body["error"]["stage"] == "ocr"
    assert repo.get(body["_id"])["status"] == "FAILED"


def test_ocr_engine_error_marks_failed(client, monkeypatch):
    from app.services import ocr_service

    def _boom(data, mime):
        raise ocr_service.OcrError("Tesseract não encontrado")

    monkeypatch.setattr("app.services.pipeline.ocr_service.run_ocr", _boom)
    body = _create(client).json()
    assert body["status"] == "FAILED"
    assert body["error"]["stage"] == "ocr"


def test_llm_invalid_forever_marks_failed(client, stub_ocr):
    client.app.dependency_overrides[get_llm_client] = lambda: FakeLLMClient(fail_times=99)
    body = _create(client).json()
    assert body["status"] == "FAILED"
    assert body["error"]["stage"] == "llm"
    assert "3 tentativa" in body["error"]["message"]


def test_failed_document_can_be_corrected_and_validated(client, stub_ocr):
    client.app.dependency_overrides[get_llm_client] = lambda: FakeLLMClient(fail_times=99)
    body = _create(client).json()
    doc_id = body["_id"]
    assert body["status"] == "FAILED"

    # validar sem corrigir → 409
    resp = client.put(f"/api/v1/documents/{doc_id}", json={"validated": True})
    assert resp.status_code == 409

    # corrigir + validar → OK
    resp = client.put(
        f"/api/v1/documents/{doc_id}",
        json={
            "extracted_data": {
                "issuer_name": "Posto Avenida LTDA",
                "cnpj": "12345678000195",
                "issue_date": "2026-01-31",
                "invoice_number": "12345",
                "total_value": 245.90,
            },
            "validated": True,
        },
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "VALIDATED"
