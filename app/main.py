"""Aplicação FastAPI (ESPECIFICACAO.md §4 / §11).

Monólito modular: API → processamento → OCR → LLM → validação → revisão
humana → persistência, tudo no mesmo processo.
"""

from __future__ import annotations

from fastapi import FastAPI

from app import __version__
from app.api.errors import ProblemException, problem_exception_handler
from app.api.routes_documents import router as documents_router
from app.api.routes_health import router as health_router
from app.logging_config import configure_logging

DESCRIPTION = (
    "POC do TCC — extração automática de dados em notas fiscais com OCR (Tesseract) "
    "e LLM. Fluxo: documento → OCR → LLM → validação sistêmica → validação humana → "
    "MongoDB. Campos: issuer_name, cnpj, issue_date, invoice_number, total_value."
)


def create_app() -> FastAPI:
    configure_logging()
    app = FastAPI(
        title="POC OCR + LLM — Notas Fiscais",
        version=__version__,
        description=DESCRIPTION,
        openapi_url="/openapi.json",
        docs_url="/docs",
    )
    app.add_exception_handler(ProblemException, problem_exception_handler)
    app.include_router(health_router)
    app.include_router(documents_router)
    return app


app = create_app()
