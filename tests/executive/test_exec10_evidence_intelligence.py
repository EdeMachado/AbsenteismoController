"""EXEC-10 — Evidence Intelligence contract, privacy, static UI."""
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
os.environ.setdefault("SECRET_KEY", "exec10-test-secret-not-for-production")
os.environ.setdefault("ENABLE_INTELLIGENT_INGESTION", "false")
os.environ.setdefault("ENABLE_BIOMED_PERFORMANCE_ENGINE", "false")
os.environ.setdefault("EXECUTIVE_STAGING_DEMO", "false")

from backend.auth import create_access_token, get_password_hash
from backend.database import Base, get_db
from backend.executive.aggregate_service import ExecutiveAggregateService
from backend.executive.evidence_intelligence import compose_evidence_intelligence
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


def test_evidence_intelligence_eight_blocks(db_session, monkeypatch):
    monkeypatch.setenv("EXECUTIVE_STAGING_DEMO", "true")
    monkeypatch.setenv("EXECUTIVE_ILLUSTRATIVE_HOURLY_COST", "35")
    payload = ExecutiveAggregateService(db_session).build_command_center(
        client_id=2, periodo_inicio="2026-01", periodo_fim="2026-03"
    )
    ei = payload["evidence_intelligence"]
    assert_no_pii_in_payload(ei)
    assert ei["engine"] == "exec10-evidence-intelligence-v1"
    assert ei["header"]["title"]
    assert 1 <= len(ei["summary"]) <= 3
    assert ei["sources"]
    assert "timeline" in ei
    assert ei["quality"]["label"]
    assert ei["confidence"]["level"] in {"Alta", "Média", "Baixa"}
    assert ei["confidence"]["reason"]
    assert ei["limitations"]
    assert ei["still_need"]
    assert 1 <= len(ei["conclusion"]) <= 3
    assert "GRUPO_SUPRIMIDO" not in str(ei)


def test_evidence_intelligence_no_commercial_cta():
    payload = {
        "hero": {"mensagem": "Estado.", "confianca": "alta", "tendencia": "melhora"},
        "intelligence": {"confianca": "alta", "limitacoes": ["Sem causalidade exclusiva."]},
        "qualidade": {
            "iqb": 82,
            "classificacao": "Alta",
            "comparabilidade": "integral",
            "cobertura_horas": "registrada",
            "dimensoes": {},
            "limitations": ["IQB via DataQualityService."],
        },
        "periodo": {"comparabilidade": "integral"},
        "custo": {"assumption": {"estado": "REAL"}},
        "charts": [
            {
                "id": "evolucao_temporal",
                "categories": ["2026-01", "2026-02"],
                "series": [{"data": [5, 3]}],
            }
        ],
        "methodology": {
            "metrics": "MetricService",
            "quality": "DataQualityService",
            "cost": "AbsenteeismCostModel",
            "intelligence": "rule_engine_deterministic_v1",
        },
        "decision_experience": {
            "header": {"title": "Ação prioritária"},
            "six_answers": {"problem": "Concentração setorial."},
            "confidence": {"level": "Alta", "reason": "Série estável."},
        },
        "privacy": {"pii_excluded": True},
        "limitations": [],
    }
    ei = compose_evidence_intelligence(payload)
    blob = str(ei).lower()
    for banned in (
        "compre agora",
        "fale conosco",
        "solicite uma proposta",
        "upsell",
        "contratar",
        "consultoria",
        "agende uma demo",
    ):
        assert banned not in blob
    assert "cta_buy" not in ei
    assert "footer_note" not in ei or "ORBIT" not in str(ei.get("footer_note") or "")


def test_evidence_intelligence_static_assets():
    html = (FRONTEND / "executive.html").read_text(encoding="utf-8")
    assert "bm-evidence-intelligence" in html
    assert "evidence-intelligence.js" in html
    assert "bm-nav-evidence" in html
    assert (FRONTEND / "static" / "js" / "executive" / "evidence-intelligence.js").exists()
    css = (FRONTEND / "static" / "css" / "biomed-executive.css").read_text(encoding="utf-8")
    assert "bm-ei-hero" in css
    assert "bm-ei-quality" in css
    js = (FRONTEND / "static" / "js" / "executive" / "decision-experience.js").read_text(
        encoding="utf-8"
    )
    assert "bm-dx-evidence" in js
    assert "Como sabemos disso?" in js


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


def test_api_evidence_intelligence(exec_app):
    token = create_access_token(data={"sub": "exec_user"})
    client = TestClient(exec_app)
    r = client.get(
        "/api/executive/command-center",
        params={"periodo_inicio": "2026-01", "periodo_fim": "2026-03", "client_id": 2},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    ei = r.json()["evidence_intelligence"]
    assert ei["conclusion"]
    assert_no_pii_in_payload(ei)
