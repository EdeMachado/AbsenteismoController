"""FIT-02 staging gate — flags, startup, security matrix, foundation modules."""

from __future__ import annotations

import hashlib
import os
import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.performance import is_performance_engine_enabled
from backend.performance.performance_shadow_service import PerformanceShadowService
from backend.performance.privacy import assert_no_pii
from backend.performance.schemas import ActionCounts
from backend.services.data_quality_service import DataQualityService
from backend.services.metric_service import MetricService
from tests.fixtures.performance.canonical_db import (
    make_memory_session,
    seed_performance_adapter_fixture,
)


@pytest.fixture
def clean_flags(monkeypatch):
    monkeypatch.delenv("ENABLE_INTELLIGENT_INGESTION", raising=False)
    monkeypatch.delenv("ENABLE_BIOMED_PERFORMANCE_ENGINE", raising=False)
    monkeypatch.delenv("INGESTION_ALLOW_TEST_DEPENDENCIES", raising=False)
    monkeypatch.delenv("INGESTION_SQLITE_PATH", raising=False)


def test_flags_default_off(clean_flags):
    from backend.ingestion import is_intelligent_ingestion_enabled

    assert is_intelligent_ingestion_enabled() is False
    assert is_performance_engine_enabled() is False


def test_ingestion_routes_absent_when_flag_off(clean_flags, monkeypatch):
    monkeypatch.setenv("ENABLE_INTELLIGENT_INGESTION", "false")
    # Import app after flag clear — main already imported; check register helper
    from backend.ingestion.api import register_ingestion_routes
    from fastapi import FastAPI

    app = FastAPI()
    assert register_ingestion_routes(app, "/tmp") is False
    paths = [getattr(r, "path", None) for r in app.routes]
    assert not any(p and str(p).startswith("/api/ingestion") for p in paths)


def test_database_path_refuses_production_override(monkeypatch):
    monkeypatch.setenv(
        "ABSENTEISMO_SQLITE_PATH",
        "/var/www/absenteismo/database/absenteismo.db",
    )
    with pytest.raises(RuntimeError):
        from backend import database as dbmod

        dbmod._resolve_db_path()


def test_canonical_and_iqb_synthetic():
    db = make_memory_session()
    seed_performance_adapter_fixture(db)
    try:
        m = MetricService(db).compute(2, "2025-05", "2025-07", efetivo_trabalhadores=100)
        q = DataQualityService(db).analyze(2, "2025-05", "2025-07")
        assert m.metricas.eventos > 0
        assert m.metricas.horas_perdidas_registradas >= 0
        assert 0 <= q.iqb <= 100
        payload = {"metrics": m.to_dict(), "iqb": q.to_dict()}
        assert_no_pii(payload)
    finally:
        db.close()


def test_performance_shadow_roi_and_limits():
    db = make_memory_session()
    seed_performance_adapter_fixture(db)
    try:
        svc = PerformanceShadowService(db)
        result = svc.analyze(
            client_id=2,
            baseline_inicio="2025-05",
            baseline_fim="2025-07",
            atual_inicio="2026-05",
            atual_fim="2026-07",
            efetivo_trabalhadores=100,
        )
        assert result.roi.get("kind") == "ROI_NAO_CALCULAVEL"
        assert result.productivity_mode == "ausente"
        assert_no_pii(result.to_dict())

        with_costs = svc.analyze(
            client_id=2,
            baseline_inicio="2025-05",
            baseline_fim="2025-07",
            atual_inicio="2026-05",
            atual_fim="2026-07",
            efetivo_trabalhadores=100,
            custo_programa=1000.0,
            custo_hora=50.0,
            acoes=ActionCounts(aprovadas=2, aplicaveis=2, executadas=1),
        )
        assert with_costs.roi.get("kind") in {
            "ROI_OBSERVADO",
            "ROI_ESTIMADO",
            "ROI_NAO_CALCULAVEL",
        }
    finally:
        db.close()


def test_critical_api_auth_matrix(tmp_path, monkeypatch):
    """Staging-like disposable DB: 401 without token; tenant isolation."""
    db_path = tmp_path / "fit02_legacy.sqlite"
    monkeypatch.setenv("ABSENTEISMO_SQLITE_PATH", str(db_path))
    monkeypatch.setenv("ENABLE_INTELLIGENT_INGESTION", "false")
    monkeypatch.setenv("ENABLE_BIOMED_PERFORMANCE_ENGINE", "false")

    # Re-bind engine to disposable DB
    import backend.database as database

    database.DB_PATH = str(db_path)
    database.SQLALCHEMY_DATABASE_URL = f"sqlite:///{db_path}"
    database.engine = database.create_engine(
        database.SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False},
    )
    database.SessionLocal = database.sessionmaker(
        autocommit=False, autoflush=False, bind=database.engine
    )
    database.Base.metadata.create_all(bind=database.engine)

    from backend.auth import get_password_hash, create_access_token
    from backend.models import Client, User

    db = database.SessionLocal()
    try:
        db.add(Client(id=101, nome="Empresa A Sintetica", nome_fantasia="A"))
        db.add(Client(id=102, nome="Empresa B Sintetica", nome_fantasia="B"))
        db.flush()
        db.add(
            User(
                username="user_a",
                email="user_a@fit02.test",
                password_hash=get_password_hash("senha-a-fit02"),
                is_admin=False,
                is_active=True,
                client_id=101,
            )
        )
        db.add(
            User(
                username="user_b",
                email="user_b@fit02.test",
                password_hash=get_password_hash("senha-b-fit02"),
                is_admin=False,
                is_active=True,
                client_id=102,
            )
        )
        db.add(
            User(
                username="admin_fit02",
                email="admin@fit02.test",
                password_hash=get_password_hash("senha-admin-fit02"),
                is_admin=True,
                is_active=True,
                client_id=None,
            )
        )
        db.commit()
    finally:
        db.close()

    # Import app late
    from backend.main import app

    client = TestClient(app)

    # health
    h = client.get("/api/health")
    assert h.status_code == 200

    # no token
    r = client.get("/api/clientes")
    assert r.status_code in {401, 403}

    # login A
    la = client.post("/api/auth/login", data={"username": "user_a", "password": "senha-a-fit02"})
    if la.status_code != 200:
        # some deployments use JSON login
        la = client.post(
            "/api/auth/login", json={"username": "user_a", "password": "senha-a-fit02"}
        )
    assert la.status_code == 200, la.text
    token_a = la.json().get("access_token") or la.json().get("token")
    assert token_a
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # forged client
    forged = client.get("/api/uploads?client_id=102", headers=headers_a)
    assert forged.status_code in {403, 404, 422, 400}

    # experimental off
    exp = client.get("/api/ingestion/mapping-profiles?client_id=101", headers=headers_a)
    assert exp.status_code in {404, 405, 401, 403}

    # invalid token
    bad = client.get(
        "/api/clientes", headers={"Authorization": "Bearer token-invalido-fit02"}
    )
    assert bad.status_code == 401

    # fingerprint unchanged after reads
    sha1 = hashlib.sha256(db_path.read_bytes()).hexdigest()
    client.get("/api/health")
    sha2 = hashlib.sha256(db_path.read_bytes()).hexdigest()
    assert sha1 == sha2


def test_env_example_flags_off():
    text = Path("/workspace/.env.example").read_text(encoding="utf-8")
    assert "ENABLE_INTELLIGENT_INGESTION=false" in text
    assert "ENABLE_BIOMED_PERFORMANCE_ENGINE=false" in text
    assert "<<<<<<<" not in text
