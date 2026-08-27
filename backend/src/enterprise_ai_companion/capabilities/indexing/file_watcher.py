"""Background file watcher that triggers automatic re-indexing on filesystem changes.

Uses watchdog to monitor watched folders in a dedicated OS thread. File events are
debounced (2 s quiet window) and then dispatched back onto the asyncio event loop
so the async FileIndexer can be called safely from the sync observer thread.
"""

from __future__ import annotations

import asyncio
import json
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
    EXCLUDED_DIRS,
    FileIndexer,
    SUPPORTED_EXTENSIONS,
)
from enterprise_ai_companion.capabilities.organisation.placement_scorer import (
    _SCORE_MIN_THRESHOLD,
)

logger = logging.getLogger(__name__)

_DEBOUNCE_SECONDS = 2.0

# The OS Downloads folder is auto-registered on first launch.
DOWNLOADS_PATH = str(Path.home() / "Downloads")


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

    When post_index_hook is provided (Downloads folder use-case), new files
    detected via on_created are indexed individually rather than triggering a
    full workspace re-index, and the hook is called with (file_path, document_id)
    after indexing succeeds.
    """

    def __init__(
        self,
        folder_path: str,
        indexer: FileIndexer,
        loop: asyncio.AbstractEventLoop,
        post_index_hook: "asyncio.Coroutine | None" = None,
        post_delete_hook: "asyncio.Coroutine | None" = None,
    ) -> None:
        super().__init__()
        self._folder_path = folder_path
        self._indexer = indexer
        self._loop = loop
        self._post_index_hook = post_index_hook
        self._post_delete_hook = post_delete_hook
        self._timers: dict[str, threading.Timer] = {}
        self._lock = threading.Lock()
        # Tracks paths that arrived via on_created (truly new files).
        self._created_paths: set[str] = set()

    def on_modified(self, event: FileSystemEvent) -> None:
        if not event.is_directory:
            self._schedule(event.src_path, is_new=False)

    def on_created(self, event: FileSystemEvent) -> None:
        if not event.is_directory:
            with self._lock:
                self._created_paths.add(event.src_path)
            self._schedule(event.src_path, is_new=True)

    def on_deleted(self, event: FileSystemEvent) -> None:
        if not event.is_directory and not _is_excluded(event.src_path):
            asyncio.run_coroutine_threadsafe(
                self._indexer.delete_file(event.src_path), self._loop
            )
            if self._post_delete_hook is not None:
                asyncio.run_coroutine_threadsafe(
                    self._post_delete_hook(event.src_path), self._loop
                )

    def on_moved(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            return
        src = event.src_path
        dest = getattr(event, "dest_path", None)
        if _is_excluded(src):
            return

        dest_in_folder = (
            dest is not None
            and dest.startswith(self._folder_path)
            and Path(dest).suffix.lower() in SUPPORTED_EXTENSIONS
        )

        if dest_in_folder:
            src_ext = Path(src).suffix.lower()
            if src_ext in SUPPORTED_EXTENSIONS:
                # File renamed or moved within this watched folder — update path only.
                asyncio.run_coroutine_threadsafe(
                    self._indexer.rename_file(src, dest), self._loop
                )
            else:
                # Source was a partial/temp file (e.g. .crdownload, .part) — a
                # browser download that just completed. Treat the final file as new.
                with self._lock:
                    self._created_paths.add(dest)
                self._schedule(dest, is_new=True)
        else:
            # File moved out of this watched folder — remove its index records
            # and dismiss any pending placement recommendation for it.
            asyncio.run_coroutine_threadsafe(
                self._indexer.delete_file(src), self._loop
            )
            if self._post_delete_hook is not None:
                asyncio.run_coroutine_threadsafe(
                    self._post_delete_hook(src), self._loop
                )

    def _schedule(self, src_path: str, is_new: bool = False) -> None:
        if _is_excluded(src_path):
            return
        # Office lock files (~$filename) are temporary and must never be indexed.
        if Path(src_path).name.startswith("~$"):
            return
        ext = Path(src_path).suffix.lower()
        if ext not in SUPPORTED_EXTENSIONS:
            return

        with self._lock:
            existing = self._timers.get(src_path)
            if existing is not None:
                existing.cancel()
            timer = threading.Timer(
                _DEBOUNCE_SECONDS, self._fire, args=[src_path]
            )
            self._timers[src_path] = timer
            timer.start()

    def _fire(self, src_path: str) -> None:
        with self._lock:
            self._timers.pop(src_path, None)
            is_new = src_path in self._created_paths
            self._created_paths.discard(src_path)

        if is_new and self._post_index_hook is not None:
            logger.debug(
                "New file detected in %s: %s — indexing single file",
                self._folder_path, Path(src_path).name,
            )
            coro = self._fire_new_file(src_path)
        else:
            logger.debug(
                "File change detected, re-indexing folder: %s (triggered by %s)",
                self._folder_path, Path(src_path).name,
            )
            coro = self._indexer.index_workspace(self._folder_path)

        asyncio.run_coroutine_threadsafe(coro, self._loop)

    async def _fire_new_file(self, src_path: str) -> None:
        """Index a single new file and invoke post_index_hook on success."""
        logger.info("[PLACEMENT] _fire_new_file: %s (hook=%s)", src_path, self._post_index_hook is not None)
        document_id = await self._indexer.index_file(src_path, self._folder_path)
        logger.info("[PLACEMENT] index_file returned doc_id=%s for %s", document_id, src_path)
        if document_id and self._post_index_hook is not None:
            try:
                await self._post_index_hook(src_path, document_id)
            except Exception:
                logger.exception("post_index_hook failed for %s", src_path)
        elif not document_id:
            logger.warning("[PLACEMENT] doc_id is None for %s — hook skipped", src_path)
        elif self._post_index_hook is None:
            logger.warning("[PLACEMENT] post_index_hook is None for %s — Downloads watcher has no hook wired", src_path)

    def cancel_all(self) -> None:
        """Cancel pending debounce timers — called when a watch is removed."""
        with self._lock:
            for timer in self._timers.values():
                timer.cancel()
            self._timers.clear()
            self._created_paths.clear()


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
        # Set by app.py after construction — wires the Downloads → recommendation pipeline.
        self.recommendation_service: object | None = None

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
        folder = await self.register_folder(path)
        asyncio.create_task(self._indexer.index_workspace(folder.path))
        logger.info("Watched folder added: %s", folder.path)
        return folder

    async def register_folder(self, path: str) -> WatchedFolder:
        """Persist a folder as watched and start the filesystem watch.

        Unlike add_folder, does NOT trigger an indexing run. Use this when the
        caller has already initiated indexing independently (e.g. the manual
        indexing endpoint) and only needs the folder registered for future
        auto-watch without duplicating the index job.
        """
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

        logger.info("Watched folder registered: %s", folder.path)
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

    async def reconcile_stale_files(self) -> int:
        """Remove index records for files that no longer exist on disk.

        Called at startup (as a background task) to purge records left behind
        when files were deleted or moved while the backend was not running —
        events that watchdog never saw.

        Three passes:
        1. Documents — for each file in `documents`, remove index records
           (documents / chunks / graph entities) if the file is gone from disk.
        2. Recommendations (orphan) — for each pending recommendation whose
           source_path no longer exists on disk, auto-dismiss it. Catches
           orphaned rows whose document was deleted by a prior watchdog run.
        3. Recommendations (threshold) — dismiss pending recommendations whose
           stored top score is below the current _SCORE_MIN_THRESHOLD. Cleans up
           false-positive records produced by an older, less selective scorer.

        Returns the count of stale document records removed.
        """
        # Pass 1 — stale document records
        async with self._db.execute("SELECT file_path FROM documents") as cur:
            doc_rows = await cur.fetchall()

        removed_docs = 0
        dismissed_from_docs: set[str] = set()
        for (file_path,) in doc_rows:
            if not Path(file_path).exists():
                logger.info("Reconcile: stale document — removing index for %s", file_path)
                await self._indexer.delete_file(file_path)
                if self.recommendation_service is not None:
                    await self.recommendation_service.dismiss_stale_for_path(file_path)
                    dismissed_from_docs.add(file_path)
                removed_docs += 1

        # Pass 2 — orphaned pending recommendations whose document is already gone
        if self.recommendation_service is not None:
            async with self._db.execute(
                "SELECT DISTINCT source_path FROM file_placement_recommendations "
                "WHERE status = 'pending'"
            ) as cur:
                rec_rows = await cur.fetchall()

            for (source_path,) in rec_rows:
                if source_path in dismissed_from_docs:
                    continue  # already handled in pass 1
                if not Path(source_path).exists():
                    logger.info(
                        "Reconcile: orphaned recommendation — auto-dismissing for %s", source_path
                    )
                    await self.recommendation_service.dismiss_stale_for_path(source_path)

        # Pass 3 — dismiss pending recommendations whose stored score is below
        # the current minimum threshold. This cleans up records produced by an
        # older, less selective scorer without requiring file deletion or a
        # manual re-drop. Safe to run at every startup: dismissed records can
        # be regenerated if the file is re-dropped into Downloads.
        dismissed_below_threshold = 0
        if self.recommendation_service is not None:
            async with self._db.execute(
                "SELECT source_path, recommendations FROM file_placement_recommendations "
                "WHERE status = 'pending'"
            ) as cur:
                score_rows = await cur.fetchall()

            for (source_path, recs_json) in score_rows:
                if source_path in dismissed_from_docs:
                    continue  # already handled in pass 1
                try:
                    candidates = json.loads(recs_json) if recs_json else []
                    top_score = candidates[0]["score"] if candidates else 0.0
                except (json.JSONDecodeError, KeyError, IndexError):
                    top_score = 0.0
                if top_score < _SCORE_MIN_THRESHOLD:
                    logger.info(
                        "Reconcile: stale recommendation (score=%.4f < threshold=%.2f) "
                        "— dismissing for %s",
                        top_score, _SCORE_MIN_THRESHOLD, source_path,
                    )
                    await self.recommendation_service.dismiss_stale_for_path(source_path)
                    dismissed_below_threshold += 1

        total = removed_docs
        if removed_docs or dismissed_below_threshold:
            logger.info(
                "Startup reconciliation complete — removed %d stale document(s), "
                "dismissed %d below-threshold recommendation(s)",
                removed_docs, dismissed_below_threshold,
            )
        else:
            logger.debug("Startup reconciliation complete — all indexed files present on disk")

        return total

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

    async def _ensure_downloads_registered(self) -> None:
        """Register the OS Downloads folder as a watched path if not already present.

        Called by app.py after recommendation_service is assigned. Creates the
        folder if it does not exist (edge case: fresh Windows installs where the
        user has never opened Downloads).
        """
        downloads = Path(DOWNLOADS_PATH)
        downloads.mkdir(parents=True, exist_ok=True)

        async with self._db.execute(
            "SELECT id FROM watched_folders WHERE path = ?", (str(downloads),)
        ) as cur:
            row = await cur.fetchone()

        if row is None:
            folder = WatchedFolder(
                id=str(uuid.uuid4()),
                path=str(downloads),
                auto_index=True,
                added_at=datetime.now(UTC).isoformat(),
            )
            await self._db.execute(
                "INSERT OR IGNORE INTO watched_folders (id, path, auto_index, added_at) "
                "VALUES (?, ?, ?, ?)",
                (folder.id, folder.path, int(folder.auto_index), folder.added_at),
            )
            await self._db.commit()
            logger.info("Downloads folder auto-registered: %s", folder.path)

        if self._running:
            downloads_str = str(downloads)
            existing_entry = self._watches.get(downloads_str)
            if existing_entry is not None:
                _, existing_handler = existing_entry
                # Handler was created during _async_start() before recommendation_service
                # was assigned — replace it with one that has both hooks wired.
                needs_rewire = self.recommendation_service is not None and (
                    existing_handler._post_index_hook is None
                    or existing_handler._post_delete_hook is None
                )
                if needs_rewire:
                    logger.info("Re-wiring Downloads watcher with recommendation hook")
                    self._unschedule_watch(downloads_str)
                    self._schedule_watch(downloads_str)
            else:
                self._schedule_watch(downloads_str)

    def _schedule_watch(self, path: str) -> None:
        if path in self._watches:
            return

        index_hook = None
        delete_hook = None
        if path == DOWNLOADS_PATH and self.recommendation_service is not None:
            if hasattr(self.recommendation_service, "process_new_file"):
                index_hook = self.recommendation_service.process_new_file
            if hasattr(self.recommendation_service, "dismiss_stale_for_path"):
                delete_hook = self.recommendation_service.dismiss_stale_for_path

        handler = DebounceHandler(
            path, self._indexer, self._loop,
            post_index_hook=index_hook,
            post_delete_hook=delete_hook,
        )
        watch = self._observer.schedule(handler, path, recursive=True)
        self._watches[path] = (watch, handler)
        logger.debug(
            "Scheduled watchdog watch on: %s (index_hook=%s, delete_hook=%s)",
            path, index_hook is not None, delete_hook is not None,
        )

    def _unschedule_watch(self, path: str) -> None:
        entry = self._watches.pop(path, None)
        if entry is None:
            return
        watch, handler = entry
        handler.cancel_all()
        self._observer.unschedule(watch)
        logger.debug("Unscheduled watchdog watch on: %s", path)
