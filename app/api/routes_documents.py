"""Rotas REST dos documentos (ESPECIFICACAO.md §11).

POST   /api/v1/documents               — upload + processamento síncrono
GET    /api/v1/documents/{id}          — consulta
PUT    /api/v1/documents/{id}          — correção / confirmação humana
POST   /api/v1/documents/{id}/reprocess — reprocessamento
"""

from __future__ import annotations

import logging
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, UploadFile

from app.api.deps import get_llm_client, get_repository
from app.api.errors import ProblemException
from app.config import get_settings
from app.models.enums import DocumentStatus
from app.models.schemas import DocumentOut, ExtractedFields, UpdateRequest
from app.repository.documents_repository import (
    DocumentNotFoundError,
    DocumentsRepository,
    RepositoryUnavailableError,
)
from app.services import file_validation
from app.services.document_factory import new_document
from app.services.pipeline import process_document
from app.services.validation_service import validate_extracted
from app.storage import files as storage
from app.utils.time_utils import now_iso

log = logging.getLogger("app.api")

router = APIRouter(prefix="/api/v1", tags=["documents"])


def _serialize(doc: dict) -> dict:
    return DocumentOut.model_validate(doc).model_dump(by_alias=True)


def _require_uuid(doc_id: str) -> str:
    try:
        UUID(doc_id)
    except (ValueError, AttributeError, TypeError):
        raise ProblemException(400, "invalid_id", "id não é um UUID válido")
    return doc_id


def _load(repo: DocumentsRepository, doc_id: str) -> dict:
    try:
        return repo.get(doc_id)
    except DocumentNotFoundError:
        raise ProblemException(404, "not_found", "documento não encontrado")
    except RepositoryUnavailableError:
        raise ProblemException(503, "db_unavailable", "MongoDB indisponível", stage="persistence")


@router.post(
    "/documents",
    status_code=201,
    response_model=DocumentOut,
    summary="Enviar documento e processar (síncrono)",
)
def create_document(
    file: UploadFile = File(..., description="Nota fiscal em PDF, PNG ou JPG/JPEG"),
    repo: DocumentsRepository = Depends(get_repository),
    llm_client=Depends(get_llm_client),
) -> dict:
    settings = get_settings()
    data = file.file.read()

    if not data:
        raise ProblemException(400, "empty_file", "arquivo vazio")
    if len(data) > settings.max_upload_bytes:
        raise ProblemException(
            413, "file_too_large", f"arquivo excede o limite de {settings.max_upload_mb} MB"
        )

    mime = file_validation.detect_mime(data)
    if mime is None:
        raise ProblemException(
            415, "unsupported_type", "formato não suportado (use PDF, PNG ou JPG/JPEG)"
        )
    try:
        file_validation.verify_openable(mime, data)
    except file_validation.CorruptFileError as exc:
        raise ProblemException(422, "corrupt_file", str(exc))

    if not repo.ping():
        raise ProblemException(503, "db_unavailable", "MongoDB indisponível", stage="persistence")

    doc_id = str(uuid4())
    ext = storage.EXT_BY_MIME[mime]
    path = storage.save(doc_id, data, ext)
    doc = new_document(doc_id, file.filename or f"{doc_id}{ext}", path, mime, len(data))

    try:
        repo.insert(doc)
    except RepositoryUnavailableError:
        storage.delete(path)
        raise ProblemException(
            503, "db_unavailable", "falha ao persistir o documento", stage="persistence"
        )

    doc = process_document(doc, data, repo, llm_client=llm_client)
    return _serialize(doc)


@router.get(
    "/documents/{doc_id}",
    response_model=DocumentOut,
    summary="Consultar documento",
)
def get_document(
    doc_id: str,
    repo: DocumentsRepository = Depends(get_repository),
) -> dict:
    _require_uuid(doc_id)
    return _serialize(_load(repo, doc_id))


@router.put(
    "/documents/{doc_id}",
    response_model=DocumentOut,
    summary="Correção / confirmação humana",
)
def update_document(
    doc_id: str,
    body: UpdateRequest,
    repo: DocumentsRepository = Depends(get_repository),
) -> dict:
    _require_uuid(doc_id)
    doc = _load(repo, doc_id)

    updates = (
        body.extracted_data.model_dump(exclude_unset=True) if body.extracted_data is not None else {}
    )
    current = doc["extracted_data"]
    corrections = doc["validation"].setdefault("corrections", [])

    for field, new_value in updates.items():
        old_value = current.get(field)
        if old_value != new_value:
            corrections.append(
                {
                    "field": field,
                    "old_value": old_value,
                    "new_value": new_value,
                    "corrected_at": now_iso(),
                    "source": "human",
                }
            )
            current[field] = new_value

    try:
        revalidated = ExtractedFields.model_validate(current)
    except Exception:  # noqa: BLE001
        raise ProblemException(400, "invalid_data", "dados corrigidos não seguem o schema")

    checks = validate_extracted(revalidated)
    doc["extracted_data"] = revalidated.model_dump()
    doc["validation"]["schema_valid"] = True
    doc["validation"]["field_checks"] = {k: v.model_dump() for k, v in checks.items()}

    if body.validated:
        if doc["status"] == DocumentStatus.FAILED and not updates:
            raise ProblemException(
                409,
                "cannot_validate_failed",
                "corrija os campos antes de validar um documento em falha",
            )
        doc["validation"]["validated"] = True
        doc["validation"]["validated_by"] = "human"
        doc["validation"]["validated_at"] = now_iso()
        doc["status"] = str(DocumentStatus.VALIDATED)

    try:
        repo.replace(doc)
    except RepositoryUnavailableError:
        raise ProblemException(503, "db_unavailable", "falha ao persistir", stage="persistence")
    except DocumentNotFoundError:
        raise ProblemException(404, "not_found", "documento não encontrado")

    return _serialize(doc)


@router.post(
    "/documents/{doc_id}/reprocess",
    response_model=DocumentOut,
    summary="Reprocessar a partir do arquivo original",
)
def reprocess_document(
    doc_id: str,
    repo: DocumentsRepository = Depends(get_repository),
    llm_client=Depends(get_llm_client),
) -> dict:
    _require_uuid(doc_id)
    doc = _load(repo, doc_id)

    if not storage.exists(doc.get("file_path", "")):
        raise ProblemException(
            409, "original_missing", "arquivo original ausente; reenvie via POST /api/v1/documents"
        )

    data = storage.read(doc["file_path"])
    doc["processing"]["reprocess_count"] += 1
    doc["validation"]["validated"] = False
    doc["validation"]["validated_by"] = None
    doc["validation"]["validated_at"] = None

    doc = process_document(doc, data, repo, llm_client=llm_client)
    return _serialize(doc)
