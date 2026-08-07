"""EXEC-11A — product audit preview route (public, synthetic)."""
from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("SECRET_KEY", "exec11a-test-secret-not-for-production")
os.environ.setdefault("ENABLE_EXECUTIVE_UI", "false")

from fastapi.testclient import TestClient

from backend.main import app

ROOT = Path(__file__).resolve().parents[2]


def test_product_audit_preview_public():
    client = TestClient(app)
    r = client.get("/preview/product-audit")
    assert r.status_code == 200
    body = r.text
    assert "Capa executiva" in body or "Executive Cover" in body or "bm-audit" in body
    assert "Abertura executiva" in body or "CEO Opening" in body
    assert "Decisão" in body
    assert "Evidências" in body
    assert "Encerramento" in body
    assert "Assinatura BioMed" in body or "BioMed Signature" in body or "Executive Signature" in body
    assert "Modo Apresentação" in body
    assert "ILUSTRATIVO" in body or "ilustrativos" in body.lower()
    assert "bm-audit-panel" in body
    assert "MetricService" not in body
    assert "rule engine" not in body.lower()
    assert "dataset" not in body.lower()


def test_product_audit_assets_exist():
    assert (ROOT / "frontend/preview/product-audit.html").exists()
    assert (ROOT / "frontend/static/css/biomed-product-audit.css").exists()
    assert (ROOT / "frontend/static/img/executive/audit/ctx-industry.svg").exists()
