"""Health check (ESPECIFICACAO.md §11 — Health)."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app import __version__
from app.api.deps import get_repository
from app.config import get_settings
from app.repository.documents_repository import DocumentsRepository

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    summary="Disponibilidade da API e do MongoDB",
    responses={
        200: {"description": "API e MongoDB disponíveis"},
        503: {"description": "MongoDB indisponível"},
    },
)
def health(repo: DocumentsRepository = Depends(get_repository)) -> JSONResponse:
    settings = get_settings()
    mongo_ok = repo.ping()
    body = {
        "status": "ok" if mongo_ok else "degraded",
        "mongo": "ok" if mongo_ok else "unavailable",
        "llm_provider": settings.llm_provider,
        "llm_configured": settings.llm_provider == "fake" or settings.llm_api_key_configured,
        "version": __version__,
    }
    return JSONResponse(body, status_code=200 if mongo_ok else 503)
