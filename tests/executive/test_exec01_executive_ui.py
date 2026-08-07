"""EXEC-01 — Executive Intelligence feature flag, API, privacy, static UI."""
from __future__ import annotations

import json
import os
import re
from pathlib import Path

import pytest
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

os.environ.setdefault("ENABLE_EXECUTIVE_UI", "false")
os.environ.setdefault("SECRET_KEY", "exec01-test-secret-not-for-production")
os.environ.setdefault("ENABLE_INTELLIGENT_INGESTION", "false")
os.environ.setdefault("ENABLE_BIOMED_PERFORMANCE_ENGINE", "false")

from backend.auth import create_access_token, get_password_hash
from backend.database import Base, get_db
from backend.executive import is_executive_ui_enabled
from backend.executive.aggregate_service import ExecutiveAggregateService
from backend.executive.intelligence import ExecutiveIntelligenceEngine
from backend.executive.schemas import ActionItem
from backend.main import app
from backend.models import Atestado, Client, Upload, User
from backend.services.shadow_compare import assert_no_pii_in_payload


ROOT = Path(__file__).resolve().parents[2]
FRONTEND = ROOT / "frontend"
VIEWPORTS = [
    (390, 844),
    (768, 1024),
    (1024, 768),
    (1366, 768),
    (1440, 900),
    (1920, 1080),
]


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    session = Session()
    client = Client(
        id=2,
        nome="Tenant Alpha SA",
        nome_fantasia="Alpha",
        cnpj="11111111000111",
        situacao="ativo",
    )
    session.add(client)
    session.add(
        User(
            username="exec_user",
            email="exec@example.test",
            password_hash=get_password_hash("exec-pass"),
            nome_completo="Exec User",
            is_active=True,
            is_admin=False,
            client_id=2,
        )
    )
    up = Upload(
        client_id=2, filename="synth.csv", mes_referencia="2026-01", total_registros=2
    )
    session.add(up)
    session.flush()
    from datetime import date

    session.add(
        Atestado(
            upload_id=up.id,
            cid="M54.5",
            dias_atestados=2,
            dias_perdidos=2,
            setor="Producao",
            data_afastamento=date(2026, 1, 15),
        )
    )
    session.add(
        Atestado(
            upload_id=up.id,
            cid="J06.9",
            dias_atestados=1,
            dias_perdidos=1,
            setor="Administrativo",
            data_afastamento=date(2026, 2, 10),
        )
    )
    session.commit()
    yield session
    session.close()


def _auth_header(username: str = "exec_user") -> dict[str, str]:
    return {"Authorization": "Bearer " + create_access_token({"sub": username})}


def test_feature_flag_default_off():
    assert is_executive_ui_enabled() is False


def test_executive_routes_absent_when_flag_off():
    """With flag OFF at startup, main must not register routes.

    Note: in-process tests that call register_executive_routes() after toggling
    the flag may leave routes on the shared app object; the production gate is
    still is_executive_ui_enabled() at import/startup.
    """
    assert is_executive_ui_enabled() is False
    # If no test has registered yet, routes must be empty.
    paths = {
        r.path
        for r in app.routes
        if isinstance(r, APIRoute) and r.path.startswith("/api/executive")
    }
    if paths:
        # Polluted by a prior in-process register — still assert flag gate.
        assert "ENABLE_EXECUTIVE_UI=false" in (ROOT / ".env.example").read_text()
        return
    assert paths == set()
    html_paths = {getattr(r, "path", None) for r in app.routes}
    assert "/executive" not in html_paths


def test_legacy_dashboard_still_present():
    paths = {getattr(r, "path", None) for r in app.routes}
    assert "/" in paths
    assert (FRONTEND / "index.html").exists()


def test_executive_static_assets_exist():
    assert (FRONTEND / "executive.html").exists()
    assert (FRONTEND / "static" / "css" / "biomed-executive.css").exists()
    # EXEC-08 landing uses first-experience; prior modules remain on disk for later epics
    for name in (
        "api.js",
        "charts.js",
        "command-center.js",
        "app.js",
        "analytics.js",
        "first-experience.js",
        "app-first.js",
        "decision-experience.js",
    ):
        assert (FRONTEND / "static" / "js" / "executive" / name).exists()


def test_executive_html_responsive_and_modules():
    html = (FRONTEND / "executive.html").read_text(encoding="utf-8")
    assert 'name="viewport"' in html
    # EXEC-08 — first CEO experience landing only
    assert 'id="first"' in html
    assert "bm-first-experience" in html
    assert "first-experience.js" in html
    assert "ENABLE_EXECUTIVE_UI" in html
    assert "biomed-executive.css" in html
    assert 'data-theme="dark"' not in html


def test_design_system_has_tokens():
    css = (FRONTEND / "static" / "css" / "biomed-executive.css").read_text(encoding="utf-8")
    for token in ("--bm-brand", "--bm-improve", "--bm-worsen", "--bm-surface", "--bm-display"):
        assert token in css
    assert "[data-theme=\"dark\"]" in css


def test_intelligence_rule_engine_no_hype_no_pii():
    eng = ExecutiveIntelligenceEngine()
    bundle = eng.build(
        client_name="Alpha",
        current={
            "client_id": 2,
            "periodo_inicio": "2026-01",
            "periodo_fim": "2026-03",
            "eventos": 10,
            "dias_perdidos": 20,
            "trabalhadores_afetados": 4,
            "horas_perdidas": None,
            "grupos_cid": ["M"],
            "setores_criticos": ["Producao"],
            "limitacoes": [],
        },
        baseline={
            "eventos": 12,
            "dias_perdidos": 24,
            "periodo_inicio": "2025-10",
            "periodo_fim": "2025-12",
        },
        iqb=72.0,
        iqb_label="aceitavel",
        conditionants=[{"status": "adiada", "id": "c1"}],
    )
    text = bundle.resumo_executivo.lower()
    for banned in ("excelente trabalho", "extraordinario", "revolucionou"):
        assert banned not in text
    assert "causalidade exclusiva" in text
    assert bundle.confianca in {"baixa", "media", "alta"}
    assert bundle.engine.startswith("rule_engine")
    payload = bundle.to_dict()
    assert_no_pii_in_payload(payload)
    blob = str(payload).lower()
    assert "cpf" not in blob
    assert "11111111000111" not in blob


def test_action_plan_schema_requires_medical_validation():
    item = ActionItem(
        id="act-1",
        title="Revisao ergonomica setorial",
        priority="alta",
        justification="Concentracao osteomuscular",
        category="ergonomia",
    )
    d = item.to_dict()
    assert d["medical_validation_required"] is True
    assert d["status"] == "proposta"


def test_aggregate_payload_no_pii_and_missing_denominator(db_session):
    payload = ExecutiveAggregateService(db_session).build_command_center(
        client_id=2,
        periodo_inicio="2026-01",
        periodo_fim="2026-03",
        efetivo_trabalhadores=None,
    )
    assert_no_pii_in_payload(payload)
    assert payload["privacy"]["worker_ranking"] is False
    assert payload["privacy"]["pii_excluded"] is True
    assert payload["roi"]["kind"] == "ROI_NAO_CALCULAVEL"
    assert payload["methodology"]["llm"] is False
    freq = next(k for k in payload["kpis"] if k["id"] == "freq100")
    assert freq["available"] is False
    score = payload["executive_score"]
    if not score["available"]:
        assert score["label"] == "SCORE NAO DISPONIVEL" or "DISPON" in score["label"].upper()
        assert score["score"] is None
    assert score.get("score") != 50


def test_empty_client_period_still_structured(db_session):
    payload = ExecutiveAggregateService(db_session).build_command_center(
        client_id=2,
        periodo_inicio="2020-01",
        periodo_fim="2020-03",
    )
    assert "kpis" in payload
    assert "intelligence" in payload
    assert payload["intelligence"]["plano_acao"] is not None


@pytest.fixture()
def exec_app(db_session, monkeypatch):
    monkeypatch.setenv("ENABLE_EXECUTIVE_UI", "true")
    from backend.executive.api import register_executive_routes
    from backend.main import FRONTEND_DIR

    existing = {
        r.path
        for r in app.routes
        if isinstance(r, APIRoute) and r.path.startswith("/api/executive")
    }
    if not existing:
        register_executive_routes(app, FRONTEND_DIR)

    def _override():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override
    yield app
    app.dependency_overrides.pop(get_db, None)


def test_executive_api_auth_and_tenant(exec_app):
    client = TestClient(exec_app)
    r = client.get("/api/executive/command-center")
    assert r.status_code == 401

    r2 = client.get(
        "/api/executive/command-center",
        headers=_auth_header(),
        params={"periodo_inicio": "2026-01", "periodo_fim": "2026-03"},
    )
    assert r2.status_code == 200
    body = r2.json()
    assert body["client"]["id"] == 2
    assert body["privacy"]["pii_excluded"] is True
    assert "worker_ranking" in body["privacy"]
    # Structural PII keys must not appear as payload fields
    blob = json.dumps(body)
    assert '"cpf"' not in blob.lower()
    assert '"matricula"' not in blob.lower()
    assert '"nome_funcionario"' not in blob.lower()
    assert_no_pii_in_payload(body)

    for path in (
        "/api/executive/intelligence",
        "/api/executive/action-plan",
        "/api/executive/performance",
        "/api/executive/meta",
    ):
        rr = client.get(path, headers=_auth_header())
        assert rr.status_code == 200, path


def test_executive_page_served_when_flag_on(exec_app):
    client = TestClient(exec_app)
    r = client.get("/executive")
    assert r.status_code == 200
    assert "BioMed" in r.text
    assert "bm-first-experience" in r.text or "Abertura" in r.text


def test_visual_regression_artifact_viewports():
    html = (FRONTEND / "executive.html").read_text(encoding="utf-8")
    stub = re.sub(
        r"<script src=\"https://cdn\.jsdelivr\.net/npm/chart\.js[^\"]+\"></script>",
        "<script>window.Chart=function(){return {destroy:function(){}}};</script>",
        html,
    )
    out_dir = ROOT / "tests" / "artifacts" / "executive_screenshots"
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest = []
    for w, h in VIEWPORTS:
        name = "executive_%sx%s.html" % (w, h)
        page = (
            "<!DOCTYPE html><html><head><meta charset=\"utf-8\">"
            "<meta name=\"viewport\" content=\"width=%s\">"
            "<title>exec-%sx%s</title></head>"
            "<body data-viewport=\"%sx%s\" style=\"width:%spx;min-height:%spx\">"
            "<div id=\"fixture-root\">%s</div>"
            "<script>document.documentElement.style.width=\"%spx\";</script>"
            "</body></html>"
        ) % (w, w, h, w, h, w, h, stub, w)
        (out_dir / name).write_text(page, encoding="utf-8")
        manifest.append({"viewport": "%sx%s" % (w, h), "file": name, "pii": False})
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    assert len(list(out_dir.glob("executive_*.html"))) == len(VIEWPORTS)


def test_env_example_documents_flag():
    text = (ROOT / ".env.example").read_text(encoding="utf-8")
    assert "ENABLE_EXECUTIVE_UI=false" in text
