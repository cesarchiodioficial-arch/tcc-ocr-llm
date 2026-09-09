"""Health check (ESPECIFICACAO.md §11 — Health)."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app import __version__
from app.api.deps import get_repository
from app.repository.documents_repository import DocumentsRepository

router = APIRouter(tags=["health"])


@router.get("/health", summary="Disponibilidade da API e do MongoDB")
def health(repo: DocumentsRepository = Depends(get_repository)) -> JSONResponse:
    mongo_ok = repo.ping()
    body = {
        "status": "ok" if mongo_ok else "degraded",
        "mongo": "ok" if mongo_ok else "unavailable",
        "version": __version__,
    }
    return JSONResponse(body, status_code=200 if mongo_ok else 503)
