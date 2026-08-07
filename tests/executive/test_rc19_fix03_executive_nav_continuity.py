"""RC-1.9 FIX-03 + RC-21B — Executive in BioMed Platform shell (no parallel product nav)."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EXEC_HTML = ROOT / "frontend/executive.html"
APP_FIRST = ROOT / "frontend/static/js/executive/app-first.js"
LOGIN_HTML = ROOT / "frontend/login.html"
SHELL_JS = ROOT / "frontend/static/js/biomed-platform-shell.js"


def test_executive_uses_platform_shell_not_parallel_product():
    html = EXEC_HTML.read_text(encoding="utf-8")
    assert 'data-bm-shell="hub"' in html
    assert "biomed-platform-shell.js" in html
    assert "bm-nav-ops" not in html
    assert "Voltar ao operacional" not in html
    assert "Voltar ao sistema" not in html
    assert "← Voltar" not in html
    assert "bm-fx-steps" in html
    assert 'id="bm-nav-first"' in html
    # Platform menu owns Início / Analytics / Operação
    js = SHELL_JS.read_text(encoding="utf-8")
    assert 'link("/", "Início"' in js
    assert 'link("/executive"' in js


def test_experimental_and_flag_copy_removed_from_client_ui():
    html = EXEC_HTML.read_text(encoding="utf-8")
    assert "experiência experimental" not in html.lower()
    assert "Experiência experimental" not in html
    assert "ENABLE_EXECUTIVE_UI" not in html


def test_cache_bust_versioned_assets():
    html = EXEC_HTML.read_text(encoding="utf-8")
    for name in (
        "biomed-executive.css?v=",
        "biomed-platform.css?v=",
        "first-experience.js?v=",
        "decision-experience.js?v=",
        "evidence-intelligence.js?v=",
        "app-first.js?v=",
        "biomed-platform-shell.js?v=",
    ):
        assert name in html


def test_internal_back_never_assigns_slash_home():
    src = APP_FIRST.read_text(encoding="utf-8")
    assert 'location.href = "/"' not in src
    assert 'href = "/"' not in src
    assert 'showView("first"' in src
    assert "openDecisionExperience" in src
    assert "popstate" in src


def test_fix01_login_next_preserved():
    js = APP_FIRST.read_text(encoding="utf-8")
    html = LOGIN_HTML.read_text(encoding="utf-8")
    assert "executiveLoginUrl" in js
    assert 'encodeURIComponent("/executive")' in js
    assert "safeInternalNext" in html
    assert "postLoginDestination" in html
