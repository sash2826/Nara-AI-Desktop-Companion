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

    # ── Cluster discovery (Phase 10 / Scenario 3) ────────────────────────────
    # Weight of entity-overlap signal vs cosine similarity in the pairwise
    # distance matrix: combined = weight × entity_overlap + (1-weight) × cosine.
    # Calibrated against benchmark Suite 1 in Phase I; default mirrors the
    # placement scorer's graph/rerank split (0.75/0.25).
    cluster_entity_weight: float = Field(0.75, alias="EAC_CLUSTER_ENTITY_WEIGHT")

    # Agglomerative linkage distance threshold above which clusters are not
    # merged. Values in [0, 1]; lower = tighter clusters, fewer proposals.
    # Calibrated in Phase I — treat this default as a placeholder.
    cluster_distance_threshold: float = Field(0.45, alias="EAC_CLUSTER_DISTANCE_THRESHOLD")

    # Kill switch for LLM-based folder naming. Must remain False until data
    # governance approval is confirmed. When False, deterministic naming is used.
    cluster_naming_llm_enabled: bool = Field(False, alias="EAC_CLUSTER_NAMING_LLM_ENABLED")

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
