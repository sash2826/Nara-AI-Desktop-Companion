"""Plugin manager — orchestrates the loader and registry.

``PluginManager`` is the single entry point for the rest of the application.
It is initialised once during the FastAPI lifespan and placed on
``app.state.plugin_manager``.  All other modules retrieve active plugins
through the typed accessor methods rather than interacting with the loader
or registry directly.
"""

from __future__ import annotations

import logging
from pathlib import Path

import aiosqlite

from enterprise_ai_companion.capabilities.plugins.plugin_interfaces import (
    FileProcessorPlugin,
    SearchEnricherPlugin,
    TextProcessorPlugin,
)
from enterprise_ai_companion.capabilities.plugins.plugin_loader import (
    LoadedPlugin,
    scan_plugins,
)
from enterprise_ai_companion.capabilities.plugins.plugin_registry import (
    PluginRecord,
    PluginRegistry,
)

logger = logging.getLogger(__name__)


class PluginManager:
    """Manages the full plugin lifecycle: discovery, persistence, and access."""

    def __init__(self, conn: aiosqlite.Connection, scan_dir: Path | None = None) -> None:
        self._registry = PluginRegistry(conn)
        self._scan_dir = scan_dir
        self._loaded: list[LoadedPlugin] = []

    async def initialize(self) -> dict[str, int]:
        """Scan for plugins, register them, and return summary counts.

        Returns:
            A dict with ``found`` and ``loaded`` counts for startup logging.
        """
        self._loaded = scan_plugins(self._scan_dir)

        for lp in self._loaded:
            try:
                await self._registry.register(lp.manifest)
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "Failed to register plugin '%s' in database: %s", lp.manifest.name, exc
                )

        return {"found": len(self._loaded), "loaded": len(self._loaded)}

    # ------------------------------------------------------------------
    # Typed accessors — return only enabled plugins of the requested type
    # ------------------------------------------------------------------

    def get_file_processors(self) -> list[FileProcessorPlugin]:
        """Return enabled plugins that implement ``FileProcessorPlugin``."""
        return [
            lp.instance  # type: ignore[return-value]
            for lp in self._loaded
            if lp.enabled
            and isinstance(lp.instance, FileProcessorPlugin)
            and "indexing.file_processing" in lp.manifest.permissions
        ]

    def get_text_processors(self) -> list[TextProcessorPlugin]:
        """Return enabled plugins that implement ``TextProcessorPlugin``."""
        return [
            lp.instance  # type: ignore[return-value]
            for lp in self._loaded
            if lp.enabled
            and isinstance(lp.instance, TextProcessorPlugin)
            and "indexing.text_processing" in lp.manifest.permissions
        ]

    def get_search_enrichers(self) -> list[SearchEnricherPlugin]:
        """Return enabled plugins that implement ``SearchEnricherPlugin``."""
        return [
            lp.instance  # type: ignore[return-value]
            for lp in self._loaded
            if lp.enabled
            and isinstance(lp.instance, SearchEnricherPlugin)
            and "search.enrichment" in lp.manifest.permissions
        ]

    # ------------------------------------------------------------------
    # Registry pass-throughs used by the REST API
    # ------------------------------------------------------------------

    async def list_plugins(self) -> list[PluginRecord]:
        """Return all registered plugins from the database."""
        return await self._registry.list_all()

    async def set_enabled(self, plugin_id: str, enabled: bool) -> None:
        """Toggle a plugin's enabled state in the database.

        NOTE: The change takes effect for the *loaded* list at the next
        application restart, since plugins are imported once at startup.
        """
        await self._registry.set_enabled(plugin_id, enabled)

        # Immediately reflect the toggle in the in-memory list so the
        # typed accessors respect the new state without requiring a restart.
        for lp in self._loaded:
            if lp.manifest.name == plugin_id:
                lp.enabled = enabled
                break
