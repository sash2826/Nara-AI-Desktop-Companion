"""Tests for BackupService."""

from __future__ import annotations

import json
from pathlib import Path

import aiosqlite
import pytest

from enterprise_ai_companion.infrastructure.backup import BackupService


# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
async def db(tmp_path):
    """In-memory SQLite database (WAL not needed for tests)."""
    db_path = tmp_path / "test.db"
    async with aiosqlite.connect(db_path) as conn:
        conn.row_factory = aiosqlite.Row
        await conn.execute("CREATE TABLE test_table (id INTEGER PRIMARY KEY, value TEXT)")
        await conn.execute("INSERT INTO test_table VALUES (1, 'hello')")
        await conn.commit()
        yield conn, db_path


@pytest.fixture
def backup_root(tmp_path):
    return tmp_path / "backups"


# ─── create_backup ────────────────────────────────────────────────────────────

class TestCreateBackup:
    async def test_returns_backup_result(self, db, backup_root):
        conn, _ = db
        service = BackupService(db_conn=conn, qdrant_client=None, backup_root=backup_root)
        result = await service.create_backup()
        assert result.backup_id
        assert result.status == "complete"

    async def test_creates_backup_directory(self, db, backup_root):
        conn, _ = db
        service = BackupService(db_conn=conn, qdrant_client=None, backup_root=backup_root)
        result = await service.create_backup()
        assert Path(result.backup_path).is_dir()

    async def test_sqlite_snapshot_exists(self, db, backup_root):
        conn, _ = db
        service = BackupService(db_conn=conn, qdrant_client=None, backup_root=backup_root)
        result = await service.create_backup()
        sqlite_file = Path(result.backup_path) / "sqlite.db"
        assert sqlite_file.exists()
        assert result.sqlite_size_bytes > 0

    async def test_manifest_is_written(self, db, backup_root):
        conn, _ = db
        service = BackupService(db_conn=conn, qdrant_client=None, backup_root=backup_root)
        result = await service.create_backup(notes="test run")
        manifest_path = Path(result.backup_path) / "manifest.json"
        assert manifest_path.exists()
        data = json.loads(manifest_path.read_text())
        assert data["backup_id"] == result.backup_id
        assert data["status"] == "complete"
        assert data["notes"] == "test run"

    async def test_no_qdrant_collections_when_client_is_none(self, db, backup_root):
        conn, _ = db
        service = BackupService(db_conn=conn, qdrant_client=None, backup_root=backup_root)
        result = await service.create_backup()
        assert result.qdrant_collections == []

    async def test_created_at_is_iso_format(self, db, backup_root):
        conn, _ = db
        service = BackupService(db_conn=conn, qdrant_client=None, backup_root=backup_root)
        result = await service.create_backup()
        # Should parse without error
        from datetime import datetime
        datetime.fromisoformat(result.created_at)

    async def test_backup_id_is_timestamp_format(self, db, backup_root):
        conn, _ = db
        service = BackupService(db_conn=conn, qdrant_client=None, backup_root=backup_root)
        result = await service.create_backup()
        # Format: YYYYMMDDTHHMMSSZ
        assert len(result.backup_id) == 16
        assert result.backup_id.endswith("Z")

    async def test_multiple_backups_have_unique_ids(self, db, backup_root):
        import asyncio
        conn, _ = db
        service = BackupService(db_conn=conn, qdrant_client=None, backup_root=backup_root)
        r1 = await service.create_backup()
        await asyncio.sleep(1.1)  # ensure different second
        r2 = await service.create_backup()
        assert r1.backup_id != r2.backup_id


# ─── list_backups ─────────────────────────────────────────────────────────────

class TestListBackups:
    async def test_empty_when_no_backups(self, db, backup_root):
        conn, _ = db
        service = BackupService(db_conn=conn, qdrant_client=None, backup_root=backup_root)
        result = await service.list_backups()
        assert result == []

    async def test_lists_created_backup(self, db, backup_root):
        conn, _ = db
        service = BackupService(db_conn=conn, qdrant_client=None, backup_root=backup_root)
        created = await service.create_backup()
        summaries = await service.list_backups()
        assert len(summaries) == 1
        assert summaries[0].backup_id == created.backup_id

    async def test_most_recent_first(self, db, backup_root):
        import asyncio
        conn, _ = db
        service = BackupService(db_conn=conn, qdrant_client=None, backup_root=backup_root)
        r1 = await service.create_backup()
        await asyncio.sleep(1.1)
        r2 = await service.create_backup()
        summaries = await service.list_backups()
        assert summaries[0].backup_id == r2.backup_id
        assert summaries[1].backup_id == r1.backup_id

    async def test_summary_fields_populated(self, db, backup_root):
        conn, _ = db
        service = BackupService(db_conn=conn, qdrant_client=None, backup_root=backup_root)
        await service.create_backup()
        summaries = await service.list_backups()
        s = summaries[0]
        assert s.backup_id
        assert s.backup_path
        assert s.created_at
        assert s.status == "complete"
        assert s.sqlite_size_bytes > 0


# ─── delete_backup ────────────────────────────────────────────────────────────

class TestDeleteBackup:
    async def test_deletes_existing_backup(self, db, backup_root):
        conn, _ = db
        service = BackupService(db_conn=conn, qdrant_client=None, backup_root=backup_root)
        result = await service.create_backup()
        deleted = await service.delete_backup(result.backup_id)
        assert deleted is True
        assert not Path(result.backup_path).exists()

    async def test_returns_false_for_nonexistent_backup(self, db, backup_root):
        conn, _ = db
        service = BackupService(db_conn=conn, qdrant_client=None, backup_root=backup_root)
        deleted = await service.delete_backup("20000101T000000Z")
        assert deleted is False

    async def test_deleted_backup_not_in_list(self, db, backup_root):
        conn, _ = db
        service = BackupService(db_conn=conn, qdrant_client=None, backup_root=backup_root)
        result = await service.create_backup()
        await service.delete_backup(result.backup_id)
        summaries = await service.list_backups()
        assert all(s.backup_id != result.backup_id for s in summaries)
