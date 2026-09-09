"""Serviço de interpretação por LLM.

Responsabilidades:
- montar o prompt (schema + texto OCR);
- chamar o `LLMClient` configurado;
- fazer parsing/reparo leve do JSON;
- validar contra o schema (chaves exatas, tipos);
- rejeitar resposta inválida e repetir de forma limitada (`LLM_MAX_RETRIES`).

O LLM é instruído a usar somente evidência do texto OCR, não inventar dados e
retornar `null` quando não houver evidência (CLAUDE.md §7 / ESPECIFICACAO.md §7).
"""

from __future__ import annotations

import json
import logging
import re
import time

from app.config import get_settings
from app.models.schemas import ESSENTIAL_FIELDS, ExtractedFields
from app.services.llm.base import LLMAuthError, LLMClient, LLMError
from app.services.llm.fake_client import FakeLLMClient
from app.services.llm.openai_client import OpenAIClient
from app.utils.money import parse_money

log = logging.getLogger("app.llm")

SYSTEM_PROMPT = """Você é um extrator de dados de notas fiscais brasileiras.
Você recebe um TEXTO extraído por OCR e deve identificar exatamente cinco campos.

Regras obrigatórias:
1. Use SOMENTE informação explicitamente presente no texto fornecido.
2. NÃO invente, NÃO deduza e NÃO complete dados ausentes.
3. Se um campo não estiver claramente presente, retorne null para esse campo.
4. Responda EXCLUSIVAMENTE um objeto JSON válido, sem texto fora do JSON e sem markdown.
5. Não normalize nem "corrija" valores além do que o texto permite.

Formato de saída (exatamente estas chaves, nesta ordem):
{
  "issuer_name": string | null,
  "cnpj": string | null,
  "issue_date": string | null,
  "invoice_number": string | null,
  "total_value": number | null
}
"""


class LLMExtractionError(Exception):
    """Não foi possível obter uma resposta válida do LLM."""

    def __init__(self, message: str, *, attempts: int = 0, provider: str | None = None) -> None:
        super().__init__(message)
        self.attempts = attempts
        self.provider = provider


def build_user_prompt(ocr_text: str) -> str:
    return (
        "Texto OCR da nota fiscal (entre os marcadores):\n"
        "<<<OCR>>>\n"
        f"{ocr_text}\n"
        "<<<END>>>\n\n"
        "Retorne apenas o JSON com as chaves "
        "issuer_name, cnpj, issue_date, invoice_number, total_value."
    )


def get_client() -> LLMClient:
    settings = get_settings()
    if settings.llm_provider == "fake":
        return FakeLLMClient()
    return OpenAIClient(
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url,
        model=settings.llm_model,
    )


def _extract_json(text: str) -> dict:
    cleaned = text.strip()
    cleaned = re.sub(r"^```[a-zA-Z]*", "", cleaned).strip()
    cleaned = re.sub(r"```$", "", cleaned).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if not match:
            raise
        return json.loads(match.group(0))


def _to_fields(raw: object) -> ExtractedFields:
    if not isinstance(raw, dict):
        raise ValueError("JSON não é um objeto")

    extra = set(raw) - set(ESSENTIAL_FIELDS)
    if extra:
        raise ValueError(f"chaves não esperadas: {sorted(extra)}")

    payload = {k: raw.get(k) for k in ESSENTIAL_FIELDS}

    total = payload.get("total_value")
    if isinstance(total, str):
        stripped = total.strip()
        if not stripped:
            payload["total_value"] = None
        else:
            money = parse_money(stripped)
            if money is None:
                raise ValueError(f"total_value ambíguo ou inválido: {total!r}")
            payload["total_value"] = float(money)

    return ExtractedFields.model_validate(payload)


def extract_fields(
    ocr_text: str,
    client: LLMClient | None = None,
) -> tuple[ExtractedFields, dict]:
    """Retorna `(ExtractedFields, meta)`.

    `meta` = provider, model, attempts, raw_response_excerpt.
    Levanta `LLMExtractionError` quando esgota as tentativas.
    """
    settings = get_settings()
    client = client or get_client()
    provider = getattr(client, "provider", settings.llm_provider)
    user_prompt = build_user_prompt(ocr_text)
    last_error: Exception | None = None
    max_attempts = settings.llm_max_retries + 1
    attempt = 0

    for attempt in range(1, max_attempts + 1):
        if attempt > 1 and settings.llm_retry_backoff_seconds > 0:
            # backoff exponencial simples entre tentativas (ajuda em 429/5xx)
            time.sleep(settings.llm_retry_backoff_seconds * (2 ** (attempt - 2)))

        try:
            result = client.complete(SYSTEM_PROMPT, user_prompt, timeout=settings.llm_timeout_seconds)
        except LLMAuthError as exc:
            raise LLMExtractionError(
                f"credencial de LLM inválida: {exc}", attempts=attempt, provider=provider
            ) from exc
        except LLMError as exc:
            last_error = exc
            log.warning("LLM tentativa %s falhou (comunicação): %s", attempt, exc)
            continue

        try:
            raw = _extract_json(result.text)
            data = _to_fields(raw)
        except (ValueError, json.JSONDecodeError) as exc:
            last_error = exc
            log.warning("LLM tentativa %s: resposta inválida (%s)", attempt, exc)
            continue

        meta = {
            "provider": result.provider,
            "model": result.model,
            "attempts": attempt,
            "raw_response_excerpt": result.text[: settings.llm_excerpt_chars] or None,
        }
        return data, meta

    raise LLMExtractionError(
        f"resposta inválida do LLM após {max_attempts} tentativa(s): {last_error}",
        attempts=attempt,
        provider=provider,
    )
