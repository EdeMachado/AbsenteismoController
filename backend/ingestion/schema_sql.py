"""Apply Epic1 additive SQL only on explicitly provided connections (tests/temp)."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from backend.ingestion.exceptions import MigrationNotAllowedError

SQL_DIR = Path(__file__).resolve().parent / "sql"
UP_SQL = SQL_DIR / "001_epic1_ingestion_up.sql"
DOWN_SQL = SQL_DIR / "001_epic1_ingestion_down.sql"

# Safety: refuse known production path patterns
_FORBIDDEN_PATH_FRAGMENTS = (
    "/var/www/absenteismo",
    "absenteismo.db",
)


def _assert_safe_target(db_path: str | None) -> None:
    if not db_path or db_path == ":memory:":
        return
    normalized = db_path.replace("\\", "/").lower()
    for frag in _FORBIDDEN_PATH_FRAGMENTS:
        if frag in normalized:
            raise MigrationNotAllowedError(
                "refusing to apply epic1 migration to production-like path"
            )


def apply_epic1_schema(conn: sqlite3.Connection, *, db_path: str | None = None) -> None:
    _assert_safe_target(db_path)
    sql = UP_SQL.read_text(encoding="utf-8")
    conn.executescript(sql)
    conn.commit()


def rollback_epic1_schema(conn: sqlite3.Connection, *, db_path: str | None = None) -> None:
    _assert_safe_target(db_path)
    sql = DOWN_SQL.read_text(encoding="utf-8")
    conn.executescript(sql)
    conn.commit()
