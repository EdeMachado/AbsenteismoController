"""RC-1.9 FIX-03 — Executive navigation continuity (no Voltar → /)."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EXEC_HTML = ROOT / "frontend/executive.html"
APP_FIRST = ROOT / "frontend/static/js/executive/app-first.js"
LOGIN_HTML = ROOT / "frontend/login.html"


def test_operational_link_is_explicit_secondary_not_voltar():
    html = EXEC_HTML.read_text(encoding="utf-8")
    assert "Área Operacional" in html
    assert 'href="/" class="bm-nav-ops"' in html or 'id="bm-nav-ops"' in html
    assert "Voltar ao operacional" not in html
    assert "← Voltar" not in html


def test_experimental_and_flag_copy_removed_from_client_ui():
    html = EXEC_HTML.read_text(encoding="utf-8")
    assert "experiência experimental" not in html.lower()
    assert "Experiência experimental" not in html
    assert "ENABLE_EXECUTIVE_UI" not in html


def test_cache_bust_incremented_to_fix03():
    html = EXEC_HTML.read_text(encoding="utf-8")
    for asset in (
        "biomed-executive.css?v=rc19fix03",
        "first-experience.js?v=rc19fix03",
        "decision-experience.js?v=rc19fix03",
        "evidence-intelligence.js?v=rc19fix03",
        "app-first.js?v=rc19fix03",
    ):
        assert asset in html


def test_internal_back_never_assigns_slash_home():
    src = APP_FIRST.read_text(encoding="utf-8")
    # No internal journey redirect to legacy home
    assert 'location.href = "/"' not in src
    assert 'href = "/"' not in src
    # Decision/Evidence backs stay inside Executive helpers
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
