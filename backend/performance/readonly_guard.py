"""Readonly SQLite guards for shadow performance validation.

Never defaults to production. Refuses known live DB paths.
"""

from __future__ import annotations

import hashlib
import sqlite3
from pathlib import Path
from typing import Iterable

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session, sessionmaker

from backend.performance.exceptions import (
    IntegrityCheckError,
    ProductionPathError,
    ReadonlyViolationError,
    SchemaIncompatibleError,
)

PRODUCTION_DB_PATH = "/var/www/absenteismo/database/absenteismo.db"
_FORBIDDEN_FRAGMENTS = (
    "/var/www/absenteismo",
    "absenteismo.db",
)
_REQUIRED_TABLES = ("clients", "uploads", "atestados")


def normalize_path(db_path: str | Path) -> Path:
    if db_path is None or str(db_path).strip() == "":
        raise ProductionPathError("db_path explícito é obrigatório (sem default)")
    return Path(str(db_path)).expanduser().resolve()


def assert_safe_db_path(db_path: str | Path) -> Path:
    """Refuse production-like paths and missing files."""
    path = normalize_path(db_path)
    norm = str(path).replace("\\", "/").lower()
    if norm == PRODUCTION_DB_PATH.lower() or PRODUCTION_DB_PATH.lower() in norm:
        raise ProductionPathError(f"refusing production path: {path}")
    for frag in _FORBIDDEN_FRAGMENTS:
        if frag in norm:
            raise ProductionPathError(f"refusing production-like path: {path}")
    if not path.is_file():
        raise FileNotFoundError(f"db file not found: {path}")
    return path


def sha256_file(path: str | Path) -> str:
    p = Path(path)
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def run_integrity_check(path: str | Path) -> str:
    """PRAGMA integrity_check via sqlite3 URI readonly."""
    p = assert_safe_db_path(path)
    uri = f"file:{p}?mode=ro"
    try:
        conn = sqlite3.connect(uri, uri=True, check_same_thread=False)
    except sqlite3.Error as exc:
        raise IntegrityCheckError(f"integrity_check failed: {exc}") from exc
    try:
        conn.execute("PRAGMA query_only=ON")
        row = conn.execute("PRAGMA integrity_check").fetchone()
        result = (row[0] if row else "").strip().lower()
        if result != "ok":
            raise IntegrityCheckError(f"integrity_check failed: {result}")
        return result
    except sqlite3.Error as exc:
        raise IntegrityCheckError(f"integrity_check failed: {exc}") from exc
    finally:
        conn.close()


def assert_compatible_schema(db: Session) -> list[str]:
    """Ensure required tables exist; raise on incompatible schema."""
    insp = inspect(db.bind)
    tables = set(insp.get_table_names())
    missing = [t for t in _REQUIRED_TABLES if t not in tables]
    if missing:
        raise SchemaIncompatibleError(
            f"schema incompatível — tabelas ausentes: {', '.join(missing)}"
        )
    return sorted(tables)


def open_sqlite_readonly(db_path: str | Path) -> Session:
    """
    Open SQLite in mode=ro with PRAGMA query_only=ON.
    Requires an explicit, non-production path that exists and passes integrity.
    """
    path = assert_safe_db_path(db_path)
    run_integrity_check(path)

    def _connect():
        conn = sqlite3.connect(
            f"file:{path}?mode=ro",
            uri=True,
            check_same_thread=False,
        )
        conn.execute("PRAGMA query_only=ON")
        return conn

    engine = create_engine("sqlite://", creator=_connect)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    assert_compatible_schema(db)
    return db


def assert_query_only(db: Session) -> None:
    """Best-effort verification that writes are blocked."""
    try:
        db.execute(text("INSERT INTO clients (id, nome) VALUES (-99999, 'x')"))
        db.rollback()
        raise ReadonlyViolationError("write succeeded on supposed readonly session")
    except ReadonlyViolationError:
        raise
    except Exception:
        db.rollback()


def file_fingerprint(path: str | Path) -> dict[str, str | int]:
    p = assert_safe_db_path(path)
    st = p.stat()
    return {
        "path_basename": p.name,
        "sha256": sha256_file(p),
        "size_bytes": int(st.st_size),
        "mtime_ns": int(st.st_mtime_ns),
    }


def fingerprints_equal(a: dict, b: dict, keys: Iterable[str] | None = None) -> bool:
    keys = tuple(keys or ("sha256", "size_bytes", "mtime_ns"))
    return all(a.get(k) == b.get(k) for k in keys)


__all__ = [
    "PRODUCTION_DB_PATH",
    "assert_safe_db_path",
    "sha256_file",
    "run_integrity_check",
    "assert_compatible_schema",
    "open_sqlite_readonly",
    "assert_query_only",
    "file_fingerprint",
    "fingerprints_equal",
]
