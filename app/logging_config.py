"""Configuração de logging.

Regra de privacidade (CLAUDE.md §9 / ESPECIFICACAO.md §14): nunca logar o
`ocr_text` completo nem o conteúdo fiscal completo. Os logs registram apenas
identificador do documento, estágio, duração e resultado.
"""

from __future__ import annotations

import logging

from app.config import get_settings

_CONFIGURED = False


def configure_logging() -> None:
    global _CONFIGURED
    if _CONFIGURED:
        return
    settings = get_settings()
    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    _CONFIGURED = True
