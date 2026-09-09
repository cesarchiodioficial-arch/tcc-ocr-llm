"""Implementação do `LLMClient` para a API OpenAI (Chat Completions).

Compatível com qualquer endpoint que siga o contrato OpenAI (`LLM_BASE_URL`
configurável). O modelo é definido por `LLM_MODEL`.
"""

from __future__ import annotations

import httpx

from app.services.llm.base import LLMAuthError, LLMError, LLMResult


class OpenAIClient:
    provider = "openai"

    def __init__(self, api_key: str, base_url: str, model: str) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._model = model

    def complete(self, system_prompt: str, user_prompt: str, *, timeout: float) -> LLMResult:
        url = f"{self._base_url}/chat/completions"
        payload = {
            "model": self._model,
            "temperature": 0,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "response_format": {"type": "json_object"},
        }
        headers = {"Authorization": f"Bearer {self._api_key}"}

        try:
            response = httpx.post(url, json=payload, headers=headers, timeout=timeout)
        except httpx.TimeoutException as exc:
            raise LLMError(f"timeout: {exc}") from exc
        except httpx.HTTPError as exc:
            raise LLMError(f"erro de comunicação: {exc}") from exc

        if response.status_code in (401, 403):
            raise LLMAuthError(f"credencial inválida (HTTP {response.status_code})")
        if response.status_code >= 400:
            raise LLMError(f"HTTP {response.status_code}: {response.text[:200]}")

        try:
            data = response.json()
            text = data["choices"][0]["message"]["content"]
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            raise LLMError(f"resposta inesperada do provedor: {exc}") from exc

        return LLMResult(text=text, model=self._model, provider=self.provider)
