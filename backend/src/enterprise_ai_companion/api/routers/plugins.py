"""API endpoints for plugin management."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

router = APIRouter(prefix="/plugins", tags=["plugins"])


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------


class PluginResponse(BaseModel):
    id: str
    display_name: str
    version: str
    description: str
    author: str
    permissions: list[str]
    enabled: bool
    installed_at: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("", response_model=list[PluginResponse])
async def list_plugins(request: Request) -> list[PluginResponse]:
    """Return all registered plugins and their current enabled state."""
    manager = getattr(request.app.state, "plugin_manager", None)
    if manager is None:
        return []

    records = await manager.list_plugins()
    return [
        PluginResponse(
            id=rec.id,
            display_name=rec.display_name,
            version=rec.version,
            description=rec.description,
            author=rec.author,
            permissions=rec.permissions,
            enabled=rec.enabled,
            installed_at=rec.installed_at,
        )
        for rec in records
    ]


@router.post("/{plugin_id}/enable", response_model=PluginResponse)
async def enable_plugin(plugin_id: str, request: Request) -> PluginResponse:
    """Enable a registered plugin."""
    manager = getattr(request.app.state, "plugin_manager", None)
    if manager is None:
        raise HTTPException(status_code=503, detail="Plugin manager not available")

    try:
        await manager.set_enabled(plugin_id, enabled=True)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Plugin '{plugin_id}' not found")

    records = await manager.list_plugins()
    for rec in records:
        if rec.id == plugin_id:
            return PluginResponse(
                id=rec.id,
                display_name=rec.display_name,
                version=rec.version,
                description=rec.description,
                author=rec.author,
                permissions=rec.permissions,
                enabled=rec.enabled,
                installed_at=rec.installed_at,
            )
    raise HTTPException(status_code=404, detail=f"Plugin '{plugin_id}' not found")


@router.post("/{plugin_id}/disable", response_model=PluginResponse)
async def disable_plugin(plugin_id: str, request: Request) -> PluginResponse:
    """Disable a registered plugin."""
    manager = getattr(request.app.state, "plugin_manager", None)
    if manager is None:
        raise HTTPException(status_code=503, detail="Plugin manager not available")

    try:
        await manager.set_enabled(plugin_id, enabled=False)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Plugin '{plugin_id}' not found")

    records = await manager.list_plugins()
    for rec in records:
        if rec.id == plugin_id:
            return PluginResponse(
                id=rec.id,
                display_name=rec.display_name,
                version=rec.version,
                description=rec.description,
                author=rec.author,
                permissions=rec.permissions,
                enabled=rec.enabled,
                installed_at=rec.installed_at,
            )
    raise HTTPException(status_code=404, detail=f"Plugin '{plugin_id}' not found")
