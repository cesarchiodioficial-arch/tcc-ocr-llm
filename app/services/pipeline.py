"""Orquestrador do processamento (Artigo §3.1 / CLAUDE.md §4).

Coordena OCR → LLM → validação sistêmica dentro do mesmo processo
(processamento síncrono — PLANO conflito C-01). Atualiza o `status` a cada
estágio, mede tempos e transforma qualquer falha em estado `FAILED` visível.

Falha de persistência (MongoDB) propaga como `RepositoryUnavailableError`
para a camada da API, que responde 503 (ESPECIFICACAO.md §13 / CLAUDE.md §10):
nunca se reporta sucesso quando a gravação não ocorreu.
"""

from __future__ import annotations

import logging
import time

from app.models.enums import DocumentStatus
from app.models.schemas import ESSENTIAL_FIELDS
from app.repository.documents_repository import DocumentsRepository, RepositoryUnavailableError
from app.services import ocr_service
from app.services.llm_service import LLMExtractionError, extract_fields
from app.services.validation_service import normalize_extracted, validate_extracted
from app.utils.time_utils import now_iso

log = logging.getLogger("app.pipeline")


def _reset_results(doc: dict) -> None:
    """Limpa o resultado de um processamento anterior antes de reprocessar (P-08)."""
    doc["ocr_text"] = None
    doc["source_pages"] = None
    doc["extracted_data"] = {field: None for field in ESSENTIAL_FIELDS}
    doc["validation"]["schema_valid"] = None
    doc["validation"]["field_checks"] = {}
    doc["llm"] = None
    doc["processing"]["ocr_duration_ms"] = 0
    doc["processing"]["llm_duration_ms"] = 0
    doc["processing"]["total_duration_ms"] = 0


def process_document(
    doc: dict,
    file_bytes: bytes,
    repo: DocumentsRepository,
    llm_client=None,
) -> dict:
    started = time.perf_counter()
    is_reprocess = doc["processing"]["reprocess_count"] > 0
    if is_reprocess:
        _reset_results(doc)
    doc["status"] = DocumentStatus.REPROCESSING if is_reprocess else DocumentStatus.PROCESSING
    doc["error"] = None
    repo.replace(doc)

    # --- OCR ---
    try:
        ocr_text, pages, ocr_ms = ocr_service.run_ocr(file_bytes, doc["mime_type"])
    except ocr_service.CorruptFileError as exc:
        return _fail(doc, "ocr", f"arquivo ilegível: {exc}", repo, started)
    except ocr_service.OcrError as exc:
        return _fail(doc, "ocr", str(exc), repo, started)

    doc["ocr_text"] = ocr_text
    doc["source_pages"] = pages
    doc["processing"]["ocr_duration_ms"] = ocr_ms

    if not ocr_service.has_useful_text(ocr_text):
        return _fail(doc, "ocr", "OCR não produziu texto útil", repo, started)

    doc["status"] = DocumentStatus.OCR_COMPLETED
    repo.replace(doc)

    # --- LLM ---
    llm_started = time.perf_counter()
    try:
        data, meta = extract_fields(ocr_text, client=llm_client)
    except LLMExtractionError as exc:
        doc["processing"]["llm_duration_ms"] = int((time.perf_counter() - llm_started) * 1000)
        doc["llm"] = {
            "provider": exc.provider or "unknown",
            "model": "unknown",
            "attempts": exc.attempts,
            "raw_response_excerpt": None,
        }
        return _fail(doc, "llm", str(exc), repo, started)

    doc["processing"]["llm_duration_ms"] = int((time.perf_counter() - llm_started) * 1000)
    doc["llm"] = {
        "provider": meta["provider"],
        "model": meta["model"],
        "attempts": meta["attempts"],
        "raw_response_excerpt": meta["raw_response_excerpt"],
    }
    doc["status"] = DocumentStatus.EXTRACTED
    repo.replace(doc)

    # --- Validação sistêmica ---
    checks = validate_extracted(data)
    normalized = normalize_extracted(data)
    doc["extracted_data"] = normalized.model_dump()
    doc["validation"]["schema_valid"] = True
    doc["validation"]["field_checks"] = {k: v.model_dump() for k, v in checks.items()}
    doc["validation"]["validated"] = False
    doc["status"] = DocumentStatus.VALIDATION_PENDING
    doc["processing"]["total_duration_ms"] = int((time.perf_counter() - started) * 1000)
    repo.replace(doc)

    log.info(
        "pipeline ok id=%s status=%s ocr_ms=%s llm_ms=%s total_ms=%s",
        doc["_id"],
        doc["status"],
        doc["processing"]["ocr_duration_ms"],
        doc["processing"]["llm_duration_ms"],
        doc["processing"]["total_duration_ms"],
    )
    return doc


def _fail(doc: dict, stage: str, message: str, repo: DocumentsRepository, started: float) -> dict:
    doc["status"] = DocumentStatus.FAILED
    doc["error"] = {"stage": stage, "message": message, "at": now_iso()}
    doc["processing"]["total_duration_ms"] = int((time.perf_counter() - started) * 1000)
    log.warning("pipeline falhou id=%s stage=%s msg=%s", doc["_id"], stage, message)
    try:
        repo.replace(doc)
    except RepositoryUnavailableError:
        # A falha do estágio já está no log acima; a falha de persistência
        # vira 503 na API (nunca se reporta sucesso sem gravação).
        log.error("pipeline: falha ao persistir estado FAILED id=%s", doc["_id"])
        raise
    return doc
