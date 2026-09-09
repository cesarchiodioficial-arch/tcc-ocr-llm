from uuid import uuid4

from tests.support import make_invoice_png


def _create(client):
    return client.post(
        "/api/v1/documents",
        files={"file": ("nota.png", make_invoice_png(), "image/png")},
    ).json()


def test_reprocess_recomputes_and_keeps_corrections(client, stub_ocr, repo):
    created = _create(client)
    doc_id = created["_id"]

    # correção humana antes do reprocessamento
    client.put(
        f"/api/v1/documents/{doc_id}",
        json={"extracted_data": {"issuer_name": "Nome corrigido"}},
    )

    response = client.post(f"/api/v1/documents/{doc_id}/reprocess")
    assert response.status_code == 200
    body = response.json()

    assert body["status"] == "VALIDATION_PENDING"
    assert body["processing"]["reprocess_count"] == 1
    assert body["validation"]["validated"] is False
    # histórico de correção preservado
    assert any(c["field"] == "issuer_name" for c in body["validation"]["corrections"])
    # dados recalculados a partir do arquivo original
    assert body["extracted_data"]["cnpj"] == "12345678000195"


def test_reprocess_missing_original_returns_409(client, stub_ocr, repo):
    created = _create(client)
    doc_id = created["_id"]

    stored = repo.get(doc_id)
    from pathlib import Path

    Path(stored["file_path"]).unlink()

    response = client.post(f"/api/v1/documents/{doc_id}/reprocess")
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "original_missing"


def test_reprocess_unknown_id_404(client):
    response = client.post(f"/api/v1/documents/{uuid4()}/reprocess")
    assert response.status_code == 404
