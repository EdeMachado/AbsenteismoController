"""FIT-04 — exports require auth/tenant and no public cache."""
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
        u = session.query(User).filter(User.username == "user_alpha").first()
        u.client_id = 2
        u.is_admin = False
        u.is_active = True
        session.commit()
        yield client
    app.dependency_overrides.clear()
    session.close()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


def _h():
    return {"Authorization": f"Bearer {create_access_token({'sub': 'user_alpha'})}"}


def test_export_excel_anonymous_401():
    c = TestClient(app)
    r = c.get("/api/export/excel", params={"client_id": 2})
    assert r.status_code == 401


def test_export_excel_cross_tenant_403(client_env):
    r = client_env.get(
        "/api/export/excel", params={"client_id": 4}, headers=_h()
    )
    assert r.status_code == 403


def test_export_excel_own_tenant_cache_headers(client_env):
    r = client_env.get(
        "/api/export/excel", params={"client_id": 2}, headers=_h()
    )
    # May be 200 with file or 400/500 if empty data — must not be 401/403 for own tenant
    assert r.status_code != 401
    assert r.status_code != 403
    cc = r.headers.get("Cache-Control", "")
    assert "no-store" in cc or "no-cache" in cc or "private" in cc
