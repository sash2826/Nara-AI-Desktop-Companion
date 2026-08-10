"""SQLite connection management and schema migration for the Enterprise AI Companion.

A single aiosqlite connection is opened at application startup and closed on
shutdown via FastAPI's lifespan context manager. All repositories receive the
connection through dependency injection rather than opening their own.

Schema evolution is handled by numbered SQL files in database/migrations/.
Each file is applied exactly once; the version is recorded in schema_migrations
so subsequent restarts skip already-applied migrations.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import AsyncGenerator

import aiosqlite

from enterprise_ai_companion.infrastructure.config import get_config


# ---------------------------------------------------------------------------
# Path resolution helpers
# ---------------------------------------------------------------------------

def _find_migrations_dir() -> Path:
    """Walk ancestor directories to locate database/migrations/ from any CWD."""
    candidate = Path(__file__).resolve()
    for _ in range(10):
        candidate = candidate.parent
        migrations = candidate / "database" / "migrations"
        if migrations.is_dir():
            return migrations
    raise FileNotFoundError(
        f"database/migrations/ not found under any ancestor of {__file__}. "
        "Set EAC_MIGRATIONS_DIR to override."
    )


def _migrations_dir() -> Path:
    cfg_val = get_config().migrations_dir
    return Path(cfg_val) if cfg_val else _find_migrations_dir()


def _db_path() -> Path:
    cfg_val = get_config().db_path
    if cfg_val:
        return Path(cfg_val)
    return Path(__file__).parents[4] / "enterprise_ai_companion.db"


# ---------------------------------------------------------------------------
# Migration runner
# ---------------------------------------------------------------------------

async def _apply_migrations(conn: aiosqlite.Connection) -> None:
    """Apply any pending SQL migrations from database/migrations/*.sql.

    Migrations are numbered files (e.g. 001_conversations.sql). Each is applied
    exactly once; the applied version is recorded in schema_migrations so
    subsequent startups skip it. Each migration runs inside its own transaction
    so a failure does not corrupt previously-applied state.
    """
    await conn.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version    INTEGER PRIMARY KEY,
            name       TEXT    NOT NULL,
            applied_at TEXT    NOT NULL
        )
        """
    )
    await conn.commit()

    async with conn.execute("SELECT version FROM schema_migrations") as cur:
        applied = {row[0] async for row in cur}

    for sql_file in sorted(_migrations_dir().glob("*.sql")):
        try:
            version = int(sql_file.stem.split("_")[0])
        except ValueError:
            continue  # skip files that don't start with an integer

        if version in applied:
            continue

        sql = sql_file.read_text(encoding="utf-8")
        try:
            await conn.executescript(sql)
            await conn.execute(
                "INSERT INTO schema_migrations (version, name, applied_at) VALUES (?, ?, ?)",
                (version, sql_file.name, datetime.now(UTC).isoformat()),
            )
            await conn.commit()
        except Exception as exc:
            await conn.rollback()
            raise RuntimeError(f"Migration {sql_file.name} failed: {exc}") from exc


# ---------------------------------------------------------------------------
# Connection lifecycle
# ---------------------------------------------------------------------------

async def open_db() -> aiosqlite.Connection:
    """Open (or create) the SQLite database, apply pending migrations, return the connection."""
    path = _db_path()
    if str(path) != ":memory:":
        path.parent.mkdir(parents=True, exist_ok=True)

    conn = await aiosqlite.connect(path)
    conn.row_factory = aiosqlite.Row
    await conn.execute("PRAGMA journal_mode=WAL")
    await conn.execute("PRAGMA foreign_keys=ON")
    await _apply_migrations(conn)
    return conn


async def close_db(conn: aiosqlite.Connection) -> None:
    """Close the database connection cleanly."""
    await conn.close()


@asynccontextmanager
async def lifespan_db() -> AsyncGenerator[aiosqlite.Connection, None]:
    """Async context manager that opens and closes the database around a lifespan."""
    conn = await open_db()
    try:
        yield conn
    finally:
        await close_db(conn)
