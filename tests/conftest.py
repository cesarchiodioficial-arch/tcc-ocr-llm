"""Fixtures compartilhadas.

- LLM sempre falso (`FakeLLMClient`) nos testes automatizados.
- MongoDB via `mongomock` (sem servidor real).
- OCR real do Tesseract é substituído por texto canônico, exceto nos testes
  marcados `ocr_real`.
"""

from __future__ import annotations

import os

import pytest

os.environ.setdefault("LLM_PROVIDER", "fake")
os.environ.setdefault("LLM_API_KEY", "changeme")
os.environ.setdefault("MONGO_URI", "mongodb://localhost:27017")
os.environ.setdefault("OCR_PREPROCESS", "false")

import mongomock  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.api.deps import get_llm_client, get_repository  # noqa: E402
from app.config import get_settings  # noqa: E402
from app.main import create_app  # noqa: E402
from app.repository.documents_repository import DocumentsRepository  # noqa: E402
from app.services.llm.fake_client import FakeLLMClient  # noqa: E402
from tests.support import SAMPLE_OCR_TEXT, SAMPLE_REFERENCE  # noqa: E402


@pytest.fixture(autouse=True)
def _clear_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def upload_dir(tmp_path, monkeypatch):
    path = tmp_path / "uploads"
    path.mkdir()
    monkeypatch.setenv("UPLOAD_DIR", str(path))
    get_settings.cache_clear()
    return path


@pytest.fixture
def repo():
    return DocumentsRepository(client=mongomock.MongoClient())


@pytest.fixture
def fake_llm():
    """FakeLLMClient em modo baseline: deriva a resposta do texto OCR do prompt."""
    return FakeLLMClient(model="fake-model", use_baseline=True)


@pytest.fixture
def stub_ocr(monkeypatch):
    """Substitui o OCR real por texto canônico da nota sintética."""

    def _fake_run_ocr(file_bytes, mime_type):
        return SAMPLE_OCR_TEXT, 1, 5

    monkeypatch.setattr("app.services.pipeline.ocr_service.run_ocr", _fake_run_ocr)
    return SAMPLE_OCR_TEXT


@pytest.fixture
def client(repo, fake_llm, upload_dir):
    app = create_app()
    app.dependency_overrides[get_repository] = lambda: repo
    app.dependency_overrides[get_llm_client] = lambda: fake_llm
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def reference():
    return dict(SAMPLE_REFERENCE)
