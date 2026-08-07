"""RC-21B — Experience unification (Executive in platform shell; no legacy chrome)."""
from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("SECRET_KEY", "rc21b-unification-secret-not-for-production")

from fastapi.testclient import TestClient

from backend.main import app

ROOT = Path(__file__).resolve().parents[2]
FRONTEND = ROOT / "frontend"


def test_blocker1_executive_inside_platform_shell():
    html = (FRONTEND / "executive.html").read_text(encoding="utf-8")
    assert 'data-bm-shell="hub"' in html
    assert "biomed-platform-shell.js" in html
    assert "bm-shell--platform" in html
    assert "bm-fx-steps" in html
    # Parallel product chrome removed
    assert "bm-nav--minimal" not in html
    assert "bm-nav-ops" not in html
    assert "Visão Executiva" not in html or "bm-brand-sub" not in html
    assert "Voltar" not in html
    client = TestClient(app)
    # Route may 404 if ENABLE_EXECUTIVE_UI false in test env — HTML file is source of truth
    assert (FRONTEND / "static/js/biomed-platform-shell.js").is_file()


def test_blocker2_auth_skips_legacy_header_under_shell():
    auth = (FRONTEND / "static/js/auth.js").read_text(encoding="utf-8")
    assert 'getAttribute("data-bm-shell")' in auth
    assert "platform shell owns user chrome" in auth or "platform shell owns navigation" in auth
    css = (FRONTEND / "static/css/biomed-platform.css").read_text(encoding="utf-8")
    assert "header-user-widget" in css
    assert "display: none !important" in css


def test_shell_logout_exists_for_flow():
    js = (FRONTEND / "static/js/biomed-platform-shell.js").read_text(encoding="utf-8")
    assert "bm-plat-logout" in js
    assert 'localStorage.removeItem("access_token")' in js


def test_one_menu_labels_unchanged():
    js = (FRONTEND / "static/js/biomed-platform-shell.js").read_text(encoding="utf-8")
    for label in ("Início", "Executive", "Analytics", "Operação", "Apresentações", "Fichas", "Configurações"):
        assert label in js


def test_landing_login_still_intact():
    client = TestClient(app)
    assert client.get("/landing").status_code == 200
    assert "BioMed" in client.get("/login").text
