"""FIT-04 — cross-tenant access by resource ID (not only query client_id)."""
from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

os.environ["SECRET_KEY"] = "fit04-test-secret-key-not-for-production"
os.environ.setdefault("ENVIRONMENT", "test")

from backend.auth import create_access_token, get_password_hash
from backend.database import Base, get_db
from backend.main import app
from backend.models import Atestado, Client, Produtividade, Upload, User


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
    session.add_all(
        [
            Client(id=2, nome="Tenant Alpha SA", nome_fantasia="Alpha", situacao="ativo"),
            Client(id=4, nome="Tenant Beta SA", nome_fantasia="Beta", situacao="ativo"),
        ]
    )
    session.flush()
    session.add_all(
        [
            User(
                username="user_alpha",
                email="alpha@fit04.test",
                password_hash=get_password_hash("pass-alpha"),
                is_active=True,
                is_admin=False,
                client_id=2,
            ),
            User(
                username="user_beta",
                email="beta@fit04.test",
                password_hash=get_password_hash("pass-beta"),
                is_active=True,
                is_admin=False,
                client_id=4,
            ),
            User(
                username="user_orphan",
                email="orphan@fit04.test",
                password_hash=get_password_hash("pass-orphan"),
                is_active=True,
                is_admin=False,
                client_id=None,
            ),
            User(
                username="user_inactive",
                email="inactive@fit04.test",
                password_hash=get_password_hash("pass-inactive"),
                is_active=False,
                is_admin=False,
                client_id=2,
            ),
            User(
                username="admin_explicit",
                email="admin@fit04.test",
                password_hash=get_password_hash("pass-admin"),
                is_active=True,
                is_admin=True,
                client_id=None,
            ),
        ]
    )
    up_a = Upload(client_id=2, filename="alpha.xlsx", mes_referencia="2026-01", total_registros=1)
    up_b = Upload(client_id=4, filename="beta.xlsx", mes_referencia="2026-01", total_registros=1)
    session.add_all([up_a, up_b])
    session.flush()
    at_a = Atestado(
        upload_id=up_a.id,
        nome_funcionario="Func Alpha",
        setor="Prod",
        dias_perdidos=1,
        horas_perdidas=8,
    )
    at_b = Atestado(
        upload_id=up_b.id,
        nome_funcionario="Func Beta",
        setor="Admin",
        dias_perdidos=2,
        horas_perdidas=16,
    )
    session.add_all([at_a, at_b])
    prod_a = Produtividade(
        client_id=2, mes_referencia="2026-01", numero_tipo="1", tipo_consulta="A", total=10
    )
    prod_b = Produtividade(
        client_id=4, mes_referencia="2026-01", numero_tipo="1", tipo_consulta="B", total=20
    )
    session.add_all([prod_a, prod_b])
    session.commit()
    # stash ids
    session.info["ids"] = {
        "upload_a": up_a.id,
        "upload_b": up_b.id,
        "atestado_a": at_a.id,
        "atestado_b": at_b.id,
        "prod_a": prod_a.id,
        "prod_b": prod_b.id,
    }
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture()
def client(db_session):
    def _override():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override
    with TestClient(app) as c:
        for username, cid in [("user_alpha", 2), ("user_beta", 4), ("user_orphan", None)]:
            u = db_session.query(User).filter(User.username == username).first()
            if u:
                u.client_id = cid
                u.is_admin = False
                u.is_active = True
        inactive = db_session.query(User).filter(User.username == "user_inactive").first()
        if inactive:
            inactive.is_active = False
            inactive.client_id = 2
        admin = db_session.query(User).filter(User.username == "admin_explicit").first()
        if admin:
            admin.is_admin = True
            admin.client_id = None
            admin.is_active = True
        db_session.commit()
        yield c
    app.dependency_overrides.clear()


def _auth(username: str) -> dict:
    return {"Authorization": f"Bearer {create_access_token({'sub': username})}"}


def test_cliente_cross_tenant_403(client):
    r = client.get("/api/clientes/4", headers=_auth("user_alpha"))
    assert r.status_code == 403


def test_upload_preview_cross_tenant(client, db_session):
    ids = db_session.info["ids"]
    # forged client_id matching own tenant but foreign upload
    r = client.get(
        f"/api/preview/{ids['upload_b']}",
        params={"client_id": 2},
        headers=_auth("user_alpha"),
    )
    assert r.status_code == 404
    # foreign client_id
    r2 = client.get(
        f"/api/preview/{ids['upload_b']}",
        params={"client_id": 4},
        headers=_auth("user_alpha"),
    )
    assert r2.status_code == 403


def test_delete_upload_cross_tenant(client, db_session):
    ids = db_session.info["ids"]
    r = client.delete(
        f"/api/uploads/{ids['upload_b']}",
        params={"client_id": 4},
        headers=_auth("user_alpha"),
    )
    assert r.status_code == 403
    # still exists
    assert db_session.query(Upload).filter(Upload.id == ids["upload_b"]).first() is not None


def test_produtividade_id_cross_tenant(client, db_session):
    ids = db_session.info["ids"]
    r = client.put(
        f"/api/produtividade/{ids['prod_b']}",
        json={"ocupacionais": 99},
        headers=_auth("user_alpha"),
    )
    assert r.status_code == 403
    r2 = client.delete(
        f"/api/produtividade/{ids['prod_b']}",
        params={"client_id": 4},
        headers=_auth("user_alpha"),
    )
    assert r2.status_code == 403


def test_atestado_id_cross_tenant_without_query(client, db_session):
    ids = db_session.info["ids"]
    r = client.get(f"/api/dados/{ids['atestado_b']}", headers=_auth("user_alpha"))
    assert r.status_code == 403
    r2 = client.get(f"/api/dados/{ids['atestado_a']}", headers=_auth("user_alpha"))
    assert r2.status_code == 200
    assert r2.json().get("nome_funcionario") == "Func Alpha"


def test_funcionario_perfil_cross_tenant(client):
    r = client.get(
        "/api/funcionario/perfil",
        params={"client_id": 4, "nome": "Func Beta"},
        headers=_auth("user_alpha"),
    )
    assert r.status_code == 403


def test_orphan_business_403(client):
    r = client.get("/api/clientes", headers=_auth("user_orphan"))
    assert r.status_code == 403
    r2 = client.get(
        "/api/dados/todos", params={"client_id": 2}, headers=_auth("user_orphan")
    )
    assert r2.status_code == 403


def test_inactive_user_blocked(client):
    # login
    r = client.post(
        "/api/auth/login",
        data={"username": "user_inactive", "password": "pass-inactive"},
    )
    assert r.status_code in (401, 403)
    # forged token for inactive user → middleware 401
    r2 = client.get("/api/clientes", headers=_auth("user_inactive"))
    assert r2.status_code == 401


def test_admin_can_read_both_resources(client, db_session):
    ids = db_session.info["ids"]
    r = client.get(f"/api/dados/{ids['atestado_b']}", headers=_auth("admin_explicit"))
    assert r.status_code == 200
    r2 = client.get(
        f"/api/preview/{ids['upload_a']}",
        params={"client_id": 2},
        headers=_auth("admin_explicit"),
    )
    assert r2.status_code == 200
