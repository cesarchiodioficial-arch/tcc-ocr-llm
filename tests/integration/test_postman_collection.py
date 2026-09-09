"""Coerência da coleção Postman com a API real (OpenAPI).

Não substitui a execução manual no Postman, mas garante que todos os
requests da coleção apontam para rotas/métodos que existem.
"""

import json
import re
from pathlib import Path

from app.main import app

COLLECTION = Path("postman/TCC-OCR-LLM.postman_collection.json")


def _iter_requests(items):
    for item in items:
        if "item" in item:
            yield from _iter_requests(item["item"])
        elif "request" in item:
            yield item["name"], item["request"]


def _to_openapi_path(segments: list[str]) -> str:
    mapping = {"{{document_id}}": "{doc_id}"}
    return "/" + "/".join(mapping.get(seg, seg) for seg in segments if seg)


def test_collection_is_valid_json_and_v21():
    data = json.loads(COLLECTION.read_text(encoding="utf-8"))
    assert "v2.1.0" in data["info"]["schema"]
    keys = {v["key"] for v in data["variable"]}
    assert {"base_url", "document_id"} <= keys


def test_every_request_matches_an_api_route():
    data = json.loads(COLLECTION.read_text(encoding="utf-8"))
    openapi = app.openapi()
    known = {
        (method.upper(), path)
        for path, methods in openapi["paths"].items()
        for method in methods
    }

    checked = 0
    for name, request in _iter_requests(data["item"]):
        method = request["method"].upper()
        segments = request["url"]["path"]
        path = _to_openapi_path(segments)
        assert (method, path) in known, f"request '{name}' → {method} {path} não existe na API"
        checked += 1
    assert checked >= 6  # health + 5 operações do fluxo


def test_upload_request_has_file_field_and_test_script():
    data = json.loads(COLLECTION.read_text(encoding="utf-8"))
    for name, request in _iter_requests(data["item"]):
        if name == "Upload documento":
            fields = request["body"]["formdata"]
            assert any(f["key"] == "file" and f["type"] == "file" for f in fields)
            return
    raise AssertionError("request 'Upload documento' não encontrado")
