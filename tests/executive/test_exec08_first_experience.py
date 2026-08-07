"""EXEC-08 — First CEO experience: contract, privacy, static UI."""
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
os.environ.setdefault("SECRET_KEY", "exec08-test-secret-not-for-production")
os.environ.setdefault("ENABLE_INTELLIGENT_INGESTION", "false")
os.environ.setdefault("ENABLE_BIOMED_PERFORMANCE_ENGINE", "false")
os.environ.setdefault("EXECUTIVE_STAGING_DEMO", "false")

from backend.auth import create_access_token, get_password_hash
from backend.database import Base, get_db
from backend.executive.aggregate_service import ExecutiveAggregateService
from backend.executive.first_experience import compose_first_experience
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
            dias_atestados=3,
            dias_perdidos=3,
            horas_perdi=24,
            horas_perdidas=24,
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


def test_first_experience_contract(db_session, monkeypatch):
    monkeypatch.setenv("EXECUTIVE_STAGING_DEMO", "true")
    monkeypatch.setenv("EXECUTIVE_ILLUSTRATIVE_HOURLY_COST", "35")
    payload = ExecutiveAggregateService(db_session).build_command_center(
        client_id=2,
        periodo_inicio="2026-01",
        periodo_fim="2026-03",
    )
    assert "first_experience" in payload
    fx = payload["first_experience"]
    assert_no_pii_in_payload(fx)
    assert fx["hero"]["company"]
    assert fx["hero"]["competencia"]
    assert "opening_phrase" in fx["hero"]
    assert "confidence" in fx["hero"]
    assert "operational_status" in fx["hero"]
    assert "updated_at" in fx["hero"]
    assert len(fx["summary"]) <= 3
    assert len(fx["summary"]) >= 1
    assert len(fx["kpis"]) == 4
    assert [k["id"] for k in fx["kpis"]] == ["horas", "dias", "custo", "score"]
    assert fx["decision"]["title"]
    assert fx["decision"]["cta"] == "Entender esta decisão"
    assert fx["privacy"]["pii_excluded"] is True


def test_compose_first_experience_limits():
    payload = {
        "hero": {
            "empresa": "Beta",
            "periodo": "2026-01 → 2026-03",
            "status": "comparavel",
            "tendencia": "melhora",
            "confianca": "moderada",
            "mensagem": "Estado estável com concentração setorial.",
            "score": {"available": True, "score": 72.5, "label": "Executive Score"},
        },
        "periodo": {"atual": {"inicio": "2026-01", "fim": "2026-03"}},
        "client": {"label": "Beta"},
        "kpis": [
            {"id": "dias", "value": 10, "available": True},
            {"id": "horas", "value": 80, "available": True},
        ],
        "custo": {"calculavel": True, "custo_estimado": 2800, "assumption": {"estado": "ILUSTRATIVO"}},
        "intelligence": {
            "confianca": "moderada",
            "mensagem_executiva": "Estado estável com concentração setorial.",
            "onde_esta_o_risco": ["Setor Operacional concentra o impacto."],
            "o_que_recomendamos": ["Revisão ergonômica no setor Operacional"],
            "plano_acao": [
                {
                    "title": "Revisão ergonômica no setor Operacional",
                    "priority": "alta",
                    "justification": "Concentração setorial persistente.",
                    "meta": "Reduzir concentração setorial",
                    "deadline": "30 dias",
                }
            ],
        },
        "charts": [{"id": "setores", "categories": ["Operacional"]}],
        "qualidade": {"iqb": 80},
    }
    fx = compose_first_experience(payload)
    assert len(fx["summary"]) == 3
    assert fx["kpis"][2]["available"] is True
    assert fx["decision"]["priority"] == "alta"
    blob = str(fx).lower()
    assert "algoritmo" not in blob
    assert "llm" not in blob


def test_first_experience_static_assets():
    html = (FRONTEND / "executive.html").read_text(encoding="utf-8")
    assert "bm-first-experience" in html
    assert "first-experience.js" in html
    assert "app-first.js" in html
    # EXEC-09 replaces modal with full Decision Experience view
    assert "bm-decision-experience" in html
    assert "bm-decision-modal" not in html
    assert "chart-temporal" not in html
    assert "Executive Analytics" not in html
    assert (FRONTEND / "static" / "js" / "executive" / "first-experience.js").exists()
    assert (FRONTEND / "static" / "js" / "executive" / "app-first.js").exists()
    css = (FRONTEND / "static" / "css" / "biomed-executive.css").read_text(encoding="utf-8")
    assert "bm-fx-hero" in css
    assert "bm-fx-decision" in css


def test_summary_max_three_phrases(db_session, monkeypatch):
    monkeypatch.setenv("EXECUTIVE_STAGING_DEMO", "true")
    payload = ExecutiveAggregateService(db_session).build_command_center(
        client_id=2, periodo_inicio="2026-01", periodo_fim="2026-03"
    )
    assert len(payload["first_experience"]["summary"]) <= 3


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


def test_api_includes_first_experience(exec_app):
    token = create_access_token(data={"sub": "exec_user"})
    client = TestClient(exec_app)
    r = client.get(
        "/api/executive/command-center",
        params={"periodo_inicio": "2026-01", "periodo_fim": "2026-03", "client_id": 2},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    body = r.json()
    fx = body["first_experience"]
    assert fx["hero"]["company"]
    assert len(fx["kpis"]) == 4
    assert_no_pii_in_payload(fx)
