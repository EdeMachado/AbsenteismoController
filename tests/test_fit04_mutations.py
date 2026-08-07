"""FIT-04 — mutation auth/tenant on synthetic DB (no cross-tenant writes)."""
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
from backend.models import Client, Produtividade, User


@pytest.fixture()
def env():
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
            Client(id=2, nome="Tenant Alpha SA", situacao="ativo"),
            Client(id=4, nome="Tenant Beta SA", situacao="ativo"),
        ]
    )
    session.add_all(
        [
            User(
                username="user_alpha",
                email="a@fit04.test",
                password_hash=get_password_hash("p"),
                is_active=True,
                is_admin=False,
                client_id=2,
            ),
            User(
                username="admin_explicit",
                email="adm@fit04.test",
                password_hash=get_password_hash("p"),
                is_active=True,
                is_admin=True,
                client_id=None,
            ),
        ]
    )
    session.add(
        Produtividade(
            client_id=2, mes_referencia="2026-02", numero_tipo="1", tipo_consulta="X", total=1
        )
    )
    session.commit()

    def _override():
        try:
            yield session
        finally:
            pass

    app.dependency_overrides[get_db] = _override
    with TestClient(app) as client:
        for u in session.query(User).all():
            if u.username == "admin_explicit":
                u.is_admin = True
                u.client_id = None
            elif u.username == "user_alpha":
                u.is_admin = False
                u.client_id = 2
            u.is_active = True
        session.commit()
        yield client, session
    app.dependency_overrides.clear()
    session.close()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


def _h(user: str) -> dict:
    return {"Authorization": f"Bearer {create_access_token({'sub': user})}"}


def test_create_cliente_requires_admin(env):
    client, session = env
    payload = {"nome": "Nova Empresa", "situacao": "ativo"}
    r = client.post("/api/clientes", json=payload, headers=_h("user_alpha"))
    assert r.status_code == 403
    before = session.query(Client).count()
    r2 = client.post("/api/clientes", json=payload, headers=_h("admin_explicit"))
    assert r2.status_code == 200
    session.expire_all()
    assert session.query(Client).count() == before + 1


def test_produtividade_post_own_tenant(env):
    client, session = env
    body = {
        "client_id": 2,
        "mes_referencia": "2026-03",
        "registros": [
            {
                "numero_tipo": "2",
                "tipo_consulta": "Y",
                "ocupacionais": 1,
                "assistenciais": 0,
                "acidente_trabalho": 0,
                "inss": 0,
                "sinistralidade": 0,
                "absenteismo": 0,
                "pericia_indireta": 0,
            }
        ],
    }
    r = client.post("/api/produtividade", json=body, headers=_h("user_alpha"))
    assert r.status_code == 200
    # cross-tenant create
    body["client_id"] = 4
    r2 = client.post("/api/produtividade", json=body, headers=_h("user_alpha"))
    assert r2.status_code == 403
    assert session.query(Produtividade).filter(Produtividade.client_id == 4).count() == 0


def test_clone_requires_admin(env):
    client, _ = env
    r = client.post(
        "/api/clientes/4/clonar_dados",
        params={"origem_id": 2},
        headers=_h("user_alpha"),
    )
    assert r.status_code == 403


def test_delete_cliente_requires_admin_and_confirmation(env):
    client, session = env
    # create empty client via admin
    r = client.post(
        "/api/clientes",
        json={"nome": "Temp Del", "situacao": "ativo"},
        headers=_h("admin_explicit"),
    )
    assert r.status_code == 200
    cid = r.json()["id"]
    r2 = client.delete(f"/api/clientes/{cid}", headers=_h("user_alpha"))
    assert r2.status_code == 403
    r3 = client.delete(f"/api/clientes/{cid}", headers=_h("admin_explicit"))
    assert r3.status_code == 200
    session.expire_all()
    assert session.query(Client).filter(Client.id == cid).first() is None
