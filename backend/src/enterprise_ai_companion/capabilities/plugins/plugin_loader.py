"""Plugin discovery and loading.

Scans a directory tree for plugin subdirectories (each containing a
``manifest.json``), imports their entry-point class, validates that the class
implements the ABCs matching the declared permissions, and returns a list of
ready-to-use ``LoadedPlugin`` instances.

A plugin that fails at any stage is skipped and logged; it never crashes the
application startup.
"""

from __future__ import annotations

import importlib
import logging
import os
import sys
from dataclasses import dataclass
from pathlib import Path

from enterprise_ai_companion.capabilities.plugins.plugin_interfaces import (
    FileProcessorPlugin,
    SearchEnricherPlugin,
    TextProcessorPlugin,
)
from enterprise_ai_companion.capabilities.plugins.plugin_manifest import (
    PluginManifest,
    load_manifest,
)

logger = logging.getLogger(__name__)

# Maps a permission string to the ABC it requires the plugin to implement.
_PERMISSION_TO_ABC = {
    "indexing.file_processing": FileProcessorPlugin,
    "indexing.text_processing": TextProcessorPlugin,
    "search.enrichment": SearchEnricherPlugin,
}


@dataclass
class LoadedPlugin:
    """A validated and instantiated plugin."""

    manifest: PluginManifest
    instance: FileProcessorPlugin | TextProcessorPlugin | SearchEnricherPlugin
    enabled: bool = True  # kept in sync with the registry by PluginManager


def _default_scan_dir() -> Path:
    """Return the platform-appropriate plugin scan directory.

    On Windows: ``%APPDATA%\\Enterprise AI Companion\\plugins``
    Fallback: ``backend/plugins`` relative to this file's package root.
    """
    appdata = os.environ.get("APPDATA")
    if appdata:
        return Path(appdata) / "Enterprise AI Companion" / "plugins"
    return Path(__file__).parents[5] / "plugins"


def _resolve_entry_point(
    entry_point: str, plugin_dir: Path
) -> type:
    """Import and return the class named by ``module:ClassName``.

    Temporarily prepends *plugin_dir* to ``sys.path`` so the plugin's
    own modules are importable without installation.
    """
    if ":" not in entry_point:
        raise ValueError(
            f"entry_point must be 'module:ClassName', got '{entry_point}'"
        )
    module_name, class_name = entry_point.rsplit(":", 1)

    # Ensure the plugin directory is on sys.path for this import.
    plugin_dir_str = str(plugin_dir)
    inserted = False
    if plugin_dir_str not in sys.path:
        sys.path.insert(0, plugin_dir_str)
        inserted = True
    try:
        mod = importlib.import_module(module_name)
    finally:
        if inserted and plugin_dir_str in sys.path:
            sys.path.remove(plugin_dir_str)

    cls = getattr(mod, class_name, None)
    if cls is None:
        raise ImportError(
            f"Module '{module_name}' has no attribute '{class_name}'"
        )
    return cls


def _validate_permissions(manifest: PluginManifest, instance: object) -> list[str]:
    """Return a list of permission mismatches.

    A mismatch occurs when a permission is declared but the instance does
    not implement the corresponding ABC.
    """
    errors: list[str] = []
    for perm in manifest.permissions:
        required_abc = _PERMISSION_TO_ABC.get(perm)
        if required_abc and not isinstance(instance, required_abc):
            errors.append(
                f"Permission '{perm}' requires {required_abc.__name__} but "
                f"{type(instance).__name__} does not implement it"
            )
    return errors


def scan_plugins(scan_dir: Path | None = None) -> list[LoadedPlugin]:
    """Discover and load all plugins found in *scan_dir*.

    Returns only plugins that pass manifest validation, import successfully,
    and implement all declared permission ABCs.
    """
    if scan_dir is None:
        scan_dir = _default_scan_dir()

    if not scan_dir.exists():
        logger.info("Plugin scan directory does not exist: %s — skipping", scan_dir)
        return []

    loaded: list[LoadedPlugin] = []
    for candidate in sorted(scan_dir.iterdir()):
        if not candidate.is_dir():
            continue
        try:
            manifest = load_manifest(candidate)
        except ValueError as exc:
            logger.warning("Skipping plugin in %s: %s", candidate.name, exc)
            continue

        try:
            cls = _resolve_entry_point(manifest.entry_point, candidate)
            instance = cls()
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Failed to load plugin '%s' (%s): %s",
                manifest.name,
                manifest.entry_point,
                exc,
            )
            continue

        mismatches = _validate_permissions(manifest, instance)
        if mismatches:
            for msg in mismatches:
                logger.warning("Plugin '%s' skipped — %s", manifest.name, msg)
            continue

        loaded.append(LoadedPlugin(manifest=manifest, instance=instance))
        logger.info(
            "Loaded plugin '%s' v%s (%s)",
            manifest.display_name,
            manifest.version,
            ", ".join(manifest.permissions) or "no permissions",
        )

    logger.info("Plugin scan complete: %d plugin(s) loaded from %s", len(loaded), scan_dir)
    return loaded
