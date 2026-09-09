"""Caminhos de falha: nunca reportar sucesso quando o processamento falhou."""

from app.api.deps import get_llm_client
from app.repository.documents_repository import RepositoryUnavailableError
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


def test_llm_invalid_forever_marks_failed(client, stub_ocr, settings):
    client.app.dependency_overrides[get_llm_client] = lambda: FakeLLMClient(fail_times=99)
    body = _create(client).json()
    assert body["status"] == "FAILED"
    assert body["error"]["stage"] == "llm"
    # rastreabilidade: nº de tentativas registrado no documento (não string frágil)
    assert body["llm"]["attempts"] == settings.llm_max_retries + 1
    assert body["llm"]["provider"] == "fake"


def test_mongo_failure_mid_pipeline_returns_503(client, stub_ocr, repo, monkeypatch):
    """MongoDB cai depois do insert inicial → 503 com envelope, nunca 500 (P-05)."""
    calls = {"n": 0}
    real_replace = repo.replace

    def _flaky_replace(doc):
        calls["n"] += 1
        if calls["n"] >= 2:
            raise RepositoryUnavailableError("conexão perdida")
        return real_replace(doc)

    monkeypatch.setattr(repo, "replace", _flaky_replace)
    response = _create(client)
    assert response.status_code == 503
    body = response.json()
    assert body["error"]["stage"] == "persistence"
    assert body["error"]["code"] == "persistence_failed"


def test_mongo_failure_while_recording_failed_state_returns_503(client, repo, monkeypatch):
    """Se nem o estado FAILED consegue ser gravado, ainda assim é 503 (nunca 500)."""
    monkeypatch.setattr(
        "app.services.pipeline.ocr_service.run_ocr",
        lambda data, mime: ("", 1, 1),  # OCR sem texto → _fail
    )
    calls = {"n": 0}
    real_replace = repo.replace

    def _replace(doc):
        calls["n"] += 1
        if calls["n"] == 1:  # deixa a transição p/ PROCESSING gravar
            return real_replace(doc)
        raise RepositoryUnavailableError("mongo down ao gravar FAILED")

    monkeypatch.setattr(repo, "replace", _replace)
    response = _create(client)
    assert response.status_code == 503
    assert response.json()["error"]["stage"] == "persistence"


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
