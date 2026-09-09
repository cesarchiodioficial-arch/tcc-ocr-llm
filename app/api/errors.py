"""Envelope de erro único da API (PLANO_IMPLEMENTACAO.md §F).

Formato: {"error": {"code": "...", "message": "...", "stage": "...|null"}}
"""

from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse


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
