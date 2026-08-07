"""RC-1.4 — Executive Presentation Premium preview & composer."""
from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("SECRET_KEY", "rc14-test-secret-not-for-production")
os.environ.setdefault("ENABLE_EXECUTIVE_UI", "false")

from fastapi.testclient import TestClient

from backend.executive.presentation import SLIDE_DEFS, compose_presentation
from backend.executive.presentation_preview import (
    build_synthetic_executive_payload,
    build_synthetic_premium_deck,
)
from backend.main import app

ROOT = Path(__file__).resolve().parents[2]


def test_rc14_preview_public():
    client = TestClient(app)
    r = client.get("/preview/executive-presentation-rc")
    assert r.status_code == 200
    body = r.text
    assert "BioMed Executive Meeting" in body
    assert "__RC14_DECK__" in body
    assert "ILUSTRATIVO" in body or "ilustrativ" in body.lower()
    assert "presentation-premium.js" in body
    assert "payload" not in body.lower() or "__RC14_DECK__" in body


def test_rc14_synthetic_deck_answers_four_questions():
    deck = build_synthetic_premium_deck()
    ids = [s["id"] for s in deck["slides"]]
    assert ids[0] == "cover"
    assert ids[-1] == "closing"
    assert "financial" in ids
    assert "priorities" in ids
    assert "decision" in ids
    assert deck["estimated_minutes"] <= 5
    assert len(deck["slides"]) <= 15
    assert len(SLIDE_DEFS) == 15
    blob = str(deck).lower()
    assert "cpf" not in blob
    assert "matricula" not in blob
    fin = next(s for s in deck["slides"] if s["id"] == "financial")
    assert fin["financial"]["premissa"] == "ILUSTRATIVO"
    assert fin["financial"]["formula"] == "HORAS PERDIDAS × CUSTO HORA"


def test_rc14_omits_inaction_without_model():
    payload = build_synthetic_executive_payload()
    payload["decision_experience"]["business_impact"]["cost_if_nothing"] = {
        "available": False,
        "value": None,
    }
    deck = compose_presentation(payload)
    ids = {s["id"] for s in deck["slides"]}
    omitted = {o["id"] for o in deck["omitted"]}
    assert "inaction" in omitted
    assert "inaction" not in ids


def test_rc14_assets_and_docs():
    assert (ROOT / "frontend/preview/executive-presentation-rc.html").exists()
    assert (ROOT / "frontend/static/js/executive/presentation-premium.js").exists()
    assert (ROOT / "frontend/static/css/biomed-presentation-premium.css").exists()
    assert (ROOT / "docs/release/RC14_EXECUTIVE_PRESENTATION_PREMIUM.md").exists()
