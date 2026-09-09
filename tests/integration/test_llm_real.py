"""Integração real com o provedor de LLM (OpenAI).

Desativado por padrão. Só executa quando:
    RUN_LLM_REAL=1  e  LLM_API_KEY  válida no ambiente.
Não faz parte dos critérios de aceite automáticos (PLANO §L.3).
"""

import os

import pytest

pytestmark = pytest.mark.llm_real

_ENABLED = os.getenv("RUN_LLM_REAL") == "1" and os.getenv("LLM_API_KEY", "changeme") not in (
    "",
    "changeme",
    "none",
)


@pytest.mark.skipif(not _ENABLED, reason="RUN_LLM_REAL!=1 ou LLM_API_KEY ausente")
def test_real_openai_returns_valid_schema():
    from app.services.llm.openai_client import OpenAIClient
    from app.services.llm_service import extract_fields
    from tests.support import SAMPLE_OCR_TEXT

    client = OpenAIClient(
        api_key=os.environ["LLM_API_KEY"],
        base_url=os.getenv("LLM_BASE_URL", "https://api.openai.com/v1"),
        model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
    )
    data, meta = extract_fields(SAMPLE_OCR_TEXT, client=client)
    assert meta["provider"] == "openai"
    # o modelo deve reconhecer ao menos o CNPJ presente no texto
    assert data.cnpj is not None
