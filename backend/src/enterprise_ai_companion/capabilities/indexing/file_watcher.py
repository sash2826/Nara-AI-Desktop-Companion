"""Background file watcher that triggers automatic re-indexing on filesystem changes.

Uses watchdog to monitor watched folders in a dedicated OS thread. File events are
debounced (2 s quiet window) and then dispatched back onto the asyncio event loop
so the async FileIndexer can be called safely from the sync observer thread.
"""

from __future__ import annotations

import asyncio
import logging
import threading
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import aiosqlite
from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from enterprise_ai_companion.capabilities.indexing.file_indexer import (
    FileIndexer,
    SUPPORTED_EXTENSIONS,
)

logger = logging.getLogger(__name__)

# Directories whose names are never watched or re-indexed regardless of depth.
EXCLUDED_DIRS: frozenset[str] = frozenset({
    "node_modules",
    ".git",
    ".venv",
    "__pycache__",
    "$Recycle.Bin",
    "Windows",
    "Program Files",
    "Program Files (x86)",
    "AppData",
    "System Volume Information",
})

_DEBOUNCE_SECONDS = 2.0


@dataclass
class WatchedFolder:
    """A folder registered for automatic background indexing."""

    id: str
    path: str
    auto_index: bool
    added_at: str


def _is_excluded(path: str) -> bool:
    """Return True if any segment of path is in EXCLUDED_DIRS."""
    return any(part in EXCLUDED_DIRS for part in Path(path).parts)


class DebounceHandler(FileSystemEventHandler):
    """Watchdog event handler with per-path debouncing.

    Consecutive events for the same source path within _DEBOUNCE_SECONDS are
    collapsed into a single index call — prevents double-indexing on editor
    save (temp file + rename pattern).
    """

    def __init__(
        self,
        folder_path: str,
        indexer: FileIndexer,
        loop: asyncio.AbstractEventLoop,
    ) -> None:
        super().__init__()
        self._folder_path = folder_path
        self._indexer = indexer
        self._loop = loop
        self._timers: dict[str, threading.Timer] = {}
        self._lock = threading.Lock()

    def on_modified(self, event: FileSystemEvent) -> None:
        if not event.is_directory:
            self._schedule(event.src_path)

    def on_created(self, event: FileSystemEvent) -> None:
        if not event.is_directory:
            self._schedule(event.src_path)

    def _schedule(self, src_path: str) -> None:
        if _is_excluded(src_path):
            return
        ext = Path(src_path).suffix.lower()
        if ext not in SUPPORTED_EXTENSIONS:
            return

        with self._lock:
            existing = self._timers.get(src_path)
            if existing is not None:
                existing.cancel()
            timer = threading.Timer(_DEBOUNCE_SECONDS, self._fire, args=[src_path])
            self._timers[src_path] = timer
            timer.start()

    def _fire(self, src_path: str) -> None:
        with self._lock:
            self._timers.pop(src_path, None)
        logger.debug("File change detected, re-indexing folder: %s (triggered by %s)",
                     self._folder_path, Path(src_path).name)
        coro = self._indexer.index_workspace(self._folder_path)
        asyncio.run_coroutine_threadsafe(coro, self._loop)

    def cancel_all(self) -> None:
        """Cancel pending debounce timers — called when a watch is removed."""
        with self._lock:
            for timer in self._timers.values():
                timer.cancel()
            self._timers.clear()


class WatcherService:
    """Manages the watchdog Observer and the set of watched folders.

    Persists the folder list to SQLite so watched folders survive application
    restarts. The Observer runs in its own OS thread (watchdog default); asyncio
    bridge via run_coroutine_threadsafe.
    """

    def __init__(
        self,
        db: aiosqlite.Connection,
        indexer: FileIndexer,
        loop: asyncio.AbstractEventLoop,
    ) -> None:
        self._db = db
        self._indexer = indexer
        self._loop = loop
        self._observer: Observer = Observer()
        # Maps folder path → (watchdog WatchHandle, DebounceHandler)
        self._watches: dict[str, tuple[Any, DebounceHandler]] = {}
        self._running = False

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Load persisted folders and start the watchdog Observer.

        Safe to call from inside a running event loop (FastAPI lifespan) or from
        a separate thread. When called from within the running loop, uses
        asyncio.run_coroutine_threadsafe via a dedicated thread to avoid
        deadlocking the loop.
        """
        try:
            running_loop = asyncio.get_running_loop()
        except RuntimeError:
            running_loop = None

        if running_loop is self._loop:
            # We're inside the target loop — schedule the load as a task.
            # The observer start is deferred to after the task completes.
            asyncio.ensure_future(self._async_start(), loop=self._loop)
        else:
            # Called from a non-async context or a different thread.
            folders = asyncio.run_coroutine_threadsafe(
                self._load_folders(), self._loop
            ).result(timeout=5)
            for folder in folders:
                if folder.auto_index:
                    self._schedule_watch(folder.path)
            self._observer.start()
            self._running = True
            logger.info("WatcherService started — watching %d folder(s)", len(self._watches))

    async def _async_start(self) -> None:
        """Async start path — used when start() is called from inside the event loop."""
        folders = await self._load_folders()
        for folder in folders:
            if folder.auto_index:
                self._schedule_watch(folder.path)
        self._observer.start()
        self._running = True
        logger.info("WatcherService started — watching %d folder(s)", len(self._watches))

    def stop(self) -> None:
        """Stop the Observer and cancel all pending debounce timers."""
        for _, (_, handler) in self._watches.items():
            handler.cancel_all()
        self._watches.clear()

        if self._running:
            self._observer.stop()
            self._observer.join()
            self._running = False
            logger.info("WatcherService stopped.")

    # ------------------------------------------------------------------
    # Public API (async — called from FastAPI request handlers)
    # ------------------------------------------------------------------

    async def add_folder(self, path: str) -> WatchedFolder:
        """Register a new folder for watching. Triggers an immediate initial index."""
        resolved = str(Path(path).resolve())
        if not Path(resolved).is_dir():
            raise ValueError(f"Path does not exist or is not a directory: {resolved}")

        folder = WatchedFolder(
            id=str(uuid.uuid4()),
            path=resolved,
            auto_index=True,
            added_at=datetime.now(UTC).isoformat(),
        )
        await self._db.execute(
            "INSERT OR IGNORE INTO watched_folders (id, path, auto_index, added_at) "
            "VALUES (?, ?, ?, ?)",
            (folder.id, folder.path, int(folder.auto_index), folder.added_at),
        )
        await self._db.commit()

        if self._running and folder.path not in self._watches:
            self._schedule_watch(folder.path)

        # Trigger initial index without blocking the response.
        asyncio.create_task(self._indexer.index_workspace(folder.path))
        logger.info("Watched folder added: %s", folder.path)
        return folder

    async def remove_folder(self, folder_id: str) -> None:
        """Unregister a folder and stop watching it."""
        async with self._db.execute(
            "SELECT path FROM watched_folders WHERE id = ?", (folder_id,)
        ) as cur:
            row = await cur.fetchone()

        if row is None:
            raise KeyError(f"Watched folder not found: {folder_id}")

        path = row[0]
        await self._db.execute(
            "DELETE FROM watched_folders WHERE id = ?", (folder_id,)
        )
        await self._db.commit()

        self._unschedule_watch(path)
        logger.info("Watched folder removed: %s", path)

    async def list_folders(self) -> list[WatchedFolder]:
        """Return all registered watched folders."""
        return await self._load_folders()

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def watched_paths(self) -> list[str]:
        return list(self._watches.keys())

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _load_folders(self) -> list[WatchedFolder]:
        async with self._db.execute(
            "SELECT id, path, auto_index, added_at FROM watched_folders"
        ) as cur:
            rows = await cur.fetchall()
        return [
            WatchedFolder(
                id=row[0],
                path=row[1],
                auto_index=bool(row[2]),
                added_at=row[3],
            )
            for row in rows
        ]

    def _schedule_watch(self, path: str) -> None:
        if path in self._watches:
            return
        handler = DebounceHandler(path, self._indexer, self._loop)
        watch = self._observer.schedule(handler, path, recursive=True)
        self._watches[path] = (watch, handler)
        logger.debug("Scheduled watchdog watch on: %s", path)

    def _unschedule_watch(self, path: str) -> None:
        entry = self._watches.pop(path, None)
        if entry is None:
            return
        watch, handler = entry
        handler.cancel_all()
        self._observer.unschedule(watch)
        logger.debug("Unscheduled watchdog watch on: %s", path)
