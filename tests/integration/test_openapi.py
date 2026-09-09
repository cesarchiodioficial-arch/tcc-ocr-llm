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


def test_openapi_file_is_in_sync():
    on_disk = json.loads(Path("docs/openapi.json").read_text(encoding="utf-8"))
    assert on_disk["paths"].keys() == app.openapi()["paths"].keys(), (
        "docs/openapi.json desatualizado — rode: python -m scripts.export_openapi"
    )
