"""Security, tenant, feature-flag, schema migration tests."""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.ingestion import is_intelligent_ingestion_enabled
from backend.ingestion.api import register_ingestion_routes, router
from backend.ingestion.exceptions import MigrationNotAllowedError, TenantGuardError, AuthRequiredError
from backend.ingestion.schema_sql import apply_epic1_schema, rollback_epic1_schema
from backend.ingestion.tenant_adapter import ExplicitTenantGuard, TenantContext
from tests.fixtures.ingestion.builders import csv_standard


def test_flag_default_false(monkeypatch):
    monkeypatch.delenv("ENABLE_INTELLIGENT_INGESTION", raising=False)
    assert is_intelligent_ingestion_enabled() is False


def test_flag_true(monkeypatch):
    monkeypatch.setenv("ENABLE_INTELLIGENT_INGESTION", "true")
    assert is_intelligent_ingestion_enabled() is True


def test_flag_off_no_routes_registered(monkeypatch):
    monkeypatch.setenv("ENABLE_INTELLIGENT_INGESTION", "false")
    app = FastAPI()
    assert register_ingestion_routes(app, "/tmp") is False
    client = TestClient(app)
    r = client.post("/api/ingestion/preview")
    assert r.status_code == 404


def test_flag_on_registers(monkeypatch, tmp_path):
    monkeypatch.setenv("ENABLE_INTELLIGENT_INGESTION", "true")
    app = FastAPI()
    # create minimal html
    html = tmp_path / "ingestion_experimental.html"
    html.write_text("<html></html>", encoding="utf-8")
    assert register_ingestion_routes(app, str(tmp_path)) is True
    client = TestClient(app)
    page = client.get("/ingestion-experimental")
    assert page.status_code == 200


def test_api_requires_auth(monkeypatch, tmp_path):
    monkeypatch.setenv("ENABLE_INTELLIGENT_INGESTION", "true")
    app = FastAPI()
    (tmp_path / "ingestion_experimental.html").write_text("x", encoding="utf-8")
    register_ingestion_routes(app, str(tmp_path))
    client = TestClient(app)
    r = client.post(
        "/api/ingestion/preview",
        data={"client_id": "99", "competencia": "2024-01"},
        files={"file": ("a.csv", csv_standard(), "text/csv")},
    )
    assert r.status_code == 401


def test_api_blocks_cross_tenant(monkeypatch, tmp_path):
    monkeypatch.setenv("ENABLE_INTELLIGENT_INGESTION", "true")
    app = FastAPI()
    (tmp_path / "ingestion_experimental.html").write_text("x", encoding="utf-8")
    register_ingestion_routes(app, str(tmp_path))
    client = TestClient(app)
    r = client.post(
        "/api/ingestion/preview",
        data={"client_id": "99", "competencia": "2024-01"},
        files={"file": ("a.csv", csv_standard(), "text/csv")},
        headers={"X-Ingestion-User": "u", "X-Ingestion-Client-Id": "100"},
    )
    assert r.status_code == 403


def test_tenant_guard_unit():
    ctx = TenantContext(1, "u", 10)
    g = ExplicitTenantGuard(ctx)
    assert g.require_tenant(10).client_id == 10
    with pytest.raises(TenantGuardError):
        g.require_tenant(11)
    with pytest.raises(AuthRequiredError):
        ExplicitTenantGuard(None).require_tenant(1)


def test_migration_upgrade_downgrade_preserves_legacy(tmp_path):
    db_path = tmp_path / "temp.db"
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE atestados (id INTEGER PRIMARY KEY, nome TEXT)")
    conn.execute("INSERT INTO atestados (nome) VALUES ('keep')")
    conn.commit()
    apply_epic1_schema(conn, db_path=str(db_path))
    tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert "ingestion_raw_files" in tables
    assert "atestados" in tables
    assert conn.execute("SELECT nome FROM atestados").fetchone()[0] == "keep"
    rollback_epic1_schema(conn, db_path=str(db_path))
    tables2 = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert "ingestion_raw_files" not in tables2
    assert "atestados" in tables2
    assert conn.execute("SELECT nome FROM atestados").fetchone()[0] == "keep"
    conn.close()


def test_migration_refuses_production_path():
    conn = sqlite3.connect(":memory:")
    with pytest.raises(MigrationNotAllowedError):
        apply_epic1_schema(conn, db_path="/var/www/absenteismo/database/absenteismo.db")


def test_api_preview_happy(monkeypatch, tmp_path):
    monkeypatch.setenv("ENABLE_INTELLIGENT_INGESTION", "true")
    app = FastAPI()
    (tmp_path / "ingestion_experimental.html").write_text("x", encoding="utf-8")
    register_ingestion_routes(app, str(tmp_path))
    client = TestClient(app)
    r = client.post(
        "/api/ingestion/preview",
        data={"client_id": "99", "competencia": "2024-01"},
        files={"file": ("a.csv", csv_standard(), "text/csv")},
        headers={"X-Ingestion-User": "tester", "X-Ingestion-Client-Id": "99"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["preview_id"]
    assert "confirmation_token" in body
    assert "storage_key" not in body
    # no full paths
    assert "/var/www" not in str(body)


def test_logging_utils_no_pii_keys():
    from backend.ingestion.logging_utils import safe_log

    # should not raise
    safe_log("test", client_id=1, nome="SHOULD_BE_STRIPPED", cpf="123", step="x")
