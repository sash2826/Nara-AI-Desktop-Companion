"""Centralised application configuration for the Enterprise AI Companion.

All environment variable reads are consolidated here. Using Pydantic BaseSettings
provides:
  - Fail-fast validation at startup when required vars are missing
  - SecretStr for credentials — values are masked in repr() and str(), preventing
    accidental exposure in logs or error messages
  - A single place to audit what configuration the application consumes

Usage:
    from enterprise_ai_companion.infrastructure.config import get_config

    config = get_config()
    # Auth is now Azure AD bearer token (forwarded via X-Azure-Token header).
    # apim_subscription_key is optional — kept for dev / legacy fallback.
"""

from __future__ import annotations

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppConfig(BaseSettings):
    """Application configuration loaded from environment variables and .env file."""

    # ── LLM / APIM ──────────────────────────────────────────────────────────
    apim_endpoint: str = Field(..., alias="EAC_APIM_ENDPOINT")
    # Subscription key is optional when Azure AD bearer tokens are used instead.
    apim_subscription_key: SecretStr | None = Field(None, alias="EAC_APIM_SUBSCRIPTION_KEY")
    llm_model_id: str = Field("gpt-5.4-mini_gb_2026-03-17", alias="EAC_LLM_MODEL_ID")

    # ── Graph provider ───────────────────────────────────────────────────────
    graph_provider: str = Field("sqlite", alias="EAC_GRAPH_PROVIDER")

    # ── Storage paths ────────────────────────────────────────────────────────
    qdrant_path: str | None = Field(None, alias="EAC_QDRANT_PATH")
    db_path: str | None = Field(None, alias="EAC_DB_PATH")
    migrations_dir: str | None = Field(None, alias="EAC_MIGRATIONS_DIR")

    # ── IPC security ─────────────────────────────────────────────────────────
    ipc_secret: str | None = Field(None, alias="EAC_IPC_SECRET")

    # ── System index paths (hidden from document browser) ────────────────────
    # Comma-separated absolute paths. Documents whose file_path starts with
    # any of these prefixes are excluded from GET /documents by default.
    # They remain fully indexed and searchable.
    system_index_paths: str = Field("", alias="EAC_SYSTEM_INDEX_PATHS")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )


_config: AppConfig | None = None


def get_config() -> AppConfig:
    """Return the singleton AppConfig, creating it on first call.

    Raises ValidationError if required environment variables are absent.
    """
    global _config
    if _config is None:
        _config = AppConfig()
    return _config


def reset_config() -> None:
    """Reset the singleton — intended for use in tests only."""
    global _config
    _config = None
