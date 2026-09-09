"""Dependências FastAPI (injeção do repositório e do cliente LLM).

Os testes substituem estas dependências por `app.dependency_overrides`
(repositório com `mongomock`, `FakeLLMClient`).
"""

from __future__ import annotations

from functools import lru_cache

from app.repository.documents_repository import DocumentsRepository
from app.services.llm.base import LLMClient
from app.services.llm_service import get_client


@lru_cache
def _repository_singleton() -> DocumentsRepository:
    return DocumentsRepository()


def get_repository() -> DocumentsRepository:
    return _repository_singleton()


def get_llm_client() -> LLMClient:
    return get_client()
