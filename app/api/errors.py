"""Envelope de erro único da API (PLANO_IMPLEMENTACAO.md §F).

Formato: {"error": {"code": "...", "message": "...", "stage": "...|null"}}
"""

from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel


class ErrorBody(BaseModel):
    code: str
    message: str
    stage: str | None = None


class ErrorEnvelope(BaseModel):
    error: ErrorBody


class ProblemException(Exception):
    def __init__(self, status_code: int, code: str, message: str, stage: str | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.stage = stage


async def problem_exception_handler(_: Request, exc: ProblemException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message, "stage": exc.stage}},
    )


# Respostas de erro declaradas no OpenAPI para todas as rotas de documentos (P-10).
_DESCRIPTIONS = {
    400: "Requisição malformada (arquivo vazio, id inválido, corpo inválido)",
    404: "Documento não encontrado",
    409: "Conflito de estado (validar documento em falha / reprocessar sem arquivo original)",
    413: "Arquivo acima do limite configurado",
    415: "Tipo de arquivo não suportado",
    422: "Arquivo do tipo esperado mas ilegível / corpo inválido",
    503: "Dependência indisponível (MongoDB) — nada foi gravado",
}

ERROR_RESPONSES = {
    code: {"model": ErrorEnvelope, "description": description}
    for code, description in _DESCRIPTIONS.items()
}
