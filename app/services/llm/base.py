"""Contrato da camada de LLM (CLAUDE.md §7 / ESPECIFICACAO.md §7).

O acesso ao LLM acontece por uma interface isolada para permitir trocar de
provedor e usar um cliente falso nos testes. O LLM nunca é fonte de verdade:
a aplicação valida sempre a saída.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class LLMResult:
    text: str
    model: str
    provider: str


class LLMError(Exception):
    """Falha recuperável (timeout, comunicação, resposta inesperada) — permite retry."""


class LLMAuthError(LLMError):
    """Credencial inválida — NÃO deve ser repetida."""


class LLMClient(Protocol):
    provider: str

    def complete(self, system_prompt: str, user_prompt: str, *, timeout: float) -> LLMResult:
        ...
