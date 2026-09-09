"""Verifica o schema OpenAPI e que docs/openapi.json está sincronizado."""

import json
from pathlib import Path

from app.main import app

EXPECTED = {
    ("get", "/health"),
    ("post", "/api/v1/documents"),
    ("get", "/api/v1/documents/{doc_id}"),
    ("put", "/api/v1/documents/{doc_id}"),
    ("post", "/api/v1/documents/{doc_id}/reprocess"),
}


def test_openapi_has_all_operations():
    schema = app.openapi()
    ops = {
        (method, path)
        for path, methods in schema["paths"].items()
        for method in methods
    }
    assert EXPECTED <= ops


def test_openapi_documents_error_responses():
    """As respostas de erro reais aparecem no contrato (P-10)."""
    schema = app.openapi()
    post = schema["paths"]["/api/v1/documents"]["post"]["responses"]
    for code in ("400", "413", "415", "422", "503"):
        assert code in post, f"POST /documents não documenta {code}"
    health = schema["paths"]["/health"]["get"]["responses"]
    assert "503" in health


def test_openapi_file_is_in_sync():
    on_disk = json.loads(Path("docs/openapi.json").read_text(encoding="utf-8"))
    live = app.openapi()
    assert json.dumps(on_disk, sort_keys=True) == json.dumps(live, sort_keys=True), (
        "docs/openapi.json desatualizado — rode: python -m scripts.export_openapi"
    )
