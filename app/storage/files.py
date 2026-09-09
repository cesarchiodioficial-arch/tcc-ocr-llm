"""Armazenamento do arquivo original no volume.

Guardar o arquivo original permite o reprocessamento sem novo upload
(ESPECIFICACAO.md §11 — `POST /{id}/reprocess`).
"""

from __future__ import annotations

from pathlib import Path

from app.config import get_settings

EXT_BY_MIME: dict[str, str] = {
    "application/pdf": ".pdf",
    "image/png": ".png",
    "image/jpeg": ".jpg",
}


def _base_dir() -> Path:
    path = Path(get_settings().upload_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def save(doc_id: str, data: bytes, ext: str) -> str:
    path = _base_dir() / f"{doc_id}{ext}"
    path.write_bytes(data)
    return str(path)


def read(path: str) -> bytes:
    return Path(path).read_bytes()


def exists(path: str) -> bool:
    return bool(path) and Path(path).is_file()


def delete(path: str) -> None:
    try:
        Path(path).unlink()
    except FileNotFoundError:
        pass
