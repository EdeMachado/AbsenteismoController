"""RC-22 — Final BioMed Platform consolidation (one shell, one brand, no stubs in menu)."""
from __future__ import annotations

import os
import re
from pathlib import Path

os.environ.setdefault("SECRET_KEY", "rc22-consolidation-secret-not-for-production")

from fastapi.testclient import TestClient

from backend.executive import is_executive_presentation_enabled
from backend.main import app
from backend.preview_gate import is_preview_homologation_path

ROOT = Path(__file__).resolve().parents[2]
FRONTEND = ROOT / "frontend"
SHELL_JS = (FRONTEND / "static/js/biomed-platform-shell.js").read_text(encoding="utf-8")
SHELL_CSS = (FRONTEND / "static/css/biomed-platform.css").read_text(encoding="utf-8")

ACTIVE_LEGACY_PAGES = (
    "index-legacy.html",
    "clientes.html",
    "funcionarios.html",
    "perfil_funcionario.html",
    "upload.html",
    "upload_inteligente.html",
    "produtividade.html",
    "comparativos.html",
    "dados_powerbi.html",
    "dashboard_powerbi.html",
    "apresentacao.html",
    "configuracoes.html",
)

NATIVE_PAGES = (
    "landing.html",
    "login.html",
    "index.html",
    "analytics.html",
    "executive.html",
)


def test_inventory_doc_exists():
    doc = (ROOT / "docs/release/RC22_ROUTE_INVENTORY.md").read_text(encoding="utf-8")
    for route in (
        "/landing",
        "/login",
        "/",
        "/dashboard",
        "/executive",
        "/analytics",
        "/clientes",
        "/apresentacao",
    ):
        assert route in doc
    assert "NEW_NATIVE" in doc
    assert "LEGACY_CONTENT_IN_NEW_SHELL" in doc


def test_shell_is_single_and_rc22():
    assert 'var CACHE = "rc22"' in SHELL_JS or 'var CACHE = "rc23"' in SHELL_JS
    assert "bm-plat-nav" in SHELL_JS
    assert "bm-plat-logout" in SHELL_JS
    # No parallel legacy menu builders in shell
    assert "sidebar-nav" not in SHELL_JS
    assert 'link("/analises"' not in SHELL_JS
    assert 'link("/tendencias.html"' not in SHELL_JS
    assert 'link("/inss"' not in SHELL_JS
    assert 'link("/download_app"' not in SHELL_JS
    assert "disabled: true" in SHELL_JS  # Fichas stay off


def test_menu_has_real_analytics_targets_only():
    for href in (
        "/dashboard",
        "/comparativos",
        "/dados_powerbi",
        "/produtividade",
        "/dashboard#graficosConverplast",
        "/dashboard#chartCids",
        "/dashboard#chartEvolucao",
    ):
        assert href in SHELL_JS, href
    # stubs / orphan filenames must not be menu targets
    for bad in ("analises.html", "tendencias.html", "inss.html", "download_app.html", "baixar_icone.html"):
        assert bad not in SHELL_JS


def test_legacy_chrome_hidden_by_css():
    assert "header-user-widget" in SHELL_CSS
    assert "aside.sidebar" in SHELL_CSS
    assert "display: none !important" in SHELL_CSS
    # RC22 content isolation markers
    assert "RC-22" in SHELL_CSS or "RC22" in SHELL_CSS or "Final platform consolidation" in SHELL_CSS
    assert "apresentacao-container" in SHELL_CSS
    assert "clientes-hero" in SHELL_CSS
    # Power BI filter panels preserved
    assert ".sidebar-left" in SHELL_CSS
    assert "display: block !important" in SHELL_CSS


def test_active_pages_use_platform_shell():
    for name in ACTIVE_LEGACY_PAGES:
        html = (FRONTEND / name).read_text(encoding="utf-8")
        assert 'data-bm-shell="legacy"' in html, name
        assert "biomed-platform-shell.js" in html, name
        assert "biomed-platform.css" in html, name
        assert "AbsenteismoController" not in html, name


def test_native_pages_branded_biomed_platform():
    for name in NATIVE_PAGES:
        html = (FRONTEND / name).read_text(encoding="utf-8")
        assert "BioMed" in html, name
        assert "AbsenteismoController" not in html, name
        assert "PR preview" not in html.lower(), name


def test_landing_login_home_consolidated():
    client = TestClient(app)
    landing = client.get("/landing").text
    assert client.get("/landing").status_code == 200
    assert "BioMed Platform" in landing
    assert "AbsenteismoController" not in landing
    assert "biomed-landing.css" in landing

    login = client.get("/login").text
    assert "BioMed" in login
    assert "biomed-login.css" in login
    assert "AbsenteismoController" not in login

    home = client.get("/").text
    assert 'data-bm-shell="hub"' in home
    assert "BioMed Platform" in home
    assert 'href="/executive"' in home
    assert 'href="/analytics"' in home


def test_executive_integrated_same_shell():
    html = (FRONTEND / "executive.html").read_text(encoding="utf-8")
    assert 'data-bm-shell="hub"' in html
    assert "biomed-platform-shell.js" in html
    assert "bm-fx-steps" in html
    assert "bm-nav-ops" not in html
    assert "bm-nav--minimal" not in html


def test_analytics_real_and_dashboard_relabeled():
    client = TestClient(app)
    body = client.get("/analytics").text
    assert "Visão Geral" in body
    assert 'href="/dashboard"' in body
    assert "em desenvolvimento" not in body.lower()

    dash = (FRONTEND / "index-legacy.html").read_text(encoding="utf-8")
    assert "Analytics · Visão Geral" in dash
    assert 'data-bm-shell="legacy"' in dash


def test_presentation_encapsulated_not_premium():
    html = (FRONTEND / "apresentacao.html").read_text(encoding="utf-8")
    assert 'data-bm-shell="legacy"' in html
    assert "biomed-platform-shell.js" in html
    assert "Apresentações · BioMed Platform" in html
    assert is_executive_presentation_enabled() is False
    client = TestClient(app)
    assert client.get("/executive/presentation").status_code == 404


def test_operations_routes_alive():
    client = TestClient(app)
    for path in (
        "/clientes",
        "/funcionarios",
        "/upload",
        "/upload_inteligente",
        "/configuracoes",
        "/comparativos",
        "/produtividade",
        "/dados_powerbi",
        "/dashboard_powerbi",
        "/apresentacao",
        "/dashboard",
    ):
        r = client.get(path)
        assert r.status_code == 200, path
        assert "biomed-platform" in r.text.lower() or "bm-plat" in r.text.lower() or "data-bm-shell" in r.text


def test_flags_and_preview_remain_off(monkeypatch):
    assert is_executive_presentation_enabled() is False
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.delenv("ENABLE_PREVIEW_SURFACES", raising=False)
    from backend.preview_gate import preview_surfaces_enabled

    assert preview_surfaces_enabled() is False
    assert is_preview_homologation_path("/preview/ficha-digital") is True
    client = TestClient(app)
    assert client.get("/preview/ficha-digital").status_code == 404
    assert client.get("/f/demo").status_code == 404


def test_auth_skips_duplicate_chrome():
    auth = (FRONTEND / "static/js/auth.js").read_text(encoding="utf-8")
    assert 'getAttribute("data-bm-shell")' in auth


def test_no_db_migration_in_rc22_scope():
    # Guardrail: this RC must not introduce alembic/sql migrations as part of consolidation.
    # Presence of historical migrations is fine; new RC22-named migration files are not.
    mig = list((ROOT / "backend").rglob("*rc22*")) + list((ROOT / "migrations").rglob("*rc22*")) if (ROOT / "migrations").exists() else list((ROOT / "backend").rglob("*rc22*"))
    assert not any("migrat" in str(p).lower() for p in mig)


def test_tendencias_still_redirects():
    client = TestClient(app)
    r = client.get("/tendencias", follow_redirects=False)
    assert r.status_code in (302, 307)
    assert "/dashboard" in r.headers.get("location", "")
