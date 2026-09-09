"""Validação do arquivo de entrada (ESPECIFICACAO.md §5 / §13).

Formatos aceitos: PDF, PNG, JPG/JPEG. O tipo é detectado pelos *magic bytes*
(não confiando apenas na extensão). Arquivos vazios, não suportados ou
corrompidos são rejeitados.
"""

from __future__ import annotations

import io

from PIL import Image, UnidentifiedImageError

_PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
_JPEG_MAGIC = b"\xff\xd8\xff"
_PDF_MAGIC = b"%PDF-"


class CorruptFileError(Exception):
    """Arquivo do tipo esperado mas ilegível."""


def detect_mime(data: bytes) -> str | None:
    if data.startswith(_PDF_MAGIC):
        return "application/pdf"
    if data.startswith(_PNG_MAGIC):
        return "image/png"
    if data.startswith(_JPEG_MAGIC):
        return "image/jpeg"
    return None


def verify_openable(mime: str, data: bytes) -> None:
    """Checagem barata de integridade feita ANTES de criar o registro.

    Para imagens: tenta abrir/verificar com Pillow.
    Para PDF: apenas confirma o cabeçalho (a integridade completa é
    verificada no pipeline de OCR, virando estado FAILED se falhar).
    """
    if mime in ("image/png", "image/jpeg"):
        try:
            with Image.open(io.BytesIO(data)) as img:
                img.verify()
        except (UnidentifiedImageError, OSError, ValueError) as exc:
            raise CorruptFileError(f"imagem ilegível: {exc}") from exc
    elif mime == "application/pdf":
        if not data.startswith(_PDF_MAGIC):
            raise CorruptFileError("PDF sem cabeçalho válido")
        # Heurística barata para PDF truncado: todo PDF válido termina com o
        # marcador %%EOF. A integridade completa é verificada no OCR.
        if b"%%EOF" not in data[-1024:]:
            raise CorruptFileError("PDF truncado ou incompleto (sem marcador %%EOF)")
