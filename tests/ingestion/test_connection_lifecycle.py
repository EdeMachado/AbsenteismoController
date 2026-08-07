"""FIT-02: ingestion repository connection lifecycle (per request close)."""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path

import pytest

from backend.ingestion.repository import (
    create_file_repository,
    get_ingestion_repository,
    ingestion_repository_session,
    set_ingestion_repository,
)
from backend.ingestion.schema_sql import apply_epic1_schema


@pytest.fixture(autouse=True)
def _clear_override():
    set_ingestion_repository(None)
    yield
    set_ingestion_repository(None)


def test_path_session_closes_connection(tmp_path, monkeypatch):
    db = tmp_path / "ingest_staging.sqlite"
    conn = sqlite3.connect(db)
    apply_epic1_schema(conn, db_path=str(db))
    conn.close()

    monkeypatch.setenv("INGESTION_SQLITE_PATH", str(db))
    monkeypatch.delenv("INGESTION_ALLOW_TEST_DEPENDENCIES", raising=False)

    with ingestion_repository_session() as repo:
        cur = repo.conn.execute("SELECT 1").fetchone()
        assert cur[0] == 1
        raw = repo.conn

    with pytest.raises(sqlite3.ProgrammingError):
        raw.execute("SELECT 1")


def test_override_session_does_not_close_injected_repo(tmp_path):
    db = tmp_path / "inject.sqlite"
    repo = create_file_repository(db, apply_schema=True)
    set_ingestion_repository(repo)
    with ingestion_repository_session() as scoped:
        assert scoped is repo
        scoped.conn.execute("SELECT 1").fetchone()
    # Injected ownership: still usable
    assert repo.conn.execute("SELECT 1").fetchone()[0] == 1
    repo.close()


def test_get_repository_refuses_production_like_path(monkeypatch):
    from backend.ingestion.exceptions import MigrationNotAllowedError

    monkeypatch.setenv(
        "INGESTION_SQLITE_PATH",
        "/var/www/absenteismo/database/absenteismo.db",
    )
    with pytest.raises(MigrationNotAllowedError):
        get_ingestion_repository()


def test_http_preview_closes_path_backed_repo(tmp_path, monkeypatch):
    """Two sequential HTTP calls with path-backed repo must not leak connections."""
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from backend.ingestion.api import register_ingestion_routes
    from backend.ingestion.tenant_adapter import (
        ExplicitTenantGuard,
        TenantContext,
        set_pr4_tenant_guard_factory,
    )
    from tests.fixtures.ingestion.builders import csv_standard

    db = tmp_path / "http_ingest.sqlite"
    conn = sqlite3.connect(db)
    apply_epic1_schema(conn, db_path=str(db))
    conn.close()

    monkeypatch.setenv("ENABLE_INTELLIGENT_INGESTION", "true")
    monkeypatch.setenv("INGESTION_ALLOW_TEST_DEPENDENCIES", "true")
    monkeypatch.setenv("INGESTION_SQLITE_PATH", str(db))
    set_ingestion_repository(None)

    ctx = TenantContext(user_id=1, username="t", client_id=99, is_global_admin=False)

    def factory(_req):
        return ExplicitTenantGuard(ctx)

    set_pr4_tenant_guard_factory(factory)
    app = FastAPI()
    (tmp_path / "ingestion_experimental.html").write_text("<html></html>", encoding="utf-8")
    assert register_ingestion_routes(app, str(tmp_path)) is True
    client = TestClient(app)

    files = {"file": ("a.csv", csv_standard(), "text/csv")}
    data = {"client_id": "99", "competencia": "2026-05"}
    r1 = client.post("/api/ingestion/preview", files=files, data=data)
    assert r1.status_code == 200, r1.text
    r2 = client.post(
        "/api/ingestion/preview",
        files={"file": ("b.csv", csv_standard(), "text/csv")},
        data=data,
    )
    assert r2.status_code == 200, r2.text
    # DB file still healthy
    c = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    try:
        assert c.execute("PRAGMA quick_check").fetchone()[0] == "ok"
    finally:
        c.close()
    set_pr4_tenant_guard_factory(None)
