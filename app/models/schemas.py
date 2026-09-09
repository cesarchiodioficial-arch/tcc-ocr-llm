"""Schemas Pydantic da POC.

Campos essenciais (CLAUDE.md §6 / ESPECIFICACAO.md §7):
issuer_name, cnpj, issue_date, invoice_number, total_value.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

ESSENTIAL_FIELDS: tuple[str, ...] = (
    "issuer_name",
    "cnpj",
    "issue_date",
    "invoice_number",
    "total_value",
)


class ExtractedFields(BaseModel):
    """Dados estruturados dos 5 campos essenciais (armazenamento / saída / edição).

    Todos os campos são opcionais: ausência de evidência ⇒ `null` (o sistema
    nunca preenche valores presumidos — ESPECIFICACAO.md §8).
    """

    model_config = ConfigDict(extra="forbid")

    issuer_name: str | None = None
    cnpj: str | None = None
    issue_date: str | None = None
    invoice_number: str | None = None
    total_value: float | None = None


class ExtractedFieldsUpdate(BaseModel):
    """Correção humana parcial: só os campos presentes no corpo são alterados."""

    model_config = ConfigDict(extra="forbid")

    issuer_name: str | None = None
    cnpj: str | None = None
    issue_date: str | None = None
    invoice_number: str | None = None
    total_value: float | None = None


class UpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    extracted_data: ExtractedFieldsUpdate | None = None
    validated: bool = False


class FieldCheck(BaseModel):
    valid: bool
    reason: str | None = None


class Correction(BaseModel):
    field: str
    old_value: Any = None
    new_value: Any = None
    corrected_at: str
    source: str = "human"


class ValidationInfo(BaseModel):
    schema_valid: bool | None = None
    field_checks: dict[str, FieldCheck] = Field(default_factory=dict)
    validated: bool = False
    validated_by: str | None = None
    validated_at: str | None = None
    corrections: list[Correction] = Field(default_factory=list)


class LLMInfo(BaseModel):
    provider: str
    model: str
    attempts: int
    raw_response_excerpt: str | None = None


class ProcessingInfo(BaseModel):
    ocr_duration_ms: int = 0
    llm_duration_ms: int = 0
    total_duration_ms: int = 0
    reprocess_count: int = 0


class ErrorInfo(BaseModel):
    stage: str
    message: str
    at: str


class DocumentOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    id: str = Field(alias="_id")
    file_name: str
    file_path: str
    mime_type: str
    file_size_bytes: int
    source_pages: int | None = None
    status: str
    ocr_text: str | None = None
    extracted_data: ExtractedFields
    validation: ValidationInfo
    llm: LLMInfo | None = None
    processing: ProcessingInfo
    error: ErrorInfo | None = None
    created_at: str
    updated_at: str


class ErrorEnvelope(BaseModel):
    error: dict[str, Any]
