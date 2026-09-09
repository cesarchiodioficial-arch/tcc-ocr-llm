"""OCR com Tesseract (ESPECIFICACAO.md §6).

- PDF → imagem por página via `pdf2image` + Poppler.
- Imagens (PNG/JPG) abertas com Pillow.
- Pré-processamento simples opcional antes do Tesseract.
- Idioma `por` preferencial, com *fallback* para `eng` quando o pacote de
  idioma não estiver instalado.
"""

from __future__ import annotations

import io
import logging
import time

import pytesseract
from pdf2image import convert_from_bytes
from pdf2image.exceptions import (
    PDFInfoNotInstalledError,
    PDFPageCountError,
    PDFPopplerTimeoutError,
    PDFSyntaxError,
    PopplerNotInstalledError,
)
from PIL import Image, UnidentifiedImageError

from app.config import get_settings
from app.services.preprocess import preprocess

log = logging.getLogger("app.ocr")

_PDF_MAGIC = b"%PDF-"
_TESS_CONFIG = "--oem 1 --psm 6"


class OcrError(Exception):
    """Falha do mecanismo de OCR / ambiente (Tesseract ou Poppler)."""


class CorruptFileError(Exception):
    """Arquivo do tipo esperado mas ilegível."""


def _images_from_pdf(data: bytes) -> list[Image.Image]:
    settings = get_settings()
    try:
        return convert_from_bytes(
            data,
            dpi=settings.pdf_dpi,
            poppler_path=settings.poppler_path_or_none,
        )
    except (PDFInfoNotInstalledError, PopplerNotInstalledError) as exc:  # ambiente sem Poppler
        raise OcrError(f"Poppler não instalado: {exc}") from exc
    except PDFPopplerTimeoutError as exc:
        raise OcrError(f"timeout ao converter PDF: {exc}") from exc
    except (PDFPageCountError, PDFSyntaxError) as exc:
        raise CorruptFileError(f"PDF ilegível: {exc}") from exc


def _image_from_bytes(data: bytes) -> list[Image.Image]:
    try:
        img = Image.open(io.BytesIO(data))
        img.load()
        return [img]
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise CorruptFileError(f"imagem ilegível: {exc}") from exc


def _ocr_one(image: Image.Image, settings) -> str:
    if settings.ocr_preprocess:
        processed = preprocess(image, binarize=settings.ocr_binarize)
    else:
        processed = image.convert("L")
    try:
        return pytesseract.image_to_string(
            processed,
            lang=settings.ocr_lang,
            config=_TESS_CONFIG,
            timeout=settings.ocr_timeout_seconds,
        )
    except pytesseract.TesseractNotFoundError as exc:
        raise OcrError(f"Tesseract não encontrado: {exc}") from exc
    except RuntimeError as exc:  # timeout do pytesseract
        raise OcrError(f"timeout de OCR: {exc}") from exc
    except pytesseract.pytesseract.TesseractError as exc:
        if settings.ocr_lang != "eng":
            log.warning("OCR: idioma '%s' indisponível, usando 'eng'", settings.ocr_lang)
            try:
                return pytesseract.image_to_string(
                    processed, lang="eng", config=_TESS_CONFIG,
                    timeout=settings.ocr_timeout_seconds,
                )
            except pytesseract.pytesseract.TesseractError as exc2:
                raise OcrError(f"erro do Tesseract: {exc2}") from exc2
        raise OcrError(f"erro do Tesseract: {exc}") from exc


def run_ocr(file_bytes: bytes, mime_type: str) -> tuple[str, int, int]:
    """Executa o OCR. Retorna `(ocr_text, page_count, duration_ms)`.

    Levanta `CorruptFileError` (arquivo ilegível) ou `OcrError` (ambiente).
    """
    settings = get_settings()
    start = time.perf_counter()

    is_pdf = mime_type == "application/pdf" or file_bytes[:5] == _PDF_MAGIC
    images = _images_from_pdf(file_bytes) if is_pdf else _image_from_bytes(file_bytes)

    texts = [_ocr_one(img, settings) for img in images]
    ocr_text = "\n\n".join(t.strip() for t in texts).strip()
    duration_ms = int((time.perf_counter() - start) * 1000)
    return ocr_text, len(images), duration_ms


def has_useful_text(text: str) -> bool:
    settings = get_settings()
    stripped = (text or "").strip()
    return len(stripped) >= settings.ocr_min_chars and any(c.isalnum() for c in stripped)


def tesseract_available() -> bool:
    try:
        pytesseract.get_tesseract_version()
        return True
    except Exception:  # noqa: BLE001 - qualquer falha significa indisponível
        return False
