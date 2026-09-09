from tests.support import make_invoice_png


def test_missing_file_field(client):
    response = client.post("/api/v1/documents")
    assert response.status_code == 422  # FastAPI: campo obrigatório ausente


def test_empty_file(client):
    response = client.post(
        "/api/v1/documents",
        files={"file": ("empty.png", b"", "image/png")},
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "empty_file"


def test_unsupported_type(client):
    response = client.post(
        "/api/v1/documents",
        files={"file": ("nota.txt", b"apenas texto", "text/plain")},
    )
    assert response.status_code == 415
    assert response.json()["error"]["code"] == "unsupported_type"


def test_corrupt_image(client):
    # cabeçalho PNG válido, conteúdo quebrado
    corrupt = b"\x89PNG\r\n\x1a\n" + b"quebrado" * 3
    response = client.post(
        "/api/v1/documents",
        files={"file": ("nota.png", corrupt, "image/png")},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "corrupt_file"


def test_file_too_large(client, monkeypatch):
    monkeypatch.setenv("MAX_UPLOAD_MB", "0")
    from app.config import get_settings

    get_settings.cache_clear()
    response = client.post(
        "/api/v1/documents",
        files={"file": ("nota.png", make_invoice_png(), "image/png")},
    )
    assert response.status_code == 413
    assert response.json()["error"]["code"] == "file_too_large"


def test_db_unavailable_returns_503(client, repo, monkeypatch):
    monkeypatch.setattr(repo, "ping", lambda: False)
    response = client.post(
        "/api/v1/documents",
        files={"file": ("nota.png", make_invoice_png(), "image/png")},
    )
    assert response.status_code == 503
    assert response.json()["error"]["stage"] == "persistence"
