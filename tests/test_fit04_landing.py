"""FIT-04 — landing institutional (Alt. A); cadastro-empresa stays admin-only."""
from __future__ import annotations

import os
from pathlib import Path

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

FRONTEND = Path(__file__).resolve().parents[1] / "frontend"


def test_landing_html_has_no_cadastro_api_call():
    text = (FRONTEND / "landing.html").read_text(encoding="utf-8")
    assert "/api/cadastro-empresa" not in text
    assert "abrirModalContato" in text
    assert "Contato comercial" in text or "contato comercial" in text.lower()


def test_anonymous_cadastro_empresa_still_401():
    client = TestClient(app)
    r = client.post(
        "/api/cadastro-empresa",
        json={
            "nome_empresa": "Fake SA",
            "cnpj": "00.000.000/0000-00",
            "endereco": "Rua X",
            "telefone": "(00) 0000-0000",
        },
    )
    assert r.status_code == 401


@pytest.fixture()
def admin_client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    session = Session()
    session.add(Client(id=2, nome="Alpha", situacao="ativo"))
    session.add(
        User(
            username="admin_explicit",
            email="admin@fit04.test",
            password_hash=get_password_hash("pass-admin"),
            is_active=True,
            is_admin=True,
            client_id=None,
        )
    )
    session.add(
        User(
            username="user_alpha",
            email="alpha@fit04.test",
            password_hash=get_password_hash("pass-alpha"),
            is_active=True,
            is_admin=False,
            client_id=2,
        )
    )
    session.commit()

    def _override():
        try:
            yield session
        finally:
            pass

    app.dependency_overrides[get_db] = _override
    with TestClient(app) as c:
        admin = session.query(User).filter(User.username == "admin_explicit").first()
        admin.is_admin = True
        admin.is_active = True
        session.commit()
        yield c, session
    app.dependency_overrides.clear()
    session.close()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


def test_non_admin_cadastro_empresa_403(admin_client):
    client, _ = admin_client
    token = create_access_token({"sub": "user_alpha"})
    r = client.post(
        "/api/cadastro-empresa",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "nome_empresa": "Fake SA",
            "cnpj": "11.111.111/0001-11",
            "endereco": "Rua Y",
            "telefone": "(11) 1111-1111",
        },
    )
    assert r.status_code == 403
