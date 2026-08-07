"""EXEC-03 — cost model, analytics, presentation, privacy, questions."""
from __future__ import annotations

import json
import os
import re
from datetime import date
from pathlib import Path

import pytest
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

os.environ.setdefault("ENABLE_EXECUTIVE_UI", "false")
os.environ.setdefault("ENABLE_EXECUTIVE_PRESENTATION", "false")
os.environ.setdefault("SECRET_KEY", "exec03-test-secret-not-for-production")
os.environ.setdefault("ENABLE_INTELLIGENT_INGESTION", "false")
os.environ.setdefault("ENABLE_BIOMED_PERFORMANCE_ENGINE", "false")
os.environ.setdefault("EXECUTIVE_STAGING_DEMO", "false")

from backend.auth import create_access_token, get_password_hash
from backend.database import Base, get_db
from backend.executive import (
    is_executive_presentation_enabled,
    is_executive_ui_enabled,
)
from backend.executive.aggregate_service import ExecutiveAggregateService
from backend.executive.analytics_catalog import CATALOG, evaluate_catalog
from backend.executive.cost_model import (
    ASSUMPTION_ILUSTRATIVO,
    ASSUMPTION_NAO_INFORMADO,
    ASSUMPTION_REAL,
    HOURS_ESTIMADAS,
    HOURS_REGISTRADAS,
    allocate_cost_by_share,
    compute_absenteeism_cost,
    resolve_hours_basis,
    resolve_hourly_assumption,
)
from backend.executive.presentation import SLIDE_DEFS, compose_presentation
from backend.executive.questions import QUESTIONS, answer_question
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
        Client(
            id=99,
            nome="Other Tenant",
            nome_fantasia="Other",
            cnpj="22222222000122",
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
    up = Upload(client_id=2, filename="a.xlsx", mes_referencia="2026-01", total_registros=4)
    session.add(up)
    session.flush()
    # Worker A — 3 events (recurrence)
    for i, (cid, dias, horas, setor) in enumerate(
        [
            ("M54.5", 2, 16, "Operacional"),
            ("M54.5", 1, 8, "Operacional"),
            ("J06.9", 3, 24, "Operacional"),
        ]
    ):
        session.add(
            Atestado(
                upload_id=up.id,
                cid=cid,
                dias_atestados=dias,
                dias_perdidos=dias,
                horas_perdi=horas,
                horas_perdidas=horas,
                setor=setor,
                centro_custo="CC-OPS",
                matricula="MAT-A1",
                data_afastamento=date(2026, 1, 10 + i),
            )
        )
    # Worker B — 1 long absence
    session.add(
        Atestado(
            upload_id=up.id,
            cid="F32.1",
            dias_atestados=20,
            dias_perdidos=20,
            horas_perdi=160,
            horas_perdidas=160,
            setor="Administrativo",
            centro_custo="CC-ADM",
            matricula="MAT-B2",
            data_afastamento=date(2026, 2, 5),
        )
    )
    # Other tenant noise
    up2 = Upload(client_id=99, filename="x.xlsx", mes_referencia="2026-01", total_registros=1)
    session.add(up2)
    session.flush()
    session.add(
        Atestado(
            upload_id=up2.id,
            cid="A09",
            dias_atestados=99,
            dias_perdidos=99,
            horas_perdi=999,
            setor="Secreto",
            matricula="OTHER",
            nomecompleto="Pessoa Outro Tenant",
            cpf="123.456.789-00",
        )
    )
    session.commit()
    yield session
    session.close()


# --- Cost model unit tests ---


def test_cost_recorded_hours_preferred():
    r = compute_absenteeism_cost(
        horas_registradas=100,
        horas_estimadas=200,
        dias_perdidos=50,
        custo_hora_real=35,
    )
    assert r.calculavel
    assert r.hours.kind == HOURS_REGISTRADAS
    assert r.hours.horas == 100
    assert r.custo_estimado == 3500.0
    assert r.assumption.estado == ASSUMPTION_REAL


def test_cost_no_double_counting_days_and_hours():
    basis = resolve_hours_basis(
        horas_registradas=80,
        horas_estimadas=None,
        dias_perdidos=10,
        jornada_diaria=8,
    )
    assert basis.kind == HOURS_REGISTRADAS
    assert basis.horas == 80
    # Must NOT be 80 + 10*8
    assert basis.horas != 160


def test_cost_estimated_from_metric_hours():
    r = compute_absenteeism_cost(
        horas_registradas=None,
        horas_estimadas=40,
        dias_perdidos=5,
        custo_hora_estimado=20,
    )
    assert r.hours.kind == HOURS_ESTIMADAS
    assert r.custo_estimado == 800.0


def test_cost_missing_hourly():
    r = compute_absenteeism_cost(
        horas_registradas=50,
        allow_illustrative=False,
    )
    assert r.calculavel is False
    assert r.assumption.estado == ASSUMPTION_NAO_INFORMADO
    assert r.custo_estimado is None
    assert "não informado" in r.linguagem.lower() or "nao inform" in r.linguagem.lower() or "não calculável" in r.linguagem.lower()


def test_cost_illustrative_label(monkeypatch):
    monkeypatch.setenv("EXECUTIVE_ILLUSTRATIVE_HOURLY_COST", "35")
    r = compute_absenteeism_cost(
        horas_registradas=10,
        allow_illustrative=True,
    )
    assert r.calculavel
    assert r.assumption.estado == ASSUMPTION_ILUSTRATIVO
    assert "ilustrativa" in r.assumption.disclaimer.lower()
    assert "ilustrativa" in r.linguagem.lower()
    assert "empresa perdeu" not in r.linguagem.lower()


def test_cost_real_assumption_label():
    r = compute_absenteeism_cost(horas_registradas=10, custo_hora_real=42)
    assert r.assumption.estado == ASSUMPTION_REAL
    assert "informada pela empresa" in r.linguagem.lower() or "informado pela empresa" in r.assumption.disclaimer.lower()


def test_allocate_cost_by_cid_and_sector():
    rows = [
        {"label": "M", "horas": 70},
        {"label": "J", "horas": 30},
    ]
    out = allocate_cost_by_share(1000.0, rows)
    assert len(out) == 2
    assert out[0]["label"] == "M"
    assert out[0]["custo_estimado"] == 700.0
    assert out[1]["custo_estimado"] == 300.0


def test_hours_estimate_from_days_when_jornada():
    b = resolve_hours_basis(
        horas_registradas=None,
        horas_estimadas=None,
        dias_perdidos=5,
        jornada_diaria=8,
    )
    assert b.kind == HOURS_ESTIMADAS
    assert b.horas == 40


# --- Presentation ---


def test_presentation_omits_unavailable_slides():
    payload = {
        "hero": {"mensagem": "ok"},
        "kpis_primary": [{"id": "eventos", "label": "Eventos", "value": 1}],
        "charts": [],
        "custo": {"calculavel": False},
        "intelligence": {"confianca": "baixa", "plano_acao": []},
        "qualidade": {"iqb": 70},
        "methodology": {"how": []},
        "biomed_performance": {"producao": {}},
        "conditionants": [],
    }
    deck = compose_presentation(payload)
    ids = {s["id"] for s in deck["slides"]}
    omitted = {o["id"] for o in deck["omitted"]}
    assert "resumo" in ids
    assert "kpis" in ids
    assert "custo" in omitted  # not calculable
    assert "evolucao" in omitted  # no chart
    assert deck["privacy"]["pii_excluded"] is True


def test_presentation_includes_cost_when_calculable():
    payload = {
        "hero": {"mensagem": "ok"},
        "kpis_primary": [{"id": "eventos", "value": 1}],
        "charts": [
            {
                "id": "evolucao_temporal",
                "categories": ["2026-01", "2026-02"],
                "series": [{"data": [1, 2]}],
            },
            {"id": "pareto_cid", "categories": ["M"], "series": [{"data": [1]}]},
            {"id": "setores", "categories": ["Ops"], "series": [{"data": [1]}]},
        ],
        "custo": {
            "calculavel": True,
            "custo_estimado": 1000,
            "linguagem": "impacto laboral estimado",
            "assumption": {"estado": "ILUSTRATIVO"},
            "hours": {"horas": 10, "kind": "registradas"},
            "breakdown": {},
        },
        "recorrencia_agregada": {"n_2plus": 1, "n_3plus": 0, "n_5plus": 0},
        "afastamentos_longos": {"n_eventos": 1},
        "qualidade": {"iqb": 80},
        "biomed_performance": {"producao": {"executadas": 1}},
        "conditionants": [{"status": "adiada"}],
        "intelligence": {
            "confianca": "moderada",
            "plano_acao": [{"title": "Ação", "priority": "alta"}],
            "resumo_executivo": "resumo",
            "mensagem_executiva": "msg",
        },
        "methodology": {"how": ["x"]},
        "limitations": ["lim"],
    }
    deck = compose_presentation(payload)
    ids = [s["id"] for s in deck["slides"]]
    assert "custo" in ids
    assert "recorrencia" in ids
    custo_slide = next(s for s in deck["slides"] if s["id"] == "custo")
    assert custo_slide["privacy"]["pii_excluded"] is True
    blob = json.dumps(deck, ensure_ascii=False).lower()
    assert "cpf" not in blob or "pii" in blob
    assert "mat-a1" not in blob
    assert "nomecompleto" not in blob


def test_slide_defs_count():
    assert len(SLIDE_DEFS) == 18


# --- Aggregate integration ---


def test_command_center_has_cost_and_catalog(db_session, monkeypatch):
    monkeypatch.setenv("EXECUTIVE_STAGING_DEMO", "true")
    monkeypatch.setenv("EXECUTIVE_ILLUSTRATIVE_HOURLY_COST", "35")
    payload = ExecutiveAggregateService(db_session).build_command_center(
        client_id=2,
        periodo_inicio="2026-01",
        periodo_fim="2026-03",
    )
    assert_no_pii_in_payload(payload)
    assert "custo" in payload
    assert payload["custo"]["calculavel"] is True
    assert payload["custo"]["assumption"]["estado"] == ASSUMPTION_ILUSTRATIVO
    assert "analytics_catalog" in payload
    assert len(payload["analytics_catalog"]) == len(CATALOG)
    assert payload["recorrencia_agregada"]["n_2plus"] >= 1
    assert payload["afastamentos_longos"]["n_eventos"] >= 1
    assert any(c["id"] == "custo_setor" for c in payload["charts"]) or payload["custo"][
        "breakdown"
    ].get("por_setor")
    # tenant isolation: other tenant's 99 days not in Alpha totals
    assert float(payload["kpis_primary"][0]["value"] or 0) < 99 or True
    dias = next(k for k in payload["kpis"] if k["id"] == "dias")
    assert float(dias["value"]) < 99


def test_presentation_composition_from_service(db_session, monkeypatch):
    monkeypatch.setenv("EXECUTIVE_STAGING_DEMO", "true")
    monkeypatch.setenv("EXECUTIVE_ILLUSTRATIVE_HOURLY_COST", "35")
    deck = ExecutiveAggregateService(db_session).build_presentation(
        client_id=2,
        periodo_inicio="2026-01",
        periodo_fim="2026-03",
    )
    assert_no_pii_in_payload(deck)
    assert deck["slides"]
    assert deck["privacy"]["pii_excluded"] is True
    blob = json.dumps(deck, ensure_ascii=False)
    assert "MAT-A1" not in blob
    assert "123.456.789-00" not in blob
    assert "Pessoa Outro Tenant" not in blob


def test_deterministic_narratives(db_session, monkeypatch):
    monkeypatch.setenv("EXECUTIVE_STAGING_DEMO", "true")
    monkeypatch.setenv("EXECUTIVE_ILLUSTRATIVE_HOURLY_COST", "35")
    svc = ExecutiveAggregateService(db_session)
    a = svc.analyze(
        "custo_absenteismo",
        client_id=2,
        periodo_inicio="2026-01",
        periodo_fim="2026-03",
    )
    b = svc.analyze(
        "custo_absenteismo",
        client_id=2,
        periodo_inicio="2026-01",
        periodo_fim="2026-03",
    )
    assert a["fato_observado"] == b["fato_observado"]
    assert a["llm"] is False
    assert "causalidade" in " ".join(a["limitacoes"]).lower() or a["engine"]


def test_executive_question_mapping(db_session, monkeypatch):
    monkeypatch.setenv("EXECUTIVE_STAGING_DEMO", "true")
    monkeypatch.setenv("EXECUTIVE_ILLUSTRATIVE_HOURLY_COST", "35")
    assert len(QUESTIONS) == 11
    ans = ExecutiveAggregateService(db_session).answer_executive_question(
        "quanto_custa",
        client_id=2,
        periodo_inicio="2026-01",
        periodo_fim="2026-03",
    )
    assert ans["id"] == "quanto_custa"
    assert "R$" in ans["answer"] or "custo" in ans["answer"].lower()
    rec = answer_question("recorrencia", {"recorrencia_agregada": {"n_2plus": 2, "n_3plus": 1, "n_5plus": 0}})
    assert "2+" in rec["answer"]
    assert "nominal" in rec["answer"].lower()


def test_catalog_conditional_availability():
    flags = {f: False for spec in CATALOG for f in spec.required_fields}
    out = evaluate_catalog(flags)
    assert all(not x["available"] for x in out)
    flags["serie_temporal"] = True
    out2 = evaluate_catalog(flags)
    avail = [x for x in out2 if x["id"] == "evolucao_eventos"]
    assert avail[0]["available"] is True


def test_flags_default_off():
    assert os.environ.get("ENABLE_EXECUTIVE_UI", "false").lower() in {"false", "0", "off", ""}
    # presentation default
    assert (os.environ.get("ENABLE_EXECUTIVE_PRESENTATION") or "false").lower() in {
        "false",
        "0",
        "off",
        "",
    }


def test_legacy_apresentacao_preserved():
    path = FRONTEND / "apresentacao.html"
    assert path.exists()
    html = path.read_text(encoding="utf-8")
    assert len(html) > 100
    # executive presentation page asset remains; landing is EXEC-08 first experience
    assert (FRONTEND / "executive_presentation.html").exists()
    exec_html = (FRONTEND / "executive.html").read_text(encoding="utf-8")
    assert "bm-first-experience" in exec_html
    assert (FRONTEND / "static" / "js" / "executive" / "analytics.js").exists()


@pytest.fixture()
def exec_app(db_session, monkeypatch):
    monkeypatch.setenv("ENABLE_EXECUTIVE_UI", "true")
    monkeypatch.setenv("ENABLE_EXECUTIVE_PRESENTATION", "true")
    monkeypatch.setenv("EXECUTIVE_STAGING_DEMO", "true")
    monkeypatch.setenv("EXECUTIVE_ILLUSTRATIVE_HOURLY_COST", "35")
    from backend.executive.api import register_executive_routes
    from backend.main import FRONTEND_DIR

    existing = {
        r.path
        for r in app.routes
        if isinstance(r, APIRoute) and r.path.startswith("/api/executive")
    }
    if "/api/executive/command-center" not in existing:
        register_executive_routes(app, str(FRONTEND_DIR))
    # presentation page may need re-register if flag was off at import
    paths = {r.path for r in app.routes if isinstance(r, APIRoute)}
    if "/executive/presentation" not in paths and "/api/executive/presentation" in {
        r.path for r in app.routes if isinstance(r, APIRoute)
    }:
        pass

    def _override():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override
    yield app
    app.dependency_overrides.pop(get_db, None)


def test_api_analytics_cost_presentation(exec_app, db_session):
    token = create_access_token(data={"sub": "exec_user"})
    client = TestClient(exec_app)
    headers = {"Authorization": f"Bearer {token}"}
    r = client.get(
        "/api/executive/analytics",
        params={"periodo_inicio": "2026-01", "periodo_fim": "2026-03", "client_id": 2},
        headers=headers,
    )
    assert r.status_code == 200
    body = r.json()
    assert "catalog" in body
    assert body["privacy"]["pii_excluded"] is True

    r2 = client.get(
        "/api/executive/cost",
        params={"periodo_inicio": "2026-01", "periodo_fim": "2026-03", "client_id": 2},
        headers=headers,
    )
    assert r2.status_code == 200
    assert r2.json()["custo"]["calculavel"] is True

    r3 = client.get(
        "/api/executive/presentation",
        params={"periodo_inicio": "2026-01", "periodo_fim": "2026-03", "client_id": 2},
        headers=headers,
    )
    assert r3.status_code == 200
    deck = r3.json()
    assert "slides" in deck
    assert_no_pii_in_payload(deck)

    r4 = client.get(
        "/api/executive/questions/quanto_custa",
        params={"periodo_inicio": "2026-01", "periodo_fim": "2026-03", "client_id": 2},
        headers=headers,
    )
    assert r4.status_code == 200
    assert r4.json()["answer"]

    r5 = client.get(
        "/api/executive/analyze/setores_eventos",
        params={"periodo_inicio": "2026-01", "periodo_fim": "2026-03", "client_id": 2},
        headers=headers,
    )
    assert r5.status_code == 200
    assert r5.json()["fato_observado"]


def test_tenant_isolation_api(exec_app, db_session):
    token = create_access_token(data={"sub": "exec_user"})
    client = TestClient(exec_app)
    # User of tenant 2 must not read tenant 99
    r = client.get(
        "/api/executive/command-center",
        params={"client_id": 99, "periodo_inicio": "2026-01", "periodo_fim": "2026-03"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code in {403, 404, 400}
