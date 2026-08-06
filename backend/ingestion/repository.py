"""Explicit persistence for Epic 1 — no implicit /tmp DB, no auto-schema on router.

Connection/schema must be supplied by the caller (tests) or an explicitly
configured staging path. Future: wrap SQLAlchemy Session from the main app.

HTTP handlers must open a short-lived repository via
`ingestion_repository_session()` so file-backed connections are closed
per request (no shared long-lived SQLite connection across workers).
"""

from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Protocol

from backend.ingestion.exceptions import IngestionError, MigrationNotAllowedError
from backend.ingestion.schema_sql import apply_epic1_schema

INGESTION_SQLITE_PATH_ENV = "INGESTION_SQLITE_PATH"


class IngestionPersistenceError(IngestionError):
    code = "PERSISTENCE_UNAVAILABLE"


class IngestionRepository(Protocol):
    """Persistence port for preview/import/profile services."""

    @property
    def conn(self) -> sqlite3.Connection: ...

    @property
    def db_path(self) -> str | None: ...


class SqliteIngestionRepository:
    """SQLite-backed repository. Does not create schema unless apply_schema=True."""

    def __init__(
        self,
        conn: sqlite3.Connection,
        *,
        db_path: str | None = None,
        apply_schema: bool = False,
    ) -> None:
        self._conn = conn
        self._db_path = db_path
        if apply_schema:
            apply_epic1_schema(conn, db_path=db_path)

    @property
    def conn(self) -> sqlite3.Connection:
        return self._conn

    @property
    def db_path(self) -> str | None:
        return self._db_path

    def close(self) -> None:
        self._conn.close()


_REPO_OVERRIDE: IngestionRepository | None = None


def set_ingestion_repository(repo: IngestionRepository | None) -> None:
    """Inject repository (tests or app wiring). None clears override."""
    global _REPO_OVERRIDE
    _REPO_OVERRIDE = repo


def get_ingestion_repository_override() -> IngestionRepository | None:
    return _REPO_OVERRIDE


def create_memory_repository(*, apply_schema: bool = True) -> SqliteIngestionRepository:
    """Test helper: explicit in-memory DB."""
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    return SqliteIngestionRepository(conn, db_path=":memory:", apply_schema=apply_schema)


def create_file_repository(
    path: str | Path,
    *,
    apply_schema: bool = False,
) -> SqliteIngestionRepository:
    """Explicit file-backed repo (staging/tests). Schema apply still guards production paths."""
    p = Path(path)
    conn = sqlite3.connect(str(p), check_same_thread=False)
    return SqliteIngestionRepository(conn, db_path=str(p), apply_schema=apply_schema)


def _open_path_repository(path: str) -> SqliteIngestionRepository:
    """Open a new connection to an explicit staging path (caller must close)."""
    normalized = path.replace("\\", "/").lower()
    if "absenteismo.db" in normalized or "/var/www/absenteismo" in normalized:
        raise MigrationNotAllowedError(
            "refusing ingestion repository on production-like database path"
        )
    if not Path(path).exists():
        raise IngestionPersistenceError(
            "ingestion sqlite path does not exist — create and migrate explicitly offline"
        )
    conn = sqlite3.connect(path, check_same_thread=False)
    return SqliteIngestionRepository(conn, db_path=path, apply_schema=False)


def get_ingestion_repository() -> IngestionRepository:
    """
    Resolve repository (legacy helper).

    Prefer `ingestion_repository_session()` in HTTP handlers so path-backed
    connections are always closed. This function still opens a new connection
    for INGESTION_SQLITE_PATH and does not auto-close.

    Order:
    1. Explicit override via set_ingestion_repository (app wiring / tests)
    2. INGESTION_SQLITE_PATH env (explicit staging path; schema NOT auto-applied)

    Never creates /tmp/absenteismo_epic1_experimental.db.
    Never applies migrations implicitly.
    """
    if _REPO_OVERRIDE is not None:
        return _REPO_OVERRIDE

    path = (os.environ.get(INGESTION_SQLITE_PATH_ENV) or "").strip()
    if not path:
        raise IngestionPersistenceError(
            "ingestion persistence unavailable — set INGESTION_SQLITE_PATH or inject repository"
        )
    return _open_path_repository(path)


@contextmanager
def ingestion_repository_session() -> Iterator[IngestionRepository]:
    """
    Per-request repository scope.

    - Override (tests/app inject): yield without closing (owned by injector).
    - INGESTION_SQLITE_PATH: open a fresh connection and always close it.
    """
    if _REPO_OVERRIDE is not None:
        yield _REPO_OVERRIDE
        return

    path = (os.environ.get(INGESTION_SQLITE_PATH_ENV) or "").strip()
    if not path:
        raise IngestionPersistenceError(
            "ingestion persistence unavailable — set INGESTION_SQLITE_PATH or inject repository"
        )
    repo = _open_path_repository(path)
    try:
        yield repo
    finally:
        try:
            repo.close()
        except Exception:
            pass
