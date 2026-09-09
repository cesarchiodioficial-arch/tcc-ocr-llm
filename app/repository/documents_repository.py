"""Persistência no MongoDB (ESPECIFICACAO.md §10 / §13).

Erros de conexão são explícitos: `RepositoryUnavailableError`. Nunca se
considera uma operação concluída quando a gravação não ocorreu
(CLAUDE.md §10).
"""

from __future__ import annotations

import logging

from pymongo import MongoClient
from pymongo.errors import PyMongoError

from app.config import get_settings
from app.utils.time_utils import now_iso

log = logging.getLogger("app.repository")


class RepositoryUnavailableError(Exception):
    """MongoDB indisponível ou erro de persistência."""


class DocumentNotFoundError(Exception):
    """Documento não encontrado."""


class DocumentsRepository:
    def __init__(self, client: MongoClient | None = None) -> None:
        settings = get_settings()
        self._client = client or MongoClient(
            settings.mongo_uri,
            serverSelectionTimeoutMS=3000,
            uuidRepresentation="standard",
        )
        self._collection = self._client[settings.mongo_db][settings.mongo_collection]

    def ping(self) -> bool:
        try:
            self._client.admin.command("ping")
            return True
        except PyMongoError as exc:
            log.warning("MongoDB indisponível: %s", exc)
            return False

    def insert(self, doc: dict) -> dict:
        try:
            self._collection.insert_one(doc)
        except PyMongoError as exc:
            raise RepositoryUnavailableError(str(exc)) from exc
        return doc

    def get(self, doc_id: str) -> dict:
        try:
            found = self._collection.find_one({"_id": doc_id})
        except PyMongoError as exc:
            raise RepositoryUnavailableError(str(exc)) from exc
        if not found:
            raise DocumentNotFoundError(doc_id)
        return found

    def replace(self, doc: dict) -> dict:
        doc["updated_at"] = now_iso()
        try:
            result = self._collection.replace_one({"_id": doc["_id"]}, doc)
        except PyMongoError as exc:
            raise RepositoryUnavailableError(str(exc)) from exc
        if result.matched_count == 0:
            raise DocumentNotFoundError(doc["_id"])
        return doc
