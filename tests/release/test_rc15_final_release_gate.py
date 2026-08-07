"""RC-1.5 — preview surfaces fail-closed in production."""
from __future__ import annotations

import os

os.environ.setdefault("SECRET_KEY", "rc15-gate-secret-not-for-production")


def test_preview_gate_defaults_off_in_production(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.delenv("ENABLE_PREVIEW_SURFACES", raising=False)
    from backend.preview_gate import preview_surfaces_enabled, is_preview_homologation_path
    from backend.authz import is_public_api_path

    assert preview_surfaces_enabled() is False
    assert is_preview_homologation_path("/preview/landing") is True
    assert is_preview_homologation_path("/api/preview/ficha/templates") is True
    assert is_preview_homologation_path("/f/abc") is True
    assert is_public_api_path("/api/preview/ficha/templates") is False
    assert is_public_api_path("/api/health") is True


def test_preview_gate_on_in_test_env(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.delenv("ENABLE_PREVIEW_SURFACES", raising=False)
    from backend.preview_gate import preview_surfaces_enabled
    from backend.authz import is_public_api_path

    assert preview_surfaces_enabled() is True
    assert is_public_api_path("/api/preview/ficha/templates") is True


def test_production_blocks_preview_http(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.delenv("ENABLE_PREVIEW_SURFACES", raising=False)
    monkeypatch.setenv("ENABLE_EXECUTIVE_UI", "false")
    # Re-import app behavior via TestClient with monkeypatched env before import path
    from fastapi.testclient import TestClient
    from backend.main import app

    client = TestClient(app)
    for path in (
        "/preview/landing",
        "/preview/ficha-digital",
        "/preview/executive-presentation-rc",
        "/staging/executive-preview",
        "/api/preview/ficha/templates",
        "/api/preview/ficha/reset",
        "/f/" + ("a" * 32),
    ):
        r = client.get(path)
        assert r.status_code == 404, path
    # Legacy upload preview page must remain reachable (not homologation).
    assert client.get("/preview").status_code == 200


def test_test_env_allows_preview_http(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.delenv("ENABLE_PREVIEW_SURFACES", raising=False)
    from fastapi.testclient import TestClient
    from backend.main import app

    client = TestClient(app)
    assert client.get("/preview/landing").status_code == 200
    assert client.get("/api/preview/ficha/templates").status_code == 200
    assert client.get("/preview").status_code == 200
