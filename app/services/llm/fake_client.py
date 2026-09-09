"""`FakeLLMClient` — cliente determinístico para os testes automatizados.

Nunca faz rede. Usado em todos os testes unitários e de integração
(CLAUDE.md §11 / ESPECIFICACAO.md §16). Também pode operar em modo
"baseline": deriva a resposta do próprio texto OCR recebido no prompt,
o que torna o teste de fluxo ponta a ponta mais realista.
"""

from __future__ import annotations

import json

from app.services.llm.base import LLMError, LLMResult


class FakeLLMClient:
    provider = "fake"

    def __init__(
        self,
        response: str | dict | None = None,
        *,
        model: str = "fake-model",
        fail_times: int = 0,
        raise_times: int = 0,
        use_baseline: bool = False,
    ) -> None:
        self.model = model
        self._fail_times = fail_times
        self._raise_times = raise_times
        self._use_baseline = use_baseline
        self.calls = 0

        if response is None:
            response = {
                "issuer_name": None,
                "cnpj": None,
                "issue_date": None,
                "invoice_number": None,
                "total_value": None,
            }
        self._response = response if isinstance(response, str) else json.dumps(response, ensure_ascii=False)

    def complete(self, system_prompt: str, user_prompt: str, *, timeout: float) -> LLMResult:
        self.calls += 1

        if self.calls <= self._raise_times:
            raise LLMError("falha simulada de comunicação")
        if self.calls <= self._raise_times + self._fail_times:
            return LLMResult(text="isto não é json", model=self.model, provider=self.provider)

        if self._use_baseline:
            from app.services.baseline_extractor import baseline_extract

            marker_start = user_prompt.find("<<<OCR>>>")
            marker_end = user_prompt.find("<<<END>>>")
            ocr_text = (
                user_prompt[marker_start + len("<<<OCR>>>") : marker_end]
                if marker_start != -1 and marker_end != -1
                else user_prompt
            )
            data = baseline_extract(ocr_text)
            return LLMResult(
                text=data.model_dump_json(),
                model=self.model,
                provider=self.provider,
            )

        return LLMResult(text=self._response, model=self.model, provider=self.provider)
