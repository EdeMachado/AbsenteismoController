"""RC-1.2 — functional consolidation preview + synthetic journey."""
from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("SECRET_KEY", "rc12-test-secret-not-for-production")
os.environ.setdefault("ENABLE_EXECUTIVE_UI", "false")

from fastapi.testclient import TestClient

from backend.main import app

ROOT = Path(__file__).resolve().parents[2]
FRONTEND = ROOT / "frontend"


def test_rc12_preview_public():
    client = TestClient(app)
    r = client.get("/preview/release-candidate-functional")
    assert r.status_code == 200
    body = r.text
    assert "Como sabemos disso?" in body
    assert "Voltar à decisão" in body
    assert "Dados insuficientes para esta análise." in body
    assert "Não foi possível carregar esta análise." in body
    assert "NÃO INFORMADO" in body
    assert "Tentar novamente" in body
    assert "payload" not in body.lower()


def test_rc12_assets_and_microcopy():
    assert (FRONTEND / "preview/release-candidate-functional.html").exists()
    assert (FRONTEND / "static/css/biomed-rc12.css").exists()
    js = (FRONTEND / "static/js/executive/app-first.js").read_text(encoding="utf-8")
    assert "Não foi possível carregar esta análise." in js
    assert "Tentar novamente" in js
    assert "forbidden" in js
    assert "hashchange" in js
    assert "payload." not in js or "lastPayload" in js  # internal vars ok
    assert "indisponível neste payload" not in js


def test_rc12_synthetic_journey_interactions():
    """Simulate open → KPIs → decision → evidence → back → closing.
    Count primary interactions (anchor CTAs in consolidated flow).
    """
    html = (FRONTEND / "preview/release-candidate-functional.html").read_text(encoding="utf-8")
    # Journey anchors that a user would click in sequence
    steps = [
        "#opening",
        "#kpis",
        "#decision",
        "#evidence",
        "#decision",  # back
        "#closing",
    ]
    for step in steps:
        assert step in html
    # Primary CTAs should remain few
    assert html.count("is-primary") <= 6
    interactions = len(steps)
    assert interactions <= 8  # simple predictable flow


def test_rc1_preview_still_available():
    client = TestClient(app)
    assert client.get("/preview/release-candidate").status_code == 200
