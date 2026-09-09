"""Estados do processamento de um documento (ESPECIFICACAO.md §9).

A causa de uma falha fica em `error.stage`; por isso não existem estados
separados `OCR_FAILED` / `LLM_FAILED` (ver PLANO_IMPLEMENTACAO.md, conflito C-03).
"""

from __future__ import annotations

from enum import StrEnum


class DocumentStatus(StrEnum):
    RECEIVED = "RECEIVED"
    PROCESSING = "PROCESSING"
    OCR_COMPLETED = "OCR_COMPLETED"
    EXTRACTED = "EXTRACTED"
    VALIDATION_PENDING = "VALIDATION_PENDING"
    VALIDATED = "VALIDATED"
    FAILED = "FAILED"
    REPROCESSING = "REPROCESSING"
