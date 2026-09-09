"""Configuração central da aplicação, carregada de variáveis de ambiente.

Ponto único de configuração (CLAUDE.md §8 / ESPECIFICACAO.md §4). Nenhum
segredo é escrito no código: valores sensíveis vêm de ambiente / `.env`.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # App
    app_env: str = "development"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    log_level: str = "INFO"
    max_upload_mb: int = 10

    # MongoDB
    mongo_uri: str = "mongodb://localhost:27017"
    mongo_db: str = "tcc_ocr_llm"
    mongo_collection: str = "documents"

    # Armazenamento de arquivos originais
    upload_dir: str = "./uploads"

    # OCR
    ocr_lang: str = "por"
    ocr_preprocess: bool = True
    ocr_min_chars: int = 20
    ocr_timeout_seconds: int = 60
    pdf_dpi: int = 300
    poppler_path: str | None = None

    # LLM (camada isolada)
    llm_provider: str = "openai"  # openai | fake
    llm_api_key: str = "changeme"
    llm_base_url: str = "https://api.openai.com/v1"
    llm_model: str = "gpt-4o-mini"
    llm_timeout_seconds: int = 30
    llm_max_retries: int = 2

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024

    @property
    def poppler_path_or_none(self) -> str | None:
        return self.poppler_path or None

    @property
    def llm_api_key_configured(self) -> bool:
        return bool(self.llm_api_key) and self.llm_api_key.lower() not in {"changeme", "", "none"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
