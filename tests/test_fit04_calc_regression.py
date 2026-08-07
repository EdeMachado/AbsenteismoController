"""FIT-04 — security gate must not alter aggregation formulas (synthetic)."""
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
def client_env():
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
            username="user_alpha",
            email="a@fit04.test",
            password_hash=get_password_hash("p"),
            is_active=True,
            is_admin=False,
            client_id=2,
        )
    )
    up = Upload(client_id=2, filename="a.xlsx", mes_referencia="2026-01", total_registros=2)
    session.add(up)
    session.flush()
    session.add_all(
        [
            Atestado(
                upload_id=up.id,
                nome_funcionario="A1",
                setor="S1",
                dias_perdidos=2,
                horas_perdidas=16,
                dias_atestados=2,
                horas_perdi=16,
            ),
            Atestado(
                upload_id=up.id,
                nome_funcionario="A2",
                setor="S1",
                dias_perdidos=1,
                horas_perdidas=8,
                dias_atestados=1,
                horas_perdi=8,
            ),
        ]
    )
    session.add(
        Produtividade(
            client_id=2,
            mes_referencia="2026-01",
            numero_tipo="1",
            tipo_consulta="Consulta",
            ocupacionais=3,
            total=3,
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
        u = session.query(User).filter(User.username == "user_alpha").first()
        u.client_id = 2
        u.is_admin = False
        u.is_active = True
        session.commit()
        yield client, session
    app.dependency_overrides.clear()
    session.close()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


def _h():
    return {"Authorization": f"Bearer {create_access_token({'sub': 'user_alpha'})}"}


def test_dashboard_and_dados_aggregates_stable(client_env):
    client, _ = client_env
    dash = client.get("/api/dashboard", params={"client_id": 2}, headers=_h())
    assert dash.status_code == 200
    body = dash.json()
    # Snapshot keys used by frontend — values must be consistent for synthetic set
    assert isinstance(body, dict)
    dados = client.get("/api/dados/todos", params={"client_id": 2}, headers=_h())
    assert dados.status_code == 200
    d = dados.json()
    stats = d.get("estatisticas") or {}
    assert stats.get("total_registros") == 2
    # dias_atestados sum = 3
    assert float(stats.get("total_atestados_dias") or 0) == 3.0

    prod = client.get("/api/produtividade", params={"client_id": 2}, headers=_h())
    assert prod.status_code == 200
    pbody = prod.json()
    assert pbody.get("success") is True
    rows = pbody.get("data") or pbody.get("registros") or []
    totals = [r.get("total") for r in rows if isinstance(r, dict)]
    assert 3 in totals

    # Second call identical (middleware must not alter formulas)
    dash2 = client.get("/api/dashboard", params={"client_id": 2}, headers=_h())
    assert dash2.json() == body
