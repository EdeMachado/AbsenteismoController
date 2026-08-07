"""FIT-03 — smoke: anonymous business API routes return 401; public paths stay open."""
from __future__ import annotations

import os

os.environ.setdefault("SECRET_KEY", "fit03-test-secret-key-not-for-production")
os.environ.setdefault("ENVIRONMENT", "test")

from fastapi.testclient import TestClient

from backend.main import app
from backend.authz import PUBLIC_API_PATHS, api_docs_enabled, is_public_api_path


# Representative business paths previously open in FIT-02 (must 401 anonymously).
ANONYMOUS_401_SAMPLES = [
    ("GET", "/api/clientes"),
    ("GET", "/api/clientes/1"),
    ("POST", "/api/clientes"),
    ("PUT", "/api/clientes/1"),
    ("DELETE", "/api/clientes/1"),
    ("POST", "/api/clientes/1/arquivar"),
    ("POST", "/api/clientes/1/ativar"),
    ("GET", "/api/analises/setores"),
    ("GET", "/api/analises/funcionarios"),
    ("GET", "/api/analises/cids"),
    ("GET", "/api/tendencias"),
    ("GET", "/api/dados/todos"),
    ("GET", "/api/dados/1"),
    ("GET", "/api/funcionario/perfil"),
    ("POST", "/api/upload/analyze"),
    ("POST", "/api/upload/process"),
    ("GET", "/api/uploads"),
    ("GET", "/api/dashboard"),
    ("GET", "/api/produtividade"),
    ("GET", "/api/produtividade/evolucao"),
    ("GET", "/api/export/excel"),
    ("GET", "/api/backup/list"),
    ("GET", "/api/users"),
    ("GET", "/api/config"),
    ("GET", "/api/buscar-cnpj/00000000000000"),
    ("POST", "/api/cadastro-empresa"),
    ("GET", "/api/health/integrity"),
    ("GET", "/api/filtros"),
    ("GET", "/api/apresentacao"),
]


def test_public_api_paths_allowlist():
    assert PUBLIC_API_PATHS == frozenset({"/api/auth/login", "/api/health"})
    assert is_public_api_path("/api/health")
    assert is_public_api_path("/api/auth/login")
    assert not is_public_api_path("/api/clientes")


def test_anonymous_business_routes_return_401():
    client = TestClient(app)
    for method, path in ANONYMOUS_401_SAMPLES:
        r = client.request(method, path)
        assert r.status_code == 401, f"{method} {path} -> {r.status_code} {r.text[:200]}"


def test_health_remains_public_and_sanitized():
    client = TestClient(app)
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert "status" in body
    assert "version" in body
    dumped = str(body).lower()
    assert "/workspace" not in dumped
    assert "secret" not in dumped
    assert "password" not in dumped
    assert "absenteismo.db" not in dumped


def test_login_remains_public():
    client = TestClient(app)
    # Missing form fields → 422, not 401 (route reachable without Bearer)
    r = client.post("/api/auth/login")
    assert r.status_code == 422


def test_api_docs_policy_default_for_production_like():
    prev = os.environ.get("ENVIRONMENT")
    prev_docs = os.environ.get("ENABLE_API_DOCS")
    try:
        os.environ.pop("ENABLE_API_DOCS", None)
        os.environ["ENVIRONMENT"] = "production"
        assert api_docs_enabled() is False
        os.environ["ENVIRONMENT"] = "development"
        assert api_docs_enabled() is True
        os.environ["ENABLE_API_DOCS"] = "0"
        assert api_docs_enabled() is False
        os.environ["ENABLE_API_DOCS"] = "1"
        os.environ["ENVIRONMENT"] = "production"
        assert api_docs_enabled() is True
    finally:
        if prev is None:
            os.environ.pop("ENVIRONMENT", None)
        else:
            os.environ["ENVIRONMENT"] = prev
        if prev_docs is None:
            os.environ.pop("ENABLE_API_DOCS", None)
        else:
            os.environ["ENABLE_API_DOCS"] = prev_docs
