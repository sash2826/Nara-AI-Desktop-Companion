"""Local Qdrant vector store provider for the Enterprise AI Companion.

Uses QdrantClient in local file-based mode — no Docker or network service required.
The collection is created automatically on first initialisation.
"""

from __future__ import annotations

import logging
import os
import signal
import sys
import time
from pathlib import Path

from enterprise_ai_companion.infrastructure.config import get_config

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

logger = logging.getLogger(__name__)

CHUNKS_COLLECTION = "document_chunks"
EMBEDDING_DIM = 384  # bge-small-en-v1.5 output dimension


def _pid_file_path(data_dir: Path) -> Path:
    return data_dir / "backend.pid"


def _write_pid_file(data_dir: Path) -> None:
    """Write the current process PID so the next startup can terminate this one."""
    _pid_file_path(data_dir).write_text(str(os.getpid()))


def _terminate_previous_instance(data_dir: Path) -> None:
    """Kill the previously recorded PID if it is still running."""
    pid_path = _pid_file_path(data_dir)
    if not pid_path.exists():
        return

    try:
        old_pid = int(pid_path.read_text().strip())
    except (ValueError, OSError):
        pid_path.unlink(missing_ok=True)
        return

    if old_pid == os.getpid():
        return

    try:
        # SIGTERM on POSIX; on Windows os.kill with SIGTERM calls TerminateProcess.
        os.kill(old_pid, signal.SIGTERM)
        # Give the process up to 3 seconds to release the Qdrant lock.
        for _ in range(30):
            time.sleep(0.1)
            try:
                os.kill(old_pid, 0)  # 0 = check existence only
            except OSError:
                break  # process is gone
        logger.warning("Terminated previous backend instance (PID %d).", old_pid)
    except OSError:
        pass  # process already gone
    finally:
        pid_path.unlink(missing_ok=True)


def _remove_stale_lock(data_dir: Path) -> None:
    """Delete a Qdrant lock file left by a previously crashed process.

    Attempts deletion directly — on Windows the OS will reject the unlink if
    another process holds an active portalocker byte-range lock on the file,
    which is the definitive signal that the lock is live rather than stale.
    """
    lock_path = data_dir / ".lock"
    if not lock_path.exists():
        return

    try:
        lock_path.unlink()
        logger.debug(
            "Removed Qdrant lock file at %s (previous sidecar process did not shut down cleanly).",
            lock_path,
        )
    except PermissionError:
        logger.error(
            "Qdrant lock file at %s is held by another process. "
            "Run: taskkill /IM python.exe /F  then retry.",
            lock_path,
        )
        sys.exit(1)


def _qdrant_data_dir() -> Path:
    cfg_val = get_config().qdrant_path
    if cfg_val:
        return Path(cfg_val)
    return Path(__file__).parents[4] / "qdrant_data"


class QdrantProvider:
    """Manages the lifecycle of a local Qdrant client and the document_chunks collection."""

    def __init__(self) -> None:
        self._client: QdrantClient | None = None

    def initialize(self) -> None:
        """Open the local Qdrant store and ensure the collection exists with correct dims.

        If the collection exists with a different vector size (e.g. left over from a
        previous embedding model), it is deleted and recreated so the dimension always
        matches EMBEDDING_DIM. This makes model switches safe without manual cleanup.

        Stale lock files left by a previously crashed process are removed automatically
        before opening the client so the backend can restart without manual intervention.
        """
        data_dir = _qdrant_data_dir()
        data_dir.mkdir(parents=True, exist_ok=True)

        _terminate_previous_instance(data_dir)
        _remove_stale_lock(data_dir)
        _write_pid_file(data_dir)

        self._client = QdrantClient(path=str(data_dir))
        logger.info("Qdrant provider initialised at %s", data_dir)

        existing = {c.name for c in self._client.get_collections().collections}
        if CHUNKS_COLLECTION in existing:
            info = self._client.get_collection(CHUNKS_COLLECTION)
            stored_dim = info.config.params.vectors.size  # type: ignore[union-attr]
            if stored_dim != EMBEDDING_DIM:
                logger.warning(
                    "Collection '%s' has dim=%d but model requires dim=%d — recreating.",
                    CHUNKS_COLLECTION, stored_dim, EMBEDDING_DIM,
                )
                self._client.delete_collection(CHUNKS_COLLECTION)
                existing.discard(CHUNKS_COLLECTION)

        if CHUNKS_COLLECTION not in existing:
            self._client.create_collection(
                collection_name=CHUNKS_COLLECTION,
                vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE),
            )
            logger.info("Created Qdrant collection '%s' (dim=%d)", CHUNKS_COLLECTION, EMBEDDING_DIM)

    def get_client(self) -> QdrantClient:
        if self._client is None:
            raise RuntimeError("QdrantProvider.initialize() must be called before get_client().")
        return self._client

    def health(self) -> bool:
        """Return True if the client is initialised and the collection is reachable."""
        if self._client is None:
            return False
        try:
            self._client.get_collection(CHUNKS_COLLECTION)
            return True
        except Exception:
            return False

    def close(self) -> None:
        if self._client is not None:
            self._client.close()
            self._client = None
            _pid_file_path(_qdrant_data_dir()).unlink(missing_ok=True)
            logger.info("Qdrant provider closed.")
