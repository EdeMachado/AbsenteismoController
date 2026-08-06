"""Security, tenant fail-closed, feature-flag, schema migration tests."""

from __future__ import annotations

import sqlite3

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.ingestion import is_intelligent_ingestion_enabled
from backend.ingestion.api import ingestion_http_ready, register_ingestion_routes
from backend.ingestion.exceptions import (
    AuthRequiredError,
    MigrationNotAllowedError,
    TenantGuardError,
)
from backend.ingestion.repository import (
    IngestionPersistenceError,
    create_memory_repository,
    get_ingestion_repository,
    set_ingestion_repository,
)
from backend.ingestion.schema_sql import apply_epic1_schema, rollback_epic1_schema
from backend.ingestion.tenant_adapter import (
    ExplicitTenantGuard,
    TenantContext,
    allow_test_dependencies,
    is_ingestion_auth_available,
    require_ingestion_tenant,
    set_pr4_tenant_guard_factory,
)
from tests.fixtures.ingestion.builders import csv_standard


@pytest.fixture(autouse=True)
def _reset_ingestion_wiring():
    set_pr4_tenant_guard_factory(None)
    set_ingestion_repository(None)
    yield
    set_pr4_tenant_guard_factory(None)
    set_ingestion_repository(None)


def _wire_test_auth(client_id: int = 99, *, global_admin: bool = False):
    ctx = TenantContext(
        user_id=1,
        username="tester",
        client_id=client_id,
        is_global_admin=global_admin,
    )

    def factory(_request):
        return ExplicitTenantGuard(ctx)

    set_pr4_tenant_guard_factory(factory)
    return ctx


def _app_with_ingestion(monkeypatch, tmp_path, *, client_id: int = 99):
    monkeypatch.setenv("ENABLE_INTELLIGENT_INGESTION", "true")
    monkeypatch.setenv("INGESTION_ALLOW_TEST_DEPENDENCIES", "true")
    _wire_test_auth(client_id)
    repo = create_memory_repository(apply_schema=True)
    set_ingestion_repository(repo)
    app = FastAPI()
    (tmp_path / "ingestion_experimental.html").write_text("<html></html>", encoding="utf-8")
    assert register_ingestion_routes(app, str(tmp_path)) is True
    return app, repo


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


def test_flag_on_without_pr4_does_not_register(monkeypatch, tmp_path):
    monkeypatch.setenv("ENABLE_INTELLIGENT_INGESTION", "true")
    monkeypatch.delenv("INGESTION_ALLOW_TEST_DEPENDENCIES", raising=False)
    set_pr4_tenant_guard_factory(None)
    app = FastAPI()
    (tmp_path / "ingestion_experimental.html").write_text("x", encoding="utf-8")
    assert is_ingestion_auth_available() is False
    assert ingestion_http_ready() is False
    assert register_ingestion_routes(app, str(tmp_path)) is False
    client = TestClient(app)
    assert client.post("/api/ingestion/preview").status_code == 404
    assert client.get("/ingestion-experimental").status_code == 404


def test_identity_headers_ignored_and_do_not_authenticate(monkeypatch, tmp_path):
    """Browser identity headers must never authenticate."""
    monkeypatch.setenv("ENABLE_INTELLIGENT_INGESTION", "true")
    monkeypatch.delenv("INGESTION_ALLOW_TEST_DEPENDENCIES", raising=False)
    set_pr4_tenant_guard_factory(None)
    app = FastAPI()
    assert register_ingestion_routes(app, str(tmp_path)) is False

    # With factory + repo, forged headers still unused — auth comes from factory only
    app2, _repo = _app_with_ingestion(monkeypatch, tmp_path, client_id=99)
    client = TestClient(app2)
    r = client.post(
        "/api/ingestion/preview",
        data={"client_id": "99", "competencia": "2024-01"},
        files={"file": ("a.csv", csv_standard(), "text/csv")},
        headers={"X-Ingestion-User": "attacker", "X-Ingestion-Client-Id": "1"},
    )
    assert r.status_code == 200
    assert r.json()["client_id"] == 99


def test_api_requires_auth_factory(monkeypatch, tmp_path):
    monkeypatch.setenv("ENABLE_INTELLIGENT_INGESTION", "true")
    monkeypatch.setenv("INGESTION_ALLOW_TEST_DEPENDENCIES", "true")
    # Register with test deps but clear factory after register to simulate 503 path:
    # Better: mount router manually and hit require without factory
    from backend.ingestion import api as api_mod

    app = FastAPI()
    app.include_router(api_mod.router)
    set_pr4_tenant_guard_factory(None)
    set_ingestion_repository(create_memory_repository())
    client = TestClient(app)
    r = client.post(
        "/api/ingestion/preview",
        data={"client_id": "99", "competencia": "2024-01"},
        files={"file": ("a.csv", csv_standard(), "text/csv")},
    )
    assert r.status_code == 503
    assert "authentication unavailable" in r.json()["detail"]


def test_api_blocks_cross_tenant(monkeypatch, tmp_path):
    app, _ = _app_with_ingestion(monkeypatch, tmp_path, client_id=100)
    client = TestClient(app)
    r = client.post(
        "/api/ingestion/preview",
        data={"client_id": "99", "competencia": "2024-01"},
        files={"file": ("a.csv", csv_standard(), "text/csv")},
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


def test_global_admin_may_select_tenant():
    ctx = TenantContext(1, "admin", 1, is_global_admin=True)
    g = ExplicitTenantGuard(ctx)
    assert g.require_tenant(99).client_id == 99


def test_require_ingestion_tenant_fail_closed_without_factory():
    set_pr4_tenant_guard_factory(None)
    with pytest.raises(AuthRequiredError):
        require_ingestion_tenant(object(), 1)


def test_no_automatic_tmp_db(monkeypatch):
    monkeypatch.delenv("INGESTION_SQLITE_PATH", raising=False)
    monkeypatch.delenv("INGESTION_ALLOW_TEST_DEPENDENCIES", raising=False)
    set_ingestion_repository(None)
    with pytest.raises(IngestionPersistenceError):
        get_ingestion_repository()


def test_repository_refuses_production_path(monkeypatch, tmp_path):
    monkeypatch.setenv("INGESTION_SQLITE_PATH", "/var/www/absenteismo/database/absenteismo.db")
    set_ingestion_repository(None)
    with pytest.raises(Exception):
        get_ingestion_repository()


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


def test_api_preview_happy_with_injected_deps(monkeypatch, tmp_path):
    app, _ = _app_with_ingestion(monkeypatch, tmp_path, client_id=99)
    client = TestClient(app)
    r = client.post(
        "/api/ingestion/preview",
        data={"client_id": "99", "competencia": "2024-01"},
        files={"file": ("a.csv", csv_standard(), "text/csv")},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["preview_id"]
    assert "confirmation_token" in body
    assert "storage_key" not in body
    assert "/var/www" not in str(body)
    assert "/tmp/absenteismo_epic1" not in str(body)


def test_test_deps_env_default_false(monkeypatch):
    monkeypatch.delenv("INGESTION_ALLOW_TEST_DEPENDENCIES", raising=False)
    assert allow_test_dependencies() is False


def test_logging_utils_no_pii_keys():
    from backend.ingestion.logging_utils import safe_log

    safe_log("test", client_id=1, nome="SHOULD_BE_STRIPPED", cpf="123", step="x")
