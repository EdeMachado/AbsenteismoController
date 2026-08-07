"""RC-21 Final Product — one BioMed Platform experience (no new features)."""
from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("SECRET_KEY", "rc21-final-test-secret-not-for-production")

from fastapi.testclient import TestClient

from backend.executive import is_executive_presentation_enabled
from backend.main import app
from backend.preview_gate import is_preview_homologation_path

ROOT = Path(__file__).resolve().parents[2]
FRONTEND = ROOT / "frontend"


def test_landing_login_home_shell_ready():
    client = TestClient(app)
    assert client.get("/landing").status_code == 200
    assert "biomed-landing.css" in client.get("/landing").text
    assert "Entrar" in client.get("/landing").text
    login = client.get("/login").text
    assert "BioMed" in login and "biomed-login.css" in login
    assert "AbsenteismoController" not in login
    home = client.get("/").text
    assert "BioMed Platform" in home
    assert 'data-bm-shell="hub"' in home
    assert "biomed-platform-shell.js" in home
    # RC25 home: entry experience (not legacy hub copy)
    assert "Olá" in home or "bc-hello" in home
    assert "Executive" in home and "Analytics" in home


def test_analytics_organizer_reuses_legacy_surfaces():
    client = TestClient(app)
    # RC25: /analytics redirects to core dashboard; /analises may still be organizer file
    r = client.get("/analytics", follow_redirects=False)
    assert r.status_code in (302, 307)
    assert r.headers.get("location") == "/dashboard"
    dash = client.get("/dashboard")
    assert dash.status_code == 200
    assert "Analytics" in dash.text
    assert "em desenvolvimento" not in dash.text.lower()
    analises = client.get("/analises")
    assert analises.status_code == 200


def test_tendencias_redirects_to_dashboard_charts():
    client = TestClient(app)
    r = client.get("/tendencias", follow_redirects=False)
    assert r.status_code in (302, 307)
    assert "/dashboard" in r.headers.get("location", "")


def test_definitive_menu_in_shell():
    js = (FRONTEND / "static/js/biomed-platform-shell.js").read_text(encoding="utf-8")
    for label in (
        "Início",
        "Executive",
        "Analytics",
        "Operação",
        "Apresentações",
        "Configurações",
        "Fichas",
        "Visão Geral",
        "Comparativos",
        "Power BI",
        "Produtividade",
        "Setores",
        "CID",
        "Tendências",
        "Empresas",
        "Funcionários",
        "Uploads",
        "Upload inteligente",
    ):
        assert label in js, label
    assert "disabled: true" in js
    assert "bm-plat-top" in js
    assert "bm-plat-crumb" in js
    assert "bm-plat-foot" in js
    assert 'link("/analises"' not in js


def test_operations_pages_in_shell():
    for name in (
        "clientes.html",
        "funcionarios.html",
        "perfil_funcionario.html",
        "upload.html",
        "upload_inteligente.html",
        "configuracoes.html",
        "index-legacy.html",
        "comparativos.html",
        "produtividade.html",
        "dados_powerbi.html",
        "dashboard_powerbi.html",
        "apresentacao.html",
        "auto_processor.html",
    ):
        html = (FRONTEND / name).read_text(encoding="utf-8")
        assert "biomed-platform-shell.js" in html, name
        assert 'data-bm-shell="legacy"' in html, name


def test_public_brand_is_biomed_not_absenteismo():
    for name in ("landing.html", "login.html", "index.html", "analytics.html", "executive.html"):
        html = (FRONTEND / name).read_text(encoding="utf-8")
        assert "AbsenteismoController" not in html, name
        assert "BioMed" in html, name
    # legacy landing preserved in git only
    assert (FRONTEND / "landing-legacy.html").is_file()


def test_presentation_and_ficha_remain_off(monkeypatch):
    assert is_executive_presentation_enabled() is False
    client = TestClient(app)
    assert client.get("/executive/presentation").status_code == 404
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.delenv("ENABLE_PREVIEW_SURFACES", raising=False)
    from backend.preview_gate import preview_surfaces_enabled

    assert preview_surfaces_enabled() is False
    assert is_preview_homologation_path("/preview/ficha-digital") is True
    assert client.get("/preview/ficha-digital").status_code == 404
    assert client.get("/f/demo").status_code == 404


def test_v22_backlog_doc_exists():
    doc = (ROOT / "docs/release/RC21_V22_BACKLOG.md").read_text(encoding="utf-8")
    for item in (
        "Presentation Premium",
        "Ficha Digital",
        "Performance Engine",
        "Intelligent Ingestion",
        "IA Clínica",
    ):
        assert item in doc


def test_flags_unchanged_defaults():
    assert os.environ.get("ENABLE_EXECUTIVE_PRESENTATION", "false").lower() in {
        "false",
        "0",
        "off",
        "",
    }
    assert os.environ.get("ENABLE_INTELLIGENT_INGESTION", "false").lower() in {
        "false",
        "0",
        "off",
        "",
    }
    assert os.environ.get("ENABLE_BIOMED_PERFORMANCE_ENGINE", "false").lower() in {
        "false",
        "0",
        "off",
        "",
    }
