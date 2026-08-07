"""EXEC-11 — identity preview route is public, static, no auth."""
from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("SECRET_KEY", "exec11-test-secret-not-for-production")
os.environ.setdefault("ENABLE_EXECUTIVE_UI", "false")

from fastapi.testclient import TestClient

from backend.main import app

ROOT = Path(__file__).resolve().parents[2]


def test_executive_identity_preview_public():
    client = TestClient(app)
    r = client.get("/preview/executive")
    assert r.status_code == 200
    assert "Executive Cover" in r.text
    assert "Executive Closing" in r.text
    assert "BioMed Executive Signature" in r.text
    assert "dataset sintético" in r.text.lower() or "sintético" in r.text


def test_executive_identity_preview_alias():
    client = TestClient(app)
    r = client.get("/staging/executive-preview")
    assert r.status_code == 200
    assert "bm-cover" in r.text


def test_identity_assets_exist():
    assert (ROOT / "frontend/static/css/biomed-identity.css").exists()
    assert (ROOT / "frontend/preview/executive-identity.html").exists()
    assert (ROOT / "frontend/static/img/executive/bg-institutional.svg").exists()
    assert (ROOT / "frontend/static/fonts/biomed/dm-sans-400.woff2").exists()


def test_exec11_does_not_rewrite_decision_evidence_modules():
    # Guard: EXEC-11 must not rewrite Decision/Evidence product modules.
    # Presence-only check of unchanged module entrypoints still existing.
    assert (ROOT / "frontend/static/js/executive/decision-experience.js").exists()
    assert (ROOT / "frontend/static/js/executive/evidence-intelligence.js").exists()
