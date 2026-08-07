"""RC-1.1 — release candidate consolidation preview (homologation only)."""
from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("SECRET_KEY", "rc1-test-secret-not-for-production")
os.environ.setdefault("ENABLE_EXECUTIVE_UI", "false")

from fastapi.testclient import TestClient

from backend.main import app

ROOT = Path(__file__).resolve().parents[2]


def test_release_candidate_preview_public():
    client = TestClient(app)
    r = client.get("/preview/release-candidate")
    assert r.status_code == 200
    body = r.text
    for name in (
        "Executive Cover",
        "Executive Opening",
        "Executive Summary",
        "Decision Experience",
        "Evidence Intelligence",
        "Executive Closing",
        "Executive Signature",
    ):
        assert name in body
    assert "Antes" in body and "Depois" in body
    assert "ILUSTRATIVO" in body
    assert "Opportunity" not in body
    assert "ORBIT funcional" not in body


def test_rc1_assets_exist():
    assert (ROOT / "frontend/preview/release-candidate.html").exists()
    assert (ROOT / "frontend/static/css/biomed-rc1.css").exists()
    assert (ROOT / "docs/release/RC1_PRODUCT_CONSOLIDATION.md").exists()


def test_rc1_does_not_touch_product_modules():
    # Consolidation is preview-only; product experience modules remain present.
    assert (ROOT / "frontend/static/js/executive/decision-experience.js").exists()
    assert (ROOT / "frontend/static/js/executive/evidence-intelligence.js").exists()
    assert (ROOT / "frontend/static/js/executive/first-experience.js").exists()
