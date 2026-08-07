"""RC-1.9 FIX-02 — Executive static assets must carry cache-bust query."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EXEC_HTML = ROOT / "frontend/executive.html"

CRITICAL = [
    "/static/css/biomed-executive.css",
    "/static/js/executive/first-experience.js",
    "/static/js/executive/decision-experience.js",
    "/static/js/executive/evidence-intelligence.js",
    "/static/js/executive/app-first.js",
]


def test_executive_html_cache_busts_critical_assets():
    html = EXEC_HTML.read_text(encoding="utf-8")
    for asset in CRITICAL:
        # Require version query (FIX-02+); exact token may increment (FIX-03…)
        assert re.search(re.escape(asset) + r"\?v=[A-Za-z0-9._-]+", html), asset
        assert f'"{asset}"' not in html  # bare unversioned href/src
