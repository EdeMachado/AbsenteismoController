"""EXEC-02 — visual structure, empty states, narrative tone, accessibility basics."""
from __future__ import annotations

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
os.environ.setdefault("SECRET_KEY", "exec02-test-secret-not-for-production")
os.environ.setdefault("ENABLE_INTELLIGENT_INGESTION", "false")
os.environ.setdefault("ENABLE_BIOMED_PERFORMANCE_ENGINE", "false")
os.environ.setdefault("EXECUTIVE_STAGING_DEMO", "false")

from backend.auth import create_access_token, get_password_hash
from backend.database import Base, get_db
from backend.executive.aggregate_service import ExecutiveAggregateService
from backend.executive.intelligence import ExecutiveIntelligenceEngine
from backend.main import app
from backend.models import Atestado, Client, Upload, User
from backend.services.shadow_compare import assert_no_pii_in_payload

ROOT = Path(__file__).resolve().parents[2]
FRONTEND = ROOT / "frontend"


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
    session.add(
        Client(
            id=2,
            nome="Tenant Alpha SA",
            nome_fantasia="Alpha",
            cnpj="11111111000111",
            situacao="ativo",
        )
    )
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
    up = Upload(client_id=2, filename="a.xlsx", mes_referencia="2026-01", total_registros=1)
    session.add(up)
    session.flush()
    session.add(
        Atestado(
            upload_id=up.id,
            cid="M54.5",
            dias_atestados=2,
            dias_perdidos=2,
            horas_perdi=16,
            horas_perdidas=16,
            setor="Operacional",
        )
    )
    session.commit()
    yield session
    session.close()


def test_html_has_hero_and_reading_order():
    html = (FRONTEND / "executive.html").read_text(encoding="utf-8")
    # EXEC-08 first experience reading order
    assert 'id="bm-first-experience"' in html
    assert "Abertura" in html or "abertura" in html.lower()
    assert "bm-nav-toggle" in html
    assert "aria-label" in html
    assert "chart-temporal" not in html


def test_css_has_responsive_and_a11y_tokens():
    css = (FRONTEND / "static" / "css" / "biomed-executive.css").read_text(encoding="utf-8")
    assert "@media (max-width: 820px)" in css
    assert ":focus-visible" in css
    assert ".bm-hero" in css
    assert ".bm-kpi--empty" in css
    assert ".bm-chart-empty" in css
    assert ".bm-perf-grid" in css
    assert ".bm-action-board" in css


def test_no_fake_zeros_for_missing_frequency(db_session):
    payload = ExecutiveAggregateService(db_session).build_command_center(
        client_id=2,
        periodo_inicio="2026-01",
        periodo_fim="2026-01",
        efetivo_trabalhadores=None,
    )
    freq = next(k for k in payload["kpis"] if k["id"] == "freq100")
    assert freq["available"] is False
    assert freq["value"] is None or freq["available"] is False
    assert "Headcount" in (freq.get("empty_label") or freq.get("unavailable_reason") or "")
    assert payload["roi"]["kind"] == "ROI_NAO_CALCULAVEL"
    assert payload["roi"]["valor"] is None


def test_kpi_hierarchy_primary_secondary(db_session):
    payload = ExecutiveAggregateService(db_session).build_command_center(
        client_id=2, periodo_inicio="2026-01", periodo_fim="2026-01"
    )
    prim = {k["id"] for k in payload["kpis_primary"]}
    sec = {k["id"] for k in payload["kpis_secondary"]}
    # Core EXEC-02 primaries; EXEC-03 may add "custo" when hourly assumption is available.
    assert {"dias", "horas", "eventos", "trabalhadores"}.issubset(prim)
    assert prim <= {"dias", "horas", "eventos", "trabalhadores", "custo"}
    assert "iqb" in sec
    assert "freq100" in sec
    assert "effectiveness" not in prim
    assert "biomed_perf" not in prim


def test_hero_and_confidence_present(db_session):
    payload = ExecutiveAggregateService(db_session).build_command_center(
        client_id=2, periodo_inicio="2026-01", periodo_fim="2026-01"
    )
    hero = payload["hero"]
    assert "empresa" in hero
    assert "mensagem" in hero
    assert "confianca" in hero
    assert hero["score"]["available"] in (True, False)
    if not hero["score"]["available"]:
        assert hero["score"]["score"] is None
        assert hero["score"].get("score") != 50


def test_performance_separation_keys(db_session, monkeypatch):
    monkeypatch.setenv("EXECUTIVE_STAGING_DEMO", "true")
    payload = ExecutiveAggregateService(db_session).build_command_center(
        client_id=2, periodo_inicio="2026-01", periodo_fim="2026-01"
    )
    bp = payload["biomed_performance"]
    assert "producao" in bp
    assert "resultado_observado" in bp
    assert "efetividade" in bp
    assert payload["conditionants_summary"]


def test_narrative_tone_no_hype():
    eng = ExecutiveIntelligenceEngine()
    bundle = eng.build(
        client_name="Alpha",
        current={
            "client_id": 2,
            "periodo_inicio": "2026-01",
            "periodo_fim": "2026-03",
            "eventos": 10,
            "dias_perdidos": 20,
            "setores_criticos": ["Operacional"],
            "grupos_cid": ["M"],
            "limitacoes": [],
        },
        baseline={"eventos": 14, "dias_perdidos": 30, "periodo_inicio": "2025-10", "periodo_fim": "2025-12"},
        iqb=85.0,
        iqb_label="bom",
        biomed_performance={"cobertura": 0.91, "execucao": 0.88},
        conditionants=[{"status": "adiada", "id": "c1"}],
    )
    blob = (bundle.resumo_executivo + " " + bundle.mensagem_executiva).lower()
    for banned in ("excelente trabalho", "extraordinário", "revolucionou", "incrível"):
        assert banned not in blob
    assert "causalidade exclusiva" in bundle.resumo_executivo.lower() or "causalidade exclusiva" in " ".join(
        bundle.limitacoes
    ).lower() or "atribuição causal" in blob or "causalidade exclusiva" in blob
    assert bundle.mensagem_executiva
    assert bundle.o_que_mudou
    assert bundle.o_que_precisa_validacao


def test_action_plan_requires_medical_validation(db_session, monkeypatch):
    monkeypatch.setenv("EXECUTIVE_STAGING_DEMO", "true")
    payload = ExecutiveAggregateService(db_session).build_command_center(
        client_id=2, periodo_inicio="2026-01", periodo_fim="2026-01"
    )
    actions = payload["intelligence"]["plano_acao"]
    assert actions
    for a in actions:
        assert a.get("medical_validation_required") is True


def test_homologation_screenshots_exist():
    out = ROOT / "tests" / "artifacts" / "executive_screenshots"
    for w, h in [(390, 844), (768, 1024), (1024, 768), (1366, 768), (1440, 900), (1920, 1080)]:
        assert (out / f"executive_{w}x{h}.png").exists()
        assert (out / f"homolog_command_{w}x{h}.png").exists()
    for mod in (
        "performance",
        "actions",
        "intelligence",
        "quality",
        "absenteeism",
        "epidemiology",
        "sectors",
        "productivity",
    ):
        assert (out / f"homolog_module_{mod}_1440x900.png").exists()


def test_legacy_dashboard_preserved_and_flag_default_off():
    from backend.executive import is_executive_ui_enabled

    # Default for this module: flag off (staging/demo must be explicit).
    assert os.environ.get("ENABLE_EXECUTIVE_UI", "false").lower() in {"false", "0", "off", ""}
    assert (FRONTEND / "index.html").exists()
    assert (FRONTEND / "executive.html").exists()
    paths = {getattr(r, "path", None) for r in app.routes}
    assert "/" in paths
    # is_executive_ui_enabled follows env; other tests may flip env temporarily via monkeypatch
    assert is_executive_ui_enabled() is False or os.environ.get("ENABLE_EXECUTIVE_UI") == "true"
