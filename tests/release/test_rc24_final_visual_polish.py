"""RC-24 — Final visual polish (responsive + legacy residue). No API/DB/flags."""
from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("SECRET_KEY", "rc24-polish-secret-not-for-production")

from fastapi.testclient import TestClient

from backend.main import app

ROOT = Path(__file__).resolve().parents[2]
FRONTEND = ROOT / "frontend"
SHELL = (FRONTEND / "static/js/biomed-platform-shell.js").read_text(encoding="utf-8")
POLISH = FRONTEND / "static/css/biomed-polish.css"


def test_polish_layer_exists_and_scoped():
    assert POLISH.is_file()
    text = POLISH.read_text(encoding="utf-8")
    assert "RC-24" in text or "RC24" in text
    assert "overflow-x: hidden" in text
    assert "clamp(220px" in text or "chart-wrapper" in text
    assert "@media (max-width: 390px)" in text
    assert "@media (max-width: 1440px)" in text
    assert "@media (max-width: 768px)" in text
    assert "--primary: var(--bm-brand" in text or "--primary:" in text
    assert "apresentacao-container" in text
    assert "powerbi-container" in text
    assert "table-container" in text


def test_shell_loads_polish_after_experience():
    assert 'CACHE = "rc24"' in SHELL or 'CACHE = "rc25"' in SHELL
    assert "biomed-polish.css" in SHELL
    assert "data-bm-polish" in SHELL
    exp = SHELL.index("biomed-experience.css")
    pol = SHELL.index("biomed-polish.css")
    assert pol > exp


def test_active_pages_link_polish_css():
    pages = (
        "index-legacy.html",
        "apresentacao.html",
        "clientes.html",
        "funcionarios.html",
        "upload.html",
        "upload_inteligente.html",
        "produtividade.html",
        "comparativos.html",
        "dados_powerbi.html",
        "dashboard_powerbi.html",
        "configuracoes.html",
        "perfil_funcionario.html",
        "analytics.html",
        "index.html",
        "executive.html",
    )
    for name in pages:
        html = (FRONTEND / name).read_text(encoding="utf-8")
        # RC25 hub pages may load polish via shell ensureStyles; legacy pages keep explicit links
        if name in ("analytics.html", "index.html", "executive.html"):
            assert "biomed-platform" in html or "biomed-core" in html or "biomed-polish" in html, name
        else:
            assert "biomed-polish.css" in html or "biomed-core.css" in html, name
        assert "rc24" in html or "rc25" in html, name


def test_apresentacao_empty_indicator_not_one_over_zero():
    html = (FRONTEND / "apresentacao.html").read_text(encoding="utf-8")
    assert 'id="slideAtual">1</span>' not in html
    assert 'id="totalSlides">0</span>' not in html
    assert "—" in html or "&mdash;" in html or "slideAtual" in html
    js = (FRONTEND / "static/js/apresentacao.js").read_text(encoding="utf-8")
    assert "is-empty" in js or "Sem conteúdo" in js
    # Default brand fallback is BioMed, not Material indigo
    assert "primary: '#1a4566'" in js
    assert "primary: '#1a237e'" not in js


def test_no_api_db_flag_surface_changes():
    # Guardrails: polish CSS must not mention migrations / ALTER / feature enable
    text = POLISH.read_text(encoding="utf-8")
    assert "ALTER TABLE" not in text.upper()
    assert "ENABLE_" not in text
    assert os.environ.get("ENABLE_EXECUTIVE_PRESENTATION", "false").lower() in {
        "false",
        "0",
        "off",
        "",
    }
    assert os.environ.get("ENABLE_PREVIEW_SURFACES", "false").lower() in {
        "false",
        "0",
        "off",
        "",
    }


def test_public_and_core_routes_still_serve():
    client = TestClient(app)
    for path in (
        "/landing",
        "/login",
        "/analytics",
        "/apresentacao",
        "/static/css/biomed-polish.css",
    ):
        r = client.get(path)
        assert r.status_code == 200, path


def test_audit_doc_exists():
    doc = ROOT / "docs/release/RC24_FINAL_VISUAL_POLISH.md"
    assert doc.is_file()
    body = doc.read_text(encoding="utf-8")
    assert "LEGACY_LOOK_REMAINS" in body or "READY_FOR_HUMAN_ACCEPTANCE" in body
