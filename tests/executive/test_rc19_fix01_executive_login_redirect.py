"""RC-1.9 FIX-01 — Executive login redirect regression.

Bug: /executive without token → /login → (token+cliente) → / (legacy).
Fix: /executive → /login?next=/executive → /executive after auth.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
APP_FIRST = ROOT / "frontend/static/js/executive/app-first.js"
LOGIN_HTML = ROOT / "frontend/login.html"


def safe_internal_next(raw: str | None) -> str | None:
    """Mirror of login.html safeInternalNext — keep in sync."""
    if not raw or not isinstance(raw, str):
        return None
    n = raw.strip()
    if not n.startswith("/"):
        return None
    if n.startswith("//"):
        return None
    if "\\" in n:
        return None
    if "://" in n:
        return None
    if re.match(r"^[a-zA-Z][a-zA-Z0-9+.\-]*:", n):
        return None
    return n


def post_login_destination(next_param: str | None, cliente_selecionado: str | None) -> str:
    nxt = safe_internal_next(next_param)
    if nxt:
        return nxt
    if cliente_selecionado:
        return "/"
    return "/clientes"


def test_app_first_redirects_to_login_with_next_executive():
    src = APP_FIRST.read_text(encoding="utf-8")
    assert "executiveLoginUrl" in src
    assert 'encodeURIComponent("/executive")' in src
    assert 'href = "/login"' not in src or "login?next=" in src
    # bare /login redirects removed from auth paths
    assert "executiveLoginUrl()" in src
    assert src.count('window.location.href = "/login"') == 0


def test_login_html_has_safe_next_and_post_login_destination():
    src = LOGIN_HTML.read_text(encoding="utf-8")
    assert "safeInternalNext" in src
    assert "postLoginDestination" in src
    assert "postLoginDestination()" in src


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("/executive", "/executive"),
        ("/executive#decision", "/executive#decision"),
        ("/clientes", "/clientes"),
        ("/", "/"),
        ("https://evil.com", None),
        ("//evil.com", None),
        ("javascript:alert(1)", None),
        ("http://evil.com/x", None),
        ("\\/evil", None),
        ("", None),
        (None, None),
        ("  /executive  ", "/executive"),
    ],
)
def test_safe_internal_next_rejects_open_redirect(raw, expected):
    assert safe_internal_next(raw) == expected


def test_login_with_next_executive_returns_to_executive():
    assert post_login_destination("/executive", "2") == "/executive"
    assert post_login_destination("/executive", None) == "/executive"


def test_login_without_next_preserves_legacy():
    assert post_login_destination(None, "2") == "/"
    assert post_login_destination(None, None) == "/clientes"
    assert post_login_destination("", "4") == "/"


def test_malicious_next_falls_back_to_legacy():
    assert post_login_destination("https://evil.com", "2") == "/"
    assert post_login_destination("//evil.com", None) == "/clientes"
    assert post_login_destination("javascript:alert(1)", None) == "/clientes"


def test_executive_page_uses_app_first():
    html = (ROOT / "frontend/executive.html").read_text(encoding="utf-8")
    assert "app-first.js" in html
