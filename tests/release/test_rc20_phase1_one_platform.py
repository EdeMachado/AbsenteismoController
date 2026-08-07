"""RC-20 Phase 1 — Landing + Login + Unified Shell (BioMed One Platform)."""
from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("SECRET_KEY", "rc20-phase1-test-secret-not-for-production")

from fastapi.testclient import TestClient

from backend.executive import is_executive_presentation_enabled
from backend.main import app
from backend.preview_gate import is_preview_homologation_path

ROOT = Path(__file__).resolve().parents[2]
FRONTEND = ROOT / "frontend"


def test_landing_serves_premium_production_safe():
    client = TestClient(app)
    r = client.get("/landing")
    assert r.status_code == 200
    body = r.text
    assert "biomed-landing.css" in body
    assert "rc20p1" in body or "rc21" in body or "rc22" in body or "rc23" in body or "rc24" in body
    assert "bm-lp-body" in body
    assert "BioMed" in body
    assert "Entrar" in body
    assert "Contato comercial" in body
    assert "abrirModalContato" in body
    assert "/api/cadastro-empresa" not in body
    assert "landing-premium" not in body
    assert "homolog" not in body.lower()
    assert "PREVIEW_ONLY" not in body
    assert (FRONTEND / "landing-legacy.html").is_file()
    legacy = (FRONTEND / "landing-legacy.html").read_text(encoding="utf-8")
    assert "btn-primary-landing" in legacy or "modal-cadastro" in legacy
    assert "bm-lp-body" not in legacy
    assert "btn-primary-landing" not in body


def test_login_biomed_identity_preserves_auth_and_safe_next():
    html = (FRONTEND / "login.html").read_text(encoding="utf-8")
    assert "biomed-login.css" in html
    assert "BioMed" in html
    assert "Inteligência em Saúde Corporativa" in html
    assert "AbsenteismoController" not in html
    assert "/api/auth/login" in html
    assert "access_token" in html
    assert "cliente_selecionado" in html
    assert "safeInternalNext" in html
    assert "postLoginDestination" in html
    assert html.count("function safeInternalNext") == 1
    assert 'n.startsWith("/")' in html
    assert 'n.startsWith("//")' in html
    assert 'n.includes("://")' in html

    client = TestClient(app)
    r = client.get("/login")
    assert r.status_code == 200
    assert "bm-login" in r.text
    assert "BioMed" in r.text


def test_home_is_biomed_hub_with_unified_shell():
    client = TestClient(app)
    r = client.get("/")
    assert r.status_code == 200
    body = r.text
    assert 'data-bm-shell="hub"' in body
    assert "biomed-platform.css" in body
    assert "biomed-platform-shell.js" in body
    assert "BioMed Platform" in body
    assert "Visão Executiva" in body or "Executive" in body
    assert 'href="/executive"' in body
    assert 'href="/dashboard"' in body or 'href="/analytics"' in body
    assert "rc21" in body or "rc20p1" in body or "rc22" in body or "rc23" in body or "rc24" in body
    assert "AbsenteismoController - GrupoBiomed" not in body
    assert 'href="/analises"' not in body


def test_legacy_dashboard_preserved_at_dashboard_route():
    client = TestClient(app)
    r = client.get("/dashboard")
    assert r.status_code == 200
    body = r.text
    assert "dashboard.js" in body
    assert "auth.js" in body
    assert "biomed-platform-shell.js" in body
    assert 'data-bm-shell="legacy"' in body
    assert (FRONTEND / "index-legacy.html").is_file()


def test_shell_menu_map_and_ficha_disabled():
    js = (FRONTEND / "static/js/biomed-platform-shell.js").read_text(encoding="utf-8")
    assert 'link("/executive"' in js
    assert "Visão Executiva" in js or "Executive" in js
    assert "Analytics" in js
    assert "Visão Geral" in js
    assert 'link("/dashboard"' in js
    assert 'link("/comparativos"' in js
    assert 'link("/dados_powerbi"' in js
    assert 'link("/produtividade"' in js
    assert "Operação" in js or "Operacional" in js
    assert "Clientes" in js
    assert 'link("/upload_inteligente"' in js
    assert "Apresentação" in js or "Apresentações" in js
    assert "Fichas" in js
    assert "disabled: true" in js
    assert 'link("/configuracoes"' in js
    assert 'link("/", "Início"' in js
    assert "Voltar ao sistema" not in js
    assert 'link("/analises"' not in js


def test_feature_inventory_doc_complete():
    doc = (ROOT / "docs/release/RC20_PHASE1_FEATURE_INVENTORY.md").read_text(encoding="utf-8")
    for marker in (
        "LEGACY_FEATURE_INVENTORY",
        "NEW_FEATURE_INVENTORY",
        "MISSING_IN_NEW",
        "DATA_SOURCE_MAP",
        "GRAPH_INVENTORY",
        "TARGET_MENU",
        "FEATURE_MIGRATION_MAP",
        "EXECUTIVE_KEEP",
        "ANALYTICS_MOVE",
        "OPERATIONS_MOVE",
        "INVENTORY_COMPLETE=yes",
    ):
        assert marker in doc


def test_operational_pages_include_shell():
    for name in (
        "clientes.html",
        "upload.html",
        "upload_inteligente.html",
        "funcionarios.html",
        "produtividade.html",
        "dados_powerbi.html",
        "dashboard_powerbi.html",
        "configuracoes.html",
        "apresentacao.html",
        "comparativos.html",
        "index-legacy.html",
        "perfil_funcionario.html",
        "auto_processor.html",
    ):
        html = (FRONTEND / name).read_text(encoding="utf-8")
        assert "biomed-platform.css" in html, name
        assert "biomed-platform-shell.js" in html, name
        assert 'data-bm-shell="legacy"' in html, name


def test_executive_integrated_in_one_platform_journey():
    html = (FRONTEND / "executive.html").read_text(encoding="utf-8")
    assert 'data-bm-shell="hub"' in html
    assert "biomed-platform-shell.js" in html
    assert "bm-nav-ops" not in html
    assert "Voltar ao sistema" not in html
    assert "Voltar ao operacional" not in html
    assert "bm-fx-steps" in html
    assert "rc21" in html or "rc22" in html or "rc23" in html or "rc24" in html
    assert "biomed-platform.css" in html


def test_preview_and_ficha_blocked_in_production(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.delenv("ENABLE_PREVIEW_SURFACES", raising=False)
    from backend.preview_gate import preview_surfaces_enabled

    assert preview_surfaces_enabled() is False
    assert is_preview_homologation_path("/preview/landing") is True
    assert is_preview_homologation_path("/f/demo") is True

    client = TestClient(app)
    assert client.get("/preview/landing").status_code == 404
    assert client.get("/preview/landing-premium").status_code == 404
    assert client.get("/preview/ficha-digital").status_code == 404
    assert client.get("/f/demo").status_code == 404
    assert client.get("/api/preview/ficha/health").status_code == 404


def test_executive_presentation_still_off():
    assert is_executive_presentation_enabled() is False
    client = TestClient(app)
    assert client.get("/executive/presentation").status_code == 404


def test_no_new_feature_flags_activated():
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
    assert os.environ.get("ENABLE_API_DOCS", "false").lower() in {"false", "0", "off", ""}


def test_operational_routes_still_served():
    client = TestClient(app)
    for path in (
        "/clientes",
        "/upload",
        "/funcionarios",
        "/produtividade",
        "/apresentacao",
        "/configuracoes",
        "/analytics",
        "/dashboard",
    ):
        r = client.get(path)
        assert r.status_code == 200, path
        assert "biomed-platform" in r.text, path
