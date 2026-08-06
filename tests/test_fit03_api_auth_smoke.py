"""FIT-03 — smoke: anonymous business API routes return 401."""
from __future__ import annotations

import os

os.environ.setdefault("SECRET_KEY", "fit03-test-secret-key-not-for-production")
os.environ.setdefault("ENVIRONMENT", "test")

from fastapi.testclient import TestClient

from backend.main import app


def test_anonymous_get_cliente_returns_401():
    client = TestClient(app)
    r = client.get("/api/clientes/1")
    assert r.status_code == 401


def test_anonymous_get_analises_setores_returns_401():
    client = TestClient(app)
    r = client.get("/api/analises/setores", params={"client_id": 1})
    assert r.status_code == 401


def test_health_remains_public():
    client = TestClient(app)
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert "status" in body
    assert "version" in body
    # No filesystem paths / secrets
    dumped = str(body).lower()
    assert "/workspace" not in dumped
    assert "secret" not in dumped
    assert "password" not in dumped
