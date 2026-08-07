"""RC-23 — Product experience rebuild (auth flow + visual layer). No API/DB changes."""
from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("SECRET_KEY", "rc23-experience-secret-not-for-production")

from fastapi.testclient import TestClient

from backend.main import app

ROOT = Path(__file__).resolve().parents[2]
FRONTEND = ROOT / "frontend"


def test_login_never_auto_resumes_session_or_company():
    html = (FRONTEND / "login.html").read_text(encoding="utf-8")
    assert "clearCompanySelection" in html
    assert 'return "/clientes"' in html
    assert 'localStorage.getItem("cliente_selecionado")) return "/"' not in html
    assert 'if (localStorage.getItem("access_token"))' not in html
    assert "Do not auto-resume sessions" in html


def test_logout_clears_company_context():
    auth = (FRONTEND / "static/js/auth.js").read_text(encoding="utf-8")
    assert "cliente_selecionado" in auth
    assert "clear company context" in auth.lower() or "cliente_selecionado_nome" in auth
    shell = (FRONTEND / "static/js/biomed-platform-shell.js").read_text(encoding="utf-8")
    assert 'localStorage.removeItem("cliente_selecionado")' in shell


def test_experience_layer_wired():
    css = FRONTEND / "static/css/biomed-experience.css"
    assert css.is_file()
    text = css.read_text(encoding="utf-8")
    assert "RC-23" in text or "Product Experience" in text
    assert "apresentacao-container" in text
    assert "charts-grid" in text or "graficosConverplast" in text
    shell = (FRONTEND / "static/js/biomed-platform-shell.js").read_text(encoding="utf-8")
    assert 'CACHE = "rc23"' in shell or 'CACHE = "rc23a"' in shell
    assert "biomed-experience.css" in shell


def test_active_pages_load_experience_css():
    for name in (
        "index-legacy.html",
        "apresentacao.html",
        "clientes.html",
        "funcionarios.html",
        "upload.html",
        "upload_inteligente.html",
        "produtividade.html",
        "comparativos.html",
        "dados_powerbi.html",
        "configuracoes.html",
        "analytics.html",
        "index.html",
    ):
        html = (FRONTEND / name).read_text(encoding="utf-8")
        assert "biomed-experience.css" in html or name in ("analytics.html", "index.html"), name
        # hub pages get CSS via shell ensureStyles; still ok if linked
        if name not in ("analytics.html", "index.html", "executive.html"):
            assert "biomed-experience.css" in html, name


def test_apresentacao_not_full_viewport_indigo_legacy():
    html = (FRONTEND / "apresentacao.html").read_text(encoding="utf-8")
    assert "RC-23" in html
    assert "background: #1a237e" not in html
    assert "100vw" not in html or "calc(100vh - 180px)" in html
    assert "#0f2a3d" in html or "biomed-experience.css" in html


def test_dashboard_bi_premium_spacing_markers():
    html = (FRONTEND / "index-legacy.html").read_text(encoding="utf-8")
    assert "biomed-experience.css" in html
    assert "Analytics · Visão Geral" in html
    assert "height: 340px" in html


def test_landing_login_public_routes():
    client = TestClient(app)
    landing = client.get("/landing")
    login = client.get("/login")
    assert landing.status_code == 200
    assert login.status_code == 200
    assert "BioMed Platform" in landing.text
    assert "/login" in landing.text
    assert "Entrar" in landing.text
    # Landing must not embed auto-auth redirect to company
    assert "cliente_selecionado" not in landing.text
    assert "access_token" not in landing.text


def test_flags_and_apis_untouched_defaults():
    assert os.environ.get("ENABLE_EXECUTIVE_PRESENTATION", "false").lower() in {"false", "0", "off", ""}
    assert os.environ.get("ENABLE_INTELLIGENT_INGESTION", "false").lower() in {"false", "0", "off", ""}


def test_audit_doc_exists():
    doc = ROOT / "docs/release/RC23_PRODUCT_EXPERIENCE.md"
    assert doc.is_file()
    text = doc.read_text(encoding="utf-8")
    assert "LOGIN_SECURITY_FIXED" in text or "Landing" in text
