"""FIT-04 — CORS policy and security/cache headers."""
from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("SECRET_KEY", "fit04-test-secret-key-not-for-production")

from backend.cors_config import cors_allowed_origins, cors_allow_credentials, is_production_like
from backend.main import app


def test_production_cors_rejects_wildcard(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("CORS_ALLOWED_ORIGINS", "https://app.example.com,*")
    with pytest.raises(RuntimeError):
        cors_allowed_origins()


def test_production_cors_empty_by_default(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.delenv("CORS_ALLOWED_ORIGINS", raising=False)
    assert cors_allowed_origins() == []
    assert cors_allow_credentials() is False


def test_staging_cors_configurable(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "staging")
    monkeypatch.setenv("CORS_ALLOWED_ORIGINS", "http://127.0.0.1:18081")
    assert cors_allowed_origins() == ["http://127.0.0.1:18081"]
    assert cors_allow_credentials() is True


def test_api_responses_have_security_and_no_store_cache():
    client = TestClient(app)
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.headers.get("X-Content-Type-Options") == "nosniff"
    assert r.headers.get("X-Frame-Options") == "DENY"
    assert r.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
    assert "geolocation=()" in (r.headers.get("Permissions-Policy") or "")
    assert "Content-Security-Policy" in r.headers
    cc = r.headers.get("Cache-Control", "")
    assert "no-store" in cc or "no-cache" in cc


def test_login_response_not_publicly_cacheable():
    client = TestClient(app)
    r = client.post("/api/auth/login", data={"username": "x", "password": "y"})
    # 401/422 expected; still must set private cache headers
    cc = r.headers.get("Cache-Control", "")
    assert "no-store" in cc or "no-cache" in cc or "private" in cc
