"""Criação do registro inicial de um documento (estrutura da ESPECIFICACAO.md §10)."""

from __future__ import annotations

from app.models.enums import DocumentStatus
from app.models.schemas import ESSENTIAL_FIELDS
from app.utils.time_utils import now_iso


def new_document(
    doc_id: str,
    file_name: str,
    file_path: str,
    mime_type: str,
    file_size_bytes: int,
) -> dict:
    timestamp = now_iso()
    return {
        "_id": doc_id,
        "file_name": file_name,
        "file_path": file_path,
        "mime_type": mime_type,
        "file_size_bytes": file_size_bytes,
        "source_pages": None,
        "status": str(DocumentStatus.RECEIVED),
        "ocr_text": None,
        "extracted_data": {field: None for field in ESSENTIAL_FIELDS},
        "validation": {
            "schema_valid": None,
            "field_checks": {},
            "validated": False,
            "validated_by": None,
            "validated_at": None,
            "corrections": [],
        },
        "llm": None,
        "processing": {
            "ocr_duration_ms": 0,
            "llm_duration_ms": 0,
            "total_duration_ms": 0,
            "reprocess_count": 0,
        },
        "error": None,
        "created_at": timestamp,
        "updated_at": timestamp,
    }
