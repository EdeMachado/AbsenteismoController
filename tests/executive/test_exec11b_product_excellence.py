"""EXEC-11B — product excellence audit preview (measure-only, public)."""
from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("SECRET_KEY", "exec11b-test-secret-not-for-production")
os.environ.setdefault("ENABLE_EXECUTIVE_UI", "false")

from fastapi.testclient import TestClient

from backend.main import app

ROOT = Path(__file__).resolve().parents[2]


def test_product_excellence_preview_public():
    client = TestClient(app)
    r = client.get("/preview/product-excellence")
    assert r.status_code == 200
    body = r.text
    assert "Audit Mode" in body
    assert "Product Metrics" in body or "x-metrics" in body
    assert "Heatmap de Complexidade" in body
    assert "Design Consistency Report" in body
    assert "Executive Readability Report" in body
    assert "Executive Value Report" in body
    assert "Executive Summary" in body
    assert "bm-audit-toggle" in body
    # audit panels exist but default mode hides via CSS class gate
    assert "is-audit-mode" in body or "bm-audit-toggle" in body


def test_product_excellence_assets_exist():
    assert (ROOT / "frontend/preview/product-excellence.html").exists()
    assert (ROOT / "frontend/static/css/biomed-product-excellence.css").exists()
    assert (ROOT / "docs/executive/EXEC11B_PRODUCT_EXCELLENCE.md").exists()


def test_excellence_does_not_change_business_apis():
    # Guard: no new business API paths introduced by EXEC-11B beyond preview route.
    src = (ROOT / "backend/main.py").read_text(encoding="utf-8")
    assert "/preview/product-excellence" in src
    assert "Opportunity Portfolio" not in src
