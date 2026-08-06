"""FIT-04 — basic multi-session tenant isolation (synthetic)."""
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
from backend.models import Client, User


@pytest.fixture()
def client_env():
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
            Client(id=2, nome="Alpha", situacao="ativo"),
            Client(id=4, nome="Beta", situacao="ativo"),
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
                username="user_beta",
                email="b@fit04.test",
                password_hash=get_password_hash("p"),
                is_active=True,
                is_admin=False,
                client_id=4,
            ),
        ]
    )
    session.commit()

    def _override():
        try:
            yield session
        finally:
            pass

    app.dependency_overrides[get_db] = _override
    with TestClient(app) as client:
        for name, cid in [("user_alpha", 2), ("user_beta", 4)]:
            u = session.query(User).filter(User.username == name).first()
            u.client_id = cid
            u.is_admin = False
            u.is_active = True
        session.commit()
        yield client
    app.dependency_overrides.clear()
    session.close()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


def test_parallel_tenant_sessions_isolated(client_env):
    """Sequential multi-session checks (SQLite StaticPool is not thread-safe)."""
    ha = {"Authorization": f"Bearer {create_access_token({'sub': 'user_alpha'})}"}
    hb = {"Authorization": f"Bearer {create_access_token({'sub': 'user_beta'})}"}

    assert client_env.get("/api/clientes", headers=ha).status_code == 200
    assert client_env.get("/api/clientes", headers=hb).status_code == 200
    assert (
        client_env.get("/api/dados/todos", params={"client_id": 2}, headers=ha).status_code
        == 200
    )
    assert (
        client_env.get("/api/dados/todos", params={"client_id": 4}, headers=hb).status_code
        == 200
    )
    assert (
        client_env.get("/api/dados/todos", params={"client_id": 4}, headers=ha).status_code
        == 403
    )
    assert (
        client_env.get("/api/dados/todos", params={"client_id": 2}, headers=hb).status_code
        == 403
    )


def test_invalid_token_401(client_env):
    r = client_env.get(
        "/api/clientes", headers={"Authorization": "Bearer totally-invalid"}
    )
    assert r.status_code == 401
