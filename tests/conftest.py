"""Fixtures compartilhadas.

Isolamento de ambiente (P-01): a suíte é hermética. Todas as variáveis de
configuração usadas pelos testes são fixadas em `os.environ` ANTES de
importar a aplicação, de forma que a existência (ou não) de um arquivo
`.env` na máquina do desenvolvedor não altera o resultado dos testes.

- LLM sempre falso (`FakeLLMClient`).
- MongoDB via `mongomock` (sem servidor real).
- OCR real do Tesseract é substituído por texto canônico, exceto nos testes
  marcados `ocr_real`.
"""

from __future__ import annotations

import os

import pytest

# --- Ambiente de teste determinístico (força override; vence qualquer .env) ---
_TEST_ENV: dict[str, str] = {
    "APP_ENV": "test",
    "API_HOST": "127.0.0.1",
    "API_PORT": "8000",
    "LOG_LEVEL": "WARNING",
    "MAX_UPLOAD_MB": "10",
    "MONGO_URI": "mongodb://localhost:27017",
    "MONGO_DB": "tcc_ocr_llm_test",
    "MONGO_COLLECTION": "documents",
    "OCR_LANG": "por",
    "OCR_PREPROCESS": "false",
    "OCR_MIN_CHARS": "20",
    "OCR_TIMEOUT_SECONDS": "10",
    "PDF_DPI": "150",
    "LLM_PROVIDER": "fake",
    "LLM_API_KEY": "test-key-not-real",
    "LLM_BASE_URL": "https://example.invalid/v1",
    "LLM_MODEL": "fake-model",
    "LLM_TIMEOUT_SECONDS": "5",
    "LLM_MAX_RETRIES": "2",
    "LLM_RETRY_BACKOFF_SECONDS": "0",
    "LLM_EXCERPT_CHARS": "600",
}
for _key, _value in _TEST_ENV.items():
    os.environ[_key] = _value
os.environ.pop("POPPLER_PATH", None)

import mongomock  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.api.deps import get_llm_client, get_repository  # noqa: E402
from app.config import Settings, get_settings  # noqa: E402
from app.main import create_app  # noqa: E402
from app.repository.documents_repository import DocumentsRepository  # noqa: E402
from app.services.llm.fake_client import FakeLLMClient  # noqa: E402
from tests.support import SAMPLE_OCR_TEXT, SAMPLE_REFERENCE  # noqa: E402

# Segunda barreira contra o `.env`: durante a suíte, `Settings` é construído
# sem ler nenhum arquivo dotenv. Como as variáveis acima já estão em
# `os.environ` (e variável de ambiente tem prioridade sobre dotenv), o
# resultado é idêntico com ou sem `.env` na máquina.
Settings.model_config["env_file"] = None


@pytest.fixture(autouse=True)
def _fresh_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def settings():
    return get_settings()


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
