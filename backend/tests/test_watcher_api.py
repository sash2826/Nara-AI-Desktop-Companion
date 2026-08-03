"""Endpoint tests for the /watcher router.

Injects a mock WatcherService into app.state *after* TestClient enters the
lifespan context — matching the pattern used in test_hybrid_search.py.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

from fastapi.testclient import TestClient

from enterprise_ai_companion.api.app import app
from enterprise_ai_companion.capabilities.indexing.file_watcher import WatchedFolder


def _make_watcher(folders: list[WatchedFolder] | None = None) -> MagicMock:
    """Build a minimal WatcherService mock for injection into app.state."""
    watcher = MagicMock()
    watcher.is_running = True
    watcher.watched_paths = [f.path for f in (folders or [])]
    watcher.add_folder = AsyncMock(
        return_value=WatchedFolder(
            id="test-id-1",
            path="/some/folder",
            auto_index=True,
            added_at="2026-01-01T00:00:00+00:00",
        )
    )
    watcher.remove_folder = AsyncMock(return_value=None)
    watcher.list_folders = AsyncMock(return_value=folders or [])
    return watcher


def _client_with_watcher(watcher: MagicMock) -> TestClient:
    """Return a TestClient that has watcher injected after lifespan starts."""
    c = TestClient(app)
    c.__enter__()
    app.state.watcher = watcher
    return c


class TestWatcherStatus:
    def test_status_running(self) -> None:
        watcher = _make_watcher()
        with TestClient(app) as c:
            app.state.watcher = watcher
            resp = c.get("/watcher/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["running"] is True
        assert data["watched_count"] == 0
        assert data["folders"] == []

    def test_status_with_folders(self) -> None:
        folders = [
            WatchedFolder(id="1", path="/docs", auto_index=True, added_at="2026-01-01T00:00:00+00:00")
        ]
        watcher = _make_watcher(folders)
        with TestClient(app) as c:
            app.state.watcher = watcher
            resp = c.get("/watcher/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["watched_count"] == 1
        assert "/docs" in data["folders"]


class TestAddFolder:
    def test_add_valid_folder(self) -> None:
        with TestClient(app) as c:
            app.state.watcher = _make_watcher()
            resp = c.post("/watcher/folders", json={"path": "/some/folder"})
        assert resp.status_code == 201
        data = resp.json()
        assert data["id"] == "test-id-1"
        assert data["path"] == "/some/folder"
        assert data["auto_index"] is True

    def test_add_folder_invalid_path_returns_422(self) -> None:
        watcher = _make_watcher()
        watcher.add_folder = AsyncMock(side_effect=ValueError("Path does not exist"))
        with TestClient(app) as c:
            app.state.watcher = watcher
            resp = c.post("/watcher/folders", json={"path": "/nonexistent/path"})
        assert resp.status_code == 422

    def test_add_folder_missing_body_returns_422(self) -> None:
        with TestClient(app) as c:
            app.state.watcher = _make_watcher()
            resp = c.post("/watcher/folders", json={})
        assert resp.status_code == 422


class TestRemoveFolder:
    def test_remove_existing_folder(self) -> None:
        with TestClient(app) as c:
            app.state.watcher = _make_watcher()
            resp = c.delete("/watcher/folders/test-id-1")
        assert resp.status_code == 204

    def test_remove_nonexistent_folder_returns_404(self) -> None:
        watcher = _make_watcher()
        watcher.remove_folder = AsyncMock(side_effect=KeyError("not found"))
        with TestClient(app) as c:
            app.state.watcher = watcher
            resp = c.delete("/watcher/folders/bad-id")
        assert resp.status_code == 404


class TestListFolders:
    def test_list_empty(self) -> None:
        with TestClient(app) as c:
            app.state.watcher = _make_watcher()
            resp = c.get("/watcher/folders")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_with_entries(self) -> None:
        folders = [
            WatchedFolder(id="1", path="/docs", auto_index=True, added_at="2026-01-01T00:00:00+00:00"),
            WatchedFolder(id="2", path="/notes", auto_index=False, added_at="2026-01-02T00:00:00+00:00"),
        ]
        with TestClient(app) as c:
            app.state.watcher = _make_watcher(folders)
            resp = c.get("/watcher/folders")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        paths = {d["path"] for d in data}
        assert paths == {"/docs", "/notes"}
