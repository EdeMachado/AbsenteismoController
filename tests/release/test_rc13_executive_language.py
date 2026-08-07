"""RC-1.3 — Executive Language & Trust (copy-only regression)."""
from __future__ import annotations

import os
import re
from pathlib import Path

os.environ.setdefault("SECRET_KEY", "rc13-test-secret-not-for-production")
os.environ.setdefault("ENABLE_EXECUTIVE_UI", "false")

from fastapi.testclient import TestClient

from backend.main import app

ROOT = Path(__file__).resolve().parents[2]
FRONTEND = ROOT / "frontend"

BANNED_UI = re.compile(
    r"\b(payload|endpoint|schema|dataset|MetricService|DataQualityService|"
    r"fallback|provider|backend|frontend|JSON|stack|exception|"
    r"internal error|Erro interno|Falha inesperada|rule engine|ENABLE_EXECUTIVE|"
    r"token opaco|Reset demo|Error state|LLM)\b",
    re.I,
)


def _scan_texts(paths: list[Path]) -> list[str]:
    hits = []
    for p in paths:
        text = p.read_text(encoding="utf-8")
        for m in BANNED_UI.finditer(text):
            start = max(0, m.start() - 40)
            ctx = text[start : m.end() + 40]
            word = m.group(0).lower()
            if word == "json" and (".json" in ctx or "application/json" in ctx or "stringify" in ctx):
                continue
            if word == "payload" and (
                "lastPayload" in ctx
                or "const payload" in ctx
                or "renderAll(payload)" in ctx
                or "function renderAll" in ctx
            ):
                continue
            if "lastPayload" in ctx or "const payload" in ctx or "function renderAll" in ctx:
                continue
            if "dataset.panel" in ctx or "dataset.module" in ctx:
                continue
            hits.append(f"{p.name}: {m.group(0)} :: {ctx.replace(chr(10),' ')[:80]}")
    return hits


def test_rc13_banned_terms_absent_from_key_ui_files():
    paths = [
        FRONTEND / "preview/landing-premium.html",
        FRONTEND / "preview/ficha-digital.html",
        FRONTEND / "preview/release-candidate-functional.html",
        FRONTEND / "static/js/executive/first-experience.js",
        FRONTEND / "static/js/executive/decision-experience.js",
        FRONTEND / "static/js/executive/evidence-intelligence.js",
        FRONTEND / "static/js/executive/app-first.js",
        FRONTEND / "static/js/ficha/digital-form.js",
    ]
    hits = _scan_texts(paths)
    assert hits == [], hits


def test_rc13_docs_exist():
    assert (ROOT / "docs/release/RC13_EXECUTIVE_LANGUAGE.md").exists()
