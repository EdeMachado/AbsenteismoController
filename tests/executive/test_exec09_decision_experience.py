"""EXEC-09 — Executive Decision Experience contract, privacy, static UI."""
from __future__ import annotations

import os
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
os.environ.setdefault("SECRET_KEY", "exec09-test-secret-not-for-production")
os.environ.setdefault("ENABLE_INTELLIGENT_INGESTION", "false")
os.environ.setdefault("ENABLE_BIOMED_PERFORMANCE_ENGINE", "false")
os.environ.setdefault("EXECUTIVE_STAGING_DEMO", "false")

from backend.auth import create_access_token, get_password_hash
from backend.database import Base, get_db
from backend.executive.aggregate_service import ExecutiveAggregateService
from backend.executive.decision_experience import compose_decision_experience
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
            nome_fantasia="Alpha Corp",
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
    up = Upload(client_id=2, filename="a.xlsx", mes_referencia="2026-01", total_registros=2)
    session.add(up)
    session.flush()
    session.add(
        Atestado(
            upload_id=up.id,
            cid="M54.5",
            dias_atestados=5,
            dias_perdidos=5,
            horas_perdi=40,
            horas_perdidas=40,
            setor="Operacional",
            data_afastamento=date(2026, 1, 12),
        )
    )
    session.add(
        Atestado(
            upload_id=up.id,
            cid="J06.9",
            dias_atestados=1,
            dias_perdidos=1,
            horas_perdi=8,
            horas_perdidas=8,
            setor="Administrativo",
            data_afastamento=date(2026, 2, 8),
        )
    )
    session.commit()
    yield session
    session.close()


def test_decision_experience_six_answers(db_session, monkeypatch):
    monkeypatch.setenv("EXECUTIVE_STAGING_DEMO", "true")
    monkeypatch.setenv("EXECUTIVE_ILLUSTRATIVE_HOURLY_COST", "35")
    payload = ExecutiveAggregateService(db_session).build_command_center(
        client_id=2, periodo_inicio="2026-01", periodo_fim="2026-03"
    )
    dx = payload["decision_experience"]
    assert_no_pii_in_payload(dx)
    six = dx["six_answers"]
    for key in ("problem", "how_we_know", "cost", "save", "how", "first_step"):
        assert six.get(key), key
    assert dx["header"]["title"]
    assert dx["header"]["priority_label"]
    assert len(dx["why"]) <= 3
    assert 1 <= len(dx["recommendations"]) <= 3
    assert len(dx["roadmap"]) == 4
    assert {r["horizon"] for r in dx["roadmap"]} == {
        "30 dias",
        "90 dias",
        "180 dias",
        "365 dias",
    }
    assert set(dx["expected_results"]) == {
        "financial",
        "operational",
        "health",
        "governance",
    }
    assert dx["confidence"]["level"] in {"Alta", "Média", "Baixa"}
    assert "ORBIT" in dx["footer_note"]
    assert "comprar" not in dx["footer_note"].lower()
    assert "contratar" not in dx["footer_note"].lower()


def test_business_impact_never_invents_without_assumption():
    payload = {
        "hero": {"mensagem": "Estado descritivo.", "confianca": "baixa", "tendencia": None},
        "intelligence": {"plano_acao": [], "o_que_recomendamos": ["Ação A"]},
        "custo": {
            "calculavel": False,
            "custo_estimado": None,
            "assumption": {"estado": "NAO_INFORMADO"},
            "hours": {"horas": None},
        },
        "charts": [],
        "first_experience": {
            "decision": {
                "title": "Ação A",
                "priority": "alta",
                "description": "Desc",
                "expected_impact": "Impacto",
                "deadline": "30 dias",
            },
            "kpis": [],
        },
        "impacto_economico_biomed": {},
    }
    dx = compose_decision_experience(payload)
    assert dx["business_impact"]["cost_today"]["available"] is False
    assert dx["business_impact"]["cost_today"]["value"] is None
    assert dx["business_impact"]["savings_potential"]["available"] is False
    assert dx["business_impact"]["savings_potential"]["value"] is None
    assert "NÃO INFORMADO" in dx["business_impact"]["cost_today"]["assumption_state"]


def test_suppressed_labels_not_shown_to_ceo():
    payload = {
        "hero": {"mensagem": "Estado.", "confianca": "moderada", "tendencia": "melhora"},
        "intelligence": {
            "plano_acao": [
                {
                    "title": "Revisão ergonômica no setor Operacional",
                    "priority": "alta",
                    "category": "ergonomia",
                    "meta": "redução setorial",
                }
            ],
            "onde_esta_o_risco": ["Concentração setorial: GRUPO_SUPRIMIDO"],
        },
        "custo": {
            "calculavel": True,
            "custo_estimado": 100.0,
            "assumption": {"estado": "ILUSTRATIVO", "valor": 35},
            "hours": {"horas": 10},
            "linguagem": "Premissa ilustrativa.",
        },
        "charts": [
            {
                "id": "setores",
                "categories": ["GRUPO_SUPRIMIDO"],
                "series": [{"name": "dias", "data": [4.0]}],
            },
            {
                "id": "pareto_cid",
                "categories": ["?"],
                "series": [{"name": "eventos", "data": [4.0]}],
            },
        ],
        "first_experience": {
            "decision": {
                "title": "Revisão ergonômica no setor Operacional",
                "priority": "alta",
                "description": "Concentração persistente.",
                "expected_impact": "redução setorial",
                "deadline": "Próximo ciclo",
            },
            "kpis": [],
        },
        "impacto_economico_biomed": {},
    }
    dx = compose_decision_experience(payload)
    blob = str(dx)
    assert "GRUPO_SUPRIMIDO" not in blob
    assert "Operacional" in dx["six_answers"]["problem"]
    assert dx["evidence"]["charts"][0]["categories"] == ["Grupo agregado (privacidade)"]


def test_recommendations_capped_at_three():
    payload = {
        "hero": {"confianca": "moderada"},
        "intelligence": {
            "plano_acao": [
                {"title": f"Ação {i}", "priority": "alta", "category": "ergonomia"}
                for i in range(6)
            ]
        },
        "custo": {"calculavel": False, "assumption": {"estado": "NAO_INFORMADO"}, "hours": {}},
        "charts": [],
        "first_experience": {"decision": {"title": "Ação 0", "priority": "alta"}, "kpis": []},
        "impacto_economico_biomed": {},
    }
    dx = compose_decision_experience(payload)
    assert len(dx["recommendations"]) == 3


def test_decision_experience_static_no_modal():
    html = (FRONTEND / "executive.html").read_text(encoding="utf-8")
    assert "bm-decision-experience" in html
    assert "decision-experience.js" in html
    assert "bm-decision-modal" not in html
    assert (FRONTEND / "static" / "js" / "executive" / "decision-experience.js").exists()
    css = (FRONTEND / "static" / "css" / "biomed-executive.css").read_text(encoding="utf-8")
    assert "bm-dx-hero-dec" in css
    assert "bm-dx-road" in css


def test_no_commercial_cta_in_experience(db_session, monkeypatch):
    monkeypatch.setenv("EXECUTIVE_STAGING_DEMO", "true")
    monkeypatch.setenv("EXECUTIVE_ILLUSTRATIVE_HOURLY_COST", "35")
    payload = ExecutiveAggregateService(db_session).build_command_center(
        client_id=2, periodo_inicio="2026-01", periodo_fim="2026-03"
    )
    blob = str(payload["decision_experience"]).lower()
    for banned in ("compre agora", "fale conosco", "solicite uma proposta", "upsell"):
        assert banned not in blob


@pytest.fixture()
def exec_app(db_session, monkeypatch):
    monkeypatch.setenv("ENABLE_EXECUTIVE_UI", "true")
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

    def _override():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override
    yield app
    app.dependency_overrides.pop(get_db, None)


def test_api_decision_experience(exec_app):
    token = create_access_token(data={"sub": "exec_user"})
    client = TestClient(exec_app)
    r = client.get(
        "/api/executive/command-center",
        params={"periodo_inicio": "2026-01", "periodo_fim": "2026-03", "client_id": 2},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    dx = r.json()["decision_experience"]
    assert dx["six_answers"]["first_step"]
    assert_no_pii_in_payload(dx)
