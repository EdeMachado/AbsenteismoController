"""RC-1.9 FIX-02 — Executive static assets must carry cache-bust query."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EXEC_HTML = ROOT / "frontend/executive.html"

REQUIRED = [
    "/static/css/biomed-executive.css?v=rc19fix02",
    "/static/js/executive/first-experience.js?v=rc19fix02",
    "/static/js/executive/decision-experience.js?v=rc19fix02",
    "/static/js/executive/evidence-intelligence.js?v=rc19fix02",
    "/static/js/executive/app-first.js?v=rc19fix02",
]


def test_executive_html_cache_busts_critical_assets():
    html = EXEC_HTML.read_text(encoding="utf-8")
    for asset in REQUIRED:
        assert asset in html, f"missing cache-bust: {asset}"
    # Unversioned critical assets must not remain
    assert 'href="/static/css/biomed-executive.css"' not in html
    assert 'src="/static/js/executive/app-first.js"' not in html
    assert 'src="/static/js/executive/first-experience.js"' not in html
    assert 'src="/static/js/executive/decision-experience.js"' not in html
    assert 'src="/static/js/executive/evidence-intelligence.js"' not in html
