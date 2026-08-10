"""Plugin manifest schema and loader.

Each plugin must include a ``manifest.json`` in its root directory.
This module defines the expected schema and provides a validated loader.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)

VALID_PERMISSIONS: frozenset[str] = frozenset(
    {
        "indexing.file_processing",   # register custom file-type extractors
        "indexing.text_processing",   # pre/post-process extracted text
        "search.enrichment",          # augment hybrid search results
    }
)


@dataclass(frozen=True)
class PluginManifest:
    """Validated, immutable representation of a plugin's manifest.json."""

    name: str                              # unique slug, e.g. "my-file-plugin"
    display_name: str
    version: str
    entry_point: str                       # "module:ClassName"
    permissions: frozenset[str] = field(default_factory=frozenset)
    description: str = ""
    author: str = ""
    min_app_version: str = "0.0.0"

    @property
    def plugin_dir(self) -> Path | None:
        """Resolved at load time; None until set by the loader."""
        return self._plugin_dir  # type: ignore[attr-defined]


def load_manifest(plugin_dir: Path) -> PluginManifest:
    """Load and validate ``manifest.json`` from *plugin_dir*.

    Raises ``ValueError`` if required fields are missing or permissions are
    not drawn from ``VALID_PERMISSIONS``.
    """
    manifest_path = plugin_dir / "manifest.json"
    if not manifest_path.is_file():
        raise ValueError(f"No manifest.json in {plugin_dir}")

    try:
        raw = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {manifest_path}: {exc}") from exc

    for required in ("name", "display_name", "version", "entry_point"):
        if not raw.get(required):
            raise ValueError(f"manifest.json missing required field '{required}' in {plugin_dir}")

    permissions_raw: list[str] = raw.get("permissions", [])
    unknown = set(permissions_raw) - VALID_PERMISSIONS
    if unknown:
        raise ValueError(
            f"Plugin '{raw['name']}' declares unknown permission(s): {unknown}. "
            f"Valid: {VALID_PERMISSIONS}"
        )

    manifest = PluginManifest(
        name=raw["name"],
        display_name=raw["display_name"],
        version=raw["version"],
        entry_point=raw["entry_point"],
        permissions=frozenset(permissions_raw),
        description=raw.get("description", ""),
        author=raw.get("author", ""),
        min_app_version=raw.get("min_app_version", "0.0.0"),
    )
    # Attach the source directory as a hidden attribute so the loader can use it.
    object.__setattr__(manifest, "_plugin_dir", plugin_dir)
    return manifest
