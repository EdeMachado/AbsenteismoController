"""
S01-A — Testes de autorização e tenant guard.
Usa SQLite temporário isolado. Sem dados reais / PII / produção.
"""
from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Isola SECRET_KEY antes de importar o app
os.environ["SECRET_KEY"] = "s01a-test-secret-key-not-for-production"

from backend.database import Base, get_db
from backend.models import Client, User, Produtividade, Upload
from backend.auth import get_password_hash, create_access_token
from backend.main import app
from backend.tenant import resolve_authorized_client


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    session = Session()

    # Tenants sintéticos (IDs alinhados ao código de tema: 2 e 4)
    c_conver = Client(
        id=2,
        nome="Tenant Alpha SA",
        nome_fantasia="Alpha",
        cnpj="11111111000111",
        situacao="ativo",
    )
    c_roda = Client(
        id=4,
        nome="Tenant Beta SA",
        nome_fantasia="Beta",
        cnpj="22222222000122",
        situacao="ativo",
    )
    session.add_all([c_conver, c_roda])
    session.flush()

    users = [
        User(
            username="user_alpha",
            email="alpha@example.test",
            password_hash=get_password_hash("test-pass-alpha"),
            nome_completo="User Alpha",
            is_active=True,
            is_admin=False,
            client_id=2,
        ),
        User(
            username="user_beta",
            email="beta@example.test",
            password_hash=get_password_hash("test-pass-beta"),
            nome_completo="User Beta",
            is_active=True,
            is_admin=False,
            client_id=4,
        ),
        User(
            username="user_orphan",
            email="orphan@example.test",
            password_hash=get_password_hash("test-pass-orphan"),
            nome_completo="User Orphan",
            is_active=True,
            is_admin=False,
            client_id=None,
        ),
        User(
            username="admin_explicit",
            email="admin_explicit@example.test",
            password_hash=get_password_hash("test-pass-admin"),
            nome_completo="Admin Explicit",
            is_active=True,
            is_admin=True,
            client_id=None,
        ),
    ]
    session.add_all(users)
    session.add(
        Produtividade(
            client_id=2,
            mes_referencia="2026-01",
            numero_tipo="1",
            tipo_consulta="Teste",
            total=1,
        )
    )
    session.add(
        Produtividade(
            client_id=4,
            mes_referencia="2026-01",
            numero_tipo="1",
            tipo_consulta="Teste",
            total=2,
        )
    )
    session.add(
        Upload(client_id=2, filename="alpha.xlsx", mes_referencia="2026-01", total_registros=0)
    )
    session.add(
        Upload(client_id=4, filename="beta.xlsx", mes_referencia="2026-01", total_registros=0)
    )
    session.commit()

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture()
def client(db_session):
    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        # Startup pode zerar client_id — restaura vínculos de teste
        for username, cid in [("user_alpha", 2), ("user_beta", 4), ("user_orphan", None)]:
            u = db_session.query(User).filter(User.username == username).first()
            if u:
                u.client_id = cid
                u.is_admin = False
        admin = db_session.query(User).filter(User.username == "admin_explicit").first()
        if admin:
            admin.is_admin = True
            admin.client_id = None
        db_session.commit()
        yield test_client
    app.dependency_overrides.clear()


def _token(username: str) -> str:
    return create_access_token({"sub": username})


def _auth(username: str) -> dict:
    return {"Authorization": f"Bearer {_token(username)}"}


def test_resolve_bound_user_own_tenant(db_session):
    user = db_session.query(User).filter(User.username == "user_alpha").first()
    client = resolve_authorized_client(db_session, user, 2)
    assert client.id == 2


def test_resolve_bound_user_cross_tenant_forbidden(db_session):
    from fastapi import HTTPException

    user = db_session.query(User).filter(User.username == "user_alpha").first()
    with pytest.raises(HTTPException) as exc:
        resolve_authorized_client(db_session, user, 4)
    assert exc.value.status_code == 403


def test_resolve_orphan_forbidden(db_session):
    from fastapi import HTTPException

    user = db_session.query(User).filter(User.username == "user_orphan").first()
    with pytest.raises(HTTPException) as exc:
        resolve_authorized_client(db_session, user, 2)
    assert exc.value.status_code == 403


def test_resolve_admin_ok(db_session):
    admin = db_session.query(User).filter(User.username == "admin_explicit").first()
    client = resolve_authorized_client(db_session, admin, 4)
    assert client.id == 4


def test_resolve_admin_missing_client_id_no_fallback(db_session):
    from fastapi import HTTPException

    admin = db_session.query(User).filter(User.username == "admin_explicit").first()
    with pytest.raises(HTTPException) as exc:
        resolve_authorized_client(db_session, admin, None)
    assert exc.value.status_code == 400


def test_resolve_client_not_found(db_session):
    from fastapi import HTTPException

    admin = db_session.query(User).filter(User.username == "admin_explicit").first()
    with pytest.raises(HTTPException) as exc:
        resolve_authorized_client(db_session, admin, 99999)
    assert exc.value.status_code == 404


def test_1_no_token_returns_401(client):
    r = client.get("/api/produtividade", params={"client_id": 2})
    assert r.status_code == 401


def test_2_alpha_access_own_ok(client):
    r = client.get(
        "/api/produtividade", params={"client_id": 2}, headers=_auth("user_alpha")
    )
    assert r.status_code == 200
    assert r.json().get("success") is True


def test_3_alpha_access_beta_forbidden(client):
    r = client.get(
        "/api/produtividade", params={"client_id": 4}, headers=_auth("user_alpha")
    )
    assert r.status_code == 403


def test_4_beta_access_own_ok(client):
    r = client.get(
        "/api/produtividade", params={"client_id": 4}, headers=_auth("user_beta")
    )
    assert r.status_code == 200


def test_5_beta_access_alpha_forbidden(client):
    r = client.get(
        "/api/produtividade", params={"client_id": 2}, headers=_auth("user_beta")
    )
    assert r.status_code == 403


def test_6_orphan_forbidden(client):
    r = client.get(
        "/api/produtividade", params={"client_id": 2}, headers=_auth("user_orphan")
    )
    assert r.status_code == 403


def test_7_admin_selected_client_ok(client):
    r = client.get(
        "/api/produtividade", params={"client_id": 2}, headers=_auth("admin_explicit")
    )
    assert r.status_code == 200
    r2 = client.get(
        "/api/produtividade", params={"client_id": 4}, headers=_auth("admin_explicit")
    )
    assert r2.status_code == 200


def test_8_omitted_client_id_no_fallback_one(client):
    r = client.get("/api/produtividade", headers=_auth("admin_explicit"))
    assert r.status_code in (400, 422)
    assert r.status_code != 200


def test_9_destructive_without_auth_401(client):
    r = client.delete("/api/clientes/2")
    assert r.status_code == 401
    r2 = client.delete("/api/uploads/1", params={"client_id": 2})
    assert r2.status_code == 401


def test_10_client_not_found_404(client):
    r = client.get(
        "/api/produtividade",
        params={"client_id": 99999},
        headers=_auth("admin_explicit"),
    )
    assert r.status_code == 404


def test_dados_todos_cross_tenant_403(client):
    r = client.get(
        "/api/dados/todos", params={"client_id": 4}, headers=_auth("user_alpha")
    )
    assert r.status_code == 403


def test_backup_list_requires_admin(client):
    r = client.get("/api/backup/list")
    assert r.status_code == 401
    r2 = client.get("/api/backup/list", headers=_auth("user_alpha"))
    assert r2.status_code == 403


def test_clone_requires_admin_and_origem(client):
    r = client.post(
        "/api/clientes/4/clonar_dados",
        params={"origem_id": 2},
        headers=_auth("user_alpha"),
    )
    assert r.status_code == 403
    r2 = client.post("/api/clientes/4/clonar_dados", headers=_auth("admin_explicit"))
    assert r2.status_code in (400, 422)


def test_listar_clientes_orphan_forbidden(client):
    """FIT-03: client_id NULL sem is_admin não lista todos — 403."""
    r = client.get("/api/clientes", headers=_auth("user_orphan"))
    assert r.status_code == 403


def test_listar_clientes_bound_only_own(client):
    r = client.get("/api/clientes", headers=_auth("user_alpha"))
    assert r.status_code == 200
    ids = {c["id"] for c in r.json()}
    assert ids == {2}


def test_listar_clientes_admin_sees_all(client):
    r = client.get("/api/clientes", headers=_auth("admin_explicit"))
    assert r.status_code == 200
    ids = {c["id"] for c in r.json()}
    assert 2 in ids and 4 in ids


def test_validar_acesso_null_without_admin_forbidden(db_session):
    from fastapi import HTTPException
    from backend.main import validar_acesso_client_id

    user = db_session.query(User).filter(User.username == "user_orphan").first()
    with pytest.raises(HTTPException) as exc:
        validar_acesso_client_id(user, 2)
    assert exc.value.status_code == 403


def test_anonymous_business_routes_401(client):
    """FIT-03 smoke: unprotected business routes require Bearer."""
    assert client.get("/api/clientes/1").status_code == 401
    assert client.get("/api/analises/setores", params={"client_id": 1}).status_code == 401
    assert client.get("/api/health").status_code == 200

