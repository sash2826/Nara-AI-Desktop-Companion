"""SQLite connection management for the Enterprise AI Companion backend.

A single aiosqlite connection is opened at application startup and closed on
shutdown via FastAPI's lifespan context manager. All repositories receive the
connection through dependency injection rather than opening their own.
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

import aiosqlite

# Resolve the schema file by walking up from this module to find the repo root
# (the directory that contains both "backend/" and "database/").
def _find_schema_path() -> Path:
    candidate = Path(__file__).resolve()
    for _ in range(10):
        candidate = candidate.parent
        schema = candidate / "database" / "schemas" / "conversations.sql"
        if schema.exists():
            return schema
    raise FileNotFoundError(
        f"conversations.sql not found under any ancestor of {__file__}. "
        "Set EAC_SCHEMA_PATH to override."
    )


_SCHEMA_PATH = Path(os.environ["EAC_SCHEMA_PATH"]) if "EAC_SCHEMA_PATH" in os.environ else None

# The database file lives in the user's app-data directory in production.
# In development, fall back to a local file next to the backend package.
_DEFAULT_DB_PATH = Path(__file__).parents[4] / "enterprise_ai_companion.db"


def _db_path() -> Path:
    env = os.environ.get("EAC_DB_PATH")
    return Path(env) if env else _DEFAULT_DB_PATH


async def open_db() -> aiosqlite.Connection:
    """Open (or create) the SQLite database and apply the schema."""
    path = _db_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    conn = await aiosqlite.connect(path)
    conn.row_factory = aiosqlite.Row

    # Enable WAL mode for better concurrent read performance.
    await conn.execute("PRAGMA journal_mode=WAL")
    await conn.execute("PRAGMA foreign_keys=ON")

    schema_path = _SCHEMA_PATH or _find_schema_path()
    schema_sql = schema_path.read_text(encoding="utf-8")
    await conn.executescript(schema_sql)
    await conn.commit()

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
