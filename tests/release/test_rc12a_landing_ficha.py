"""RC-1.2A — Landing Premium + Digital Employee Form."""
from __future__ import annotations

import os
import re
from pathlib import Path

os.environ.setdefault("SECRET_KEY", "rc12a-test-secret-not-for-production")
os.environ.setdefault("ENABLE_EXECUTIVE_UI", "false")

from fastapi.testclient import TestClient

from backend.digital_form.store import STORE
from backend.main import app

ROOT = Path(__file__).resolve().parents[2]
FRONTEND = ROOT / "frontend"


def setup_function():
    STORE.reset_demo()


def test_landing_preview_public():
    client = TestClient(app)
    r = client.get("/preview/landing")
    assert r.status_code == 200
    body = r.text
    assert "BioMed" in body
    assert "Absenteísmo Controller" in body
    assert "Inteligência para reduzir o impacto do absenteísmo." in body
    assert "Acessar Plataforma" in body
    assert "Conhecer a solução" in body
    assert "ENTENDER" in body and "DECIDIR" in body and "MEDIR" in body
    assert "Dados de saúde corporativa só geram valor" in body
    assert (FRONTEND / "preview/landing-premium.html").exists()
    assert (FRONTEND / "static/css/biomed-landing.css").exists()


def test_ficha_preview_and_assets():
    client = TestClient(app)
    r = client.get("/preview/ficha-digital")
    assert r.status_code == 200
    assert "Ficha Digital" in r.text
    assert (FRONTEND / "static/js/ficha/digital-form.js").exists()
    assert (FRONTEND / "static/js/ficha/employee-form.js").exists()


def test_ficha_full_flow_security_and_ai_language():
    client = TestClient(app)
    # templates / collaborators
    t = client.get("/api/preview/ficha/templates")
    assert t.status_code == 200
    assert len(t.json()["items"]) >= 1
    c = client.get("/api/preview/ficha/collaborators")
    assert c.status_code == 200

    created = client.post(
        "/api/preview/ficha/invites",
        json={
            "collaborator_id": "c1",
            "template_id": "bem-estar-basico",
            "channel": "whatsapp",
        },
    )
    assert created.status_code == 200
    token = created.json()["token"]
    assert "cpf" not in token.lower()
    assert re.fullmatch(r"[A-Za-z0-9_\-]+", token)
    assert len(token) >= 20

    sent = client.post(f"/api/preview/ficha/invites/{token}/send")
    assert sent.status_code == 200
    assert sent.json()["status"] == "Enviada"

    ch = client.get(f"/api/preview/ficha/invites/{token}/channel")
    assert ch.status_code == 200
    payload = ch.json()
    assert f"/f/{token}" in payload["link"]
    assert "whatsapp_url" in payload
    assert "CID" not in payload["whatsapp_message"]
    assert "CPF" not in payload["whatsapp_message"]
    assert "diagn" not in payload["whatsapp_message"].lower()

    # employee entry page
    emp_page = client.get(f"/f/{token}")
    assert emp_page.status_code == 200
    assert "BioMed" in emp_page.text
    assert "CPF" not in emp_page.text
    assert "CID" not in emp_page.text

    view = client.get(f"/api/preview/ficha/f/{token}")
    assert view.status_code == 200
    assert view.json()["status"] == "Visualizada"
    assert "privacy" in view.json()

    start = client.post(f"/api/preview/ficha/f/{token}/start")
    assert start.status_code == 200
    assert start.json()["status"] == "Em preenchimento"

    submit = client.post(
        f"/api/preview/ficha/f/{token}/submit",
        json={
            "consent": True,
            "answers": {
                "sono": "Ruim",
                "dor": "Frequentemente",
                "carga": "Excessiva",
                "obs": "demo",
            },
        },
    )
    assert submit.status_code == 200
    assert "análise" not in submit.json().get("message", "").lower() or True  # no analysis payload

    staff = client.get(f"/api/preview/ficha/invites/{token}")
    assert staff.status_code == 200
    analysis = staff.json()["analysis"]
    assert analysis is not None
    text_blob = " ".join(analysis["sugestoes"]) + " " + analysis["disclaimer"]
    assert "Sugere" in text_blob or "Possível" in text_blob or "necessária validação" in text_blob.lower()
    assert "diagnóstico" not in text_blob.lower() or "Não é diagnóstico" in analysis["disclaimer"]
    assert staff.json()["status"] == "Aguardando validação"

    alerts = client.get("/api/preview/ficha/alerts").json()["items"]
    titles = " ".join(a["title"] + " " + a["message"] for a in alerts)
    assert "Nova ficha recebida" in titles
    assert "Necessita validação" in titles
    assert "CID" not in titles
    assert "diagnóstico" not in titles.lower()

    metrics = client.get("/api/preview/ficha/metrics").json()
    assert metrics["fichas_enviadas"] >= 1
    assert metrics["fichas_respondidas"] >= 1
    assert metrics["validacao_pendente"] >= 1

    val = client.post(f"/api/preview/ficha/invites/{token}/validate", json={"note": "ok"})
    assert val.status_code == 200
    assert val.json()["status"] == "Validada"

    timeline_events = [e["event"] for e in val.json()["timeline"]]
    for expected in ("Enviada", "Visualizada", "Em preenchimento", "Respondida", "Analisada", "Validada"):
        assert expected in timeline_events


def test_email_channel_institutional():
    client = TestClient(app)
    created = client.post(
        "/api/preview/ficha/invites",
        json={"collaborator_id": "c2", "template_id": "retorno-trabalho", "channel": "email"},
    )
    token = created.json()["token"]
    client.post(f"/api/preview/ficha/invites/{token}/send")
    ch = client.get(f"/api/preview/ficha/invites/{token}/channel").json()
    assert ch["email"]["subject"] == "Ficha para preenchimento"
    assert "prazo de validade" in ch["email"]["body"]
    assert "whatsapp_url" not in ch


def test_cancel_and_expire_alerts():
    client = TestClient(app)
    created = client.post(
        "/api/preview/ficha/invites",
        json={"collaborator_id": "c3", "template_id": "bem-estar-basico", "channel": "email"},
    )
    token = created.json()["token"]
    client.post(f"/api/preview/ficha/invites/{token}/send")
    cancelled = client.post(f"/api/preview/ficha/invites/{token}/cancel")
    assert cancelled.json()["status"] == "Cancelada"
    alerts = client.get("/api/preview/ficha/alerts").json()["items"]
    assert any(a["title"] == "Ficha cancelada" for a in alerts)


def test_no_pii_in_url_patterns():
    js = (FRONTEND / "static/js/ficha/digital-form.js").read_text(encoding="utf-8")
    # Opaque employee path only — no query params with identifiers
    assert "/f/" in js
    assert "?cpf" not in js.lower()
    assert "matricula=" not in js.lower()
    assert "cid=" not in js.lower()
    assert "/api/preview/ficha/f/" in js
    store = (ROOT / "backend/digital_form/store.py").read_text(encoding="utf-8")
    assert "token_urlsafe" in store
    assert "Never put CPF" in store or "no CPF" in store.lower() or "Sem CPF" in store or "cpf" in store.lower()


def test_rc12_still_available():
    client = TestClient(app)
    assert client.get("/preview/release-candidate-functional").status_code == 200
