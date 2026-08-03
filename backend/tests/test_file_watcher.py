"""Unit tests for WatcherService and DebounceHandler."""

import asyncio
import os
import threading
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import aiosqlite
import pytest

from enterprise_ai_companion.capabilities.indexing.file_watcher import (
    EXCLUDED_DIRS,
    DebounceHandler,
    WatchedFolder,
    WatcherService,
    _is_excluded,
)
from enterprise_ai_companion.infrastructure.database import open_db


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
async def db():
    os.environ["EAC_DB_PATH"] = ":memory:"
    conn = await open_db()
    yield conn
    await conn.close()
    del os.environ["EAC_DB_PATH"]


@pytest.fixture
def mock_indexer():
    indexer = MagicMock()
    indexer.index_workspace = AsyncMock(return_value=None)
    return indexer


@pytest.fixture
async def watcher_service(db, mock_indexer):
    loop = asyncio.get_running_loop()
    with patch("enterprise_ai_companion.capabilities.indexing.file_watcher.Observer") as MockObserver:
        mock_observer = MagicMock()
        MockObserver.return_value = mock_observer
        svc = WatcherService(db=db, indexer=mock_indexer, loop=loop)
        svc._observer = mock_observer
        yield svc, mock_observer


# ---------------------------------------------------------------------------
# _is_excluded
# ---------------------------------------------------------------------------

class TestIsExcluded:
    def test_excluded_dir_name(self) -> None:
        assert _is_excluded("C:/Windows/System32/file.txt") is True

    def test_excluded_appdata(self) -> None:
        assert _is_excluded("C:/Users/user/AppData/Local/file.txt") is True

    def test_git_dir(self) -> None:
        assert _is_excluded("/home/user/project/.git/config") is True

    def test_venv_dir(self) -> None:
        assert _is_excluded("/project/.venv/lib/site.py") is True

    def test_normal_path_not_excluded(self) -> None:
        assert _is_excluded("C:/Users/user/Documents/notes.txt") is False

    def test_excluded_dirs_constant_not_empty(self) -> None:
        assert len(EXCLUDED_DIRS) > 0


# ---------------------------------------------------------------------------
# DebounceHandler
# ---------------------------------------------------------------------------

def _make_handler(mock_indexer: MagicMock) -> DebounceHandler:
    """Create a DebounceHandler with a fresh non-running loop (timers only)."""
    loop = asyncio.new_event_loop()
    return DebounceHandler(folder_path="/some/folder", indexer=mock_indexer, loop=loop)


class TestDebounceHandler:
    def test_skips_excluded_path(self, mock_indexer) -> None:
        handler = _make_handler(mock_indexer)
        event = MagicMock()
        event.is_directory = False
        event.src_path = "C:/Windows/System32/hosts"
        handler.on_modified(event)
        assert len(handler._timers) == 0

    def test_skips_unsupported_extension(self, mock_indexer) -> None:
        handler = _make_handler(mock_indexer)
        event = MagicMock()
        event.is_directory = False
        event.src_path = "/some/folder/image.png"
        handler.on_modified(event)
        assert len(handler._timers) == 0

    def test_schedules_timer_for_supported_file(self, mock_indexer) -> None:
        handler = _make_handler(mock_indexer)
        event = MagicMock()
        event.is_directory = False
        event.src_path = "/some/folder/notes.txt"
        handler.on_modified(event)
        assert "/some/folder/notes.txt" in handler._timers
        handler.cancel_all()

    def test_debounce_resets_on_rapid_events(self, mock_indexer) -> None:
        handler = _make_handler(mock_indexer)
        event = MagicMock()
        event.is_directory = False
        event.src_path = "/some/folder/doc.md"
        handler.on_modified(event)
        first_timer = handler._timers.get("/some/folder/doc.md")
        handler.on_modified(event)
        second_timer = handler._timers.get("/some/folder/doc.md")
        assert second_timer is not first_timer
        handler.cancel_all()

    def test_cancel_all_clears_timers(self, mock_indexer) -> None:
        handler = _make_handler(mock_indexer)
        event = MagicMock()
        event.is_directory = False
        event.src_path = "/some/folder/notes.txt"
        handler.on_modified(event)
        assert len(handler._timers) == 1
        handler.cancel_all()
        assert len(handler._timers) == 0

    def test_directory_events_ignored(self, mock_indexer) -> None:
        handler = _make_handler(mock_indexer)
        event = MagicMock()
        event.is_directory = True
        event.src_path = "/some/folder/subdir"
        handler.on_modified(event)
        assert len(handler._timers) == 0


# ---------------------------------------------------------------------------
# WatcherService
# ---------------------------------------------------------------------------

class TestWatcherServiceStart:
    async def test_start_with_no_folders(self, watcher_service) -> None:
        svc, mock_observer = watcher_service
        await svc._async_start()
        mock_observer.start.assert_called_once()
        assert svc.is_running is True
        assert svc.watched_paths == []

    async def test_stop_calls_observer_stop(self, watcher_service) -> None:
        svc, mock_observer = watcher_service
        await svc._async_start()
        svc.stop()
        mock_observer.stop.assert_called_once()
        mock_observer.join.assert_called_once()
        assert svc.is_running is False


class TestWatcherServiceFolders:
    async def test_add_folder_persists_to_db(self, watcher_service, tmp_path) -> None:
        svc, mock_observer = watcher_service
        await svc._async_start()
        folder = await svc.add_folder(str(tmp_path))
        assert isinstance(folder, WatchedFolder)
        assert folder.path == str(tmp_path)
        assert folder.auto_index is True

        folders = await svc.list_folders()
        assert len(folders) == 1
        assert folders[0].path == str(tmp_path)
        svc.stop()

    async def test_add_nonexistent_path_raises(self, watcher_service) -> None:
        svc, _ = watcher_service
        await svc._async_start()
        with pytest.raises(ValueError, match="does not exist"):
            await svc.add_folder("/nonexistent/path/that/does/not/exist")
        svc.stop()

    async def test_remove_folder_deletes_from_db(self, watcher_service, tmp_path) -> None:
        svc, mock_observer = watcher_service
        await svc._async_start()
        folder = await svc.add_folder(str(tmp_path))
        await svc.remove_folder(folder.id)
        folders = await svc.list_folders()
        assert len(folders) == 0
        svc.stop()

    async def test_remove_nonexistent_folder_raises(self, watcher_service) -> None:
        svc, _ = watcher_service
        await svc._async_start()
        with pytest.raises(KeyError):
            await svc.remove_folder("nonexistent-id")
        svc.stop()

    async def test_list_folders_empty_by_default(self, watcher_service) -> None:
        svc, _ = watcher_service
        folders = await svc.list_folders()
        assert folders == []
