from uuid import uuid4

from tests.support import make_invoice_png


def _create(client):
    return client.post(
        "/api/v1/documents",
        files={"file": ("nota.png", make_invoice_png(), "image/png")},
    ).json()


def test_get_returns_full_structure(client, stub_ocr):
    created = _create(client)
    response = client.get(f"/api/v1/documents/{created['_id']}")
    assert response.status_code == 200
    body = response.json()
    for key in ("status", "ocr_text", "extracted_data", "validation", "processing", "llm"):
        assert key in body


def test_get_unknown_id_404(client):
    response = client.get(f"/api/v1/documents/{uuid4()}")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


def test_get_invalid_id_400(client):
    response = client.get("/api/v1/documents/nao-e-uuid")
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_id"
