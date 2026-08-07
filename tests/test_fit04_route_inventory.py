"""FIT-04 — runtime FastAPI inventory must stay fully classified."""
from __future__ import annotations

import os

os.environ.setdefault("SECRET_KEY", "fit04-test-secret-key-not-for-production")
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("ENABLE_INTELLIGENT_INGESTION", "false")
os.environ.setdefault("ENABLE_BIOMED_PERFORMANCE_ENGINE", "false")

from fastapi.routing import APIRoute
from fastapi.testclient import TestClient

from backend.authz import PUBLIC_API_PATHS, api_docs_enabled
from backend.main import app
from backend.route_security_registry import (
    PUBLIC_INTENTIONAL,
    inventory_unclassified,
)


def test_no_unclassified_api_routes():
    bad = inventory_unclassified(app)
    assert bad == [], f"Unclassified API routes appeared: {bad}"


def test_only_login_and_health_are_public_api():
    assert PUBLIC_API_PATHS == frozenset({"/api/auth/login", "/api/health"})
    assert PUBLIC_INTENTIONAL == frozenset(
        {("POST", "/api/auth/login"), ("GET", "/api/health")}
    )


def test_ingestion_routes_absent_when_flags_off():
    paths = {
        r.path
        for r in app.routes
        if isinstance(r, APIRoute) and r.path.startswith("/api/ingestion")
    }
    assert paths == set()


def test_docs_disabled_in_production_env(monkeypatch):
    monkeypatch.delenv("ENABLE_API_DOCS", raising=False)
    monkeypatch.setenv("ENVIRONMENT", "production")
    assert api_docs_enabled() is False


def test_anonymous_non_public_api_still_401():
    client = TestClient(app)
    r = client.get("/api/clientes")
    assert r.status_code == 401
    r2 = client.get("/api/health")
    assert r2.status_code == 200
