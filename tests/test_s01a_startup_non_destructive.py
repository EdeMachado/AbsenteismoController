"""
S01-A revisão — startup não destrutivo.
Banco temporário isolado; nomes fictícios.
"""
from __future__ import annotations

import os

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

os.environ["SECRET_KEY"] = "s01a-startup-test-secret"

from backend.database import Base
from backend.models import Client, User, Config
from backend.auth import get_password_hash, verify_password
from backend.main import apply_non_destructive_startup_seeds


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
            Client(id=2, nome="Tenant Alpha SA", nome_fantasia="Alpha", cnpj="11111111000111"),
            Client(id=4, nome="Tenant Beta SA", nome_fantasia="Beta", cnpj="22222222000122"),
        ]
    )
    session.flush()

    pwd_admin = get_password_hash("existing-admin-secret")
    session.add_all(
        [
            User(
                username="user_conver_ficticio",
                email="conver_ficticio@example.test",
                password_hash=get_password_hash("pass-conver"),
                is_active=True,
                is_admin=False,
                client_id=2,
            ),
            User(
                username="user_roda_ficticio",
                email="roda_ficticio@example.test",
                password_hash=get_password_hash("pass-roda"),
                is_active=True,
                is_admin=False,
                client_id=4,
            ),
            User(
                username="user_comum_ficticio",
                email="comum_ficticio@example.test",
                password_hash=get_password_hash("pass-comum"),
                is_active=True,
                is_admin=False,
                client_id=2,
            ),
            User(
                username="admin",
                email="admin@grupobiomed.com",
                password_hash=pwd_admin,
                is_active=True,
                is_admin=True,
                client_id=None,
            ),
        ]
    )
    session.commit()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


def _snapshot(db):
    rows = {}
    for u in db.query(User).all():
        rows[u.username] = {
            "client_id": u.client_id,
            "is_admin": u.is_admin,
            "password_hash": u.password_hash,
        }
    return rows


def test_startup_preserves_conver_client_id(db_session):
    before = _snapshot(db_session)
    apply_non_destructive_startup_seeds(db_session)
    after = _snapshot(db_session)
    assert after["user_conver_ficticio"]["client_id"] == 2
    assert after["user_conver_ficticio"]["client_id"] == before["user_conver_ficticio"]["client_id"]


def test_startup_preserves_roda_client_id(db_session):
    apply_non_destructive_startup_seeds(db_session)
    u = db_session.query(User).filter(User.username == "user_roda_ficticio").one()
    assert u.client_id == 4


def test_startup_does_not_promote_common_user(db_session):
    apply_non_destructive_startup_seeds(db_session)
    u = db_session.query(User).filter(User.username == "user_comum_ficticio").one()
    assert u.is_admin is False
    assert u.client_id == 2


def test_startup_does_not_reset_admin_password(db_session):
    before = db_session.query(User).filter(User.username == "admin").one().password_hash
    apply_non_destructive_startup_seeds(db_session)
    admin = db_session.query(User).filter(User.username == "admin").one()
    assert admin.password_hash == before
    assert verify_password("existing-admin-secret", admin.password_hash)


def test_startup_idempotent_twice(db_session):
    s1 = _snapshot(db_session)
    apply_non_destructive_startup_seeds(db_session)
    mid = _snapshot(db_session)
    apply_non_destructive_startup_seeds(db_session)
    s2 = _snapshot(db_session)
    assert mid == s2
    # vínculos originais intactos
    assert s2["user_conver_ficticio"]["client_id"] == s1["user_conver_ficticio"]["client_id"]
    assert s2["user_roda_ficticio"]["client_id"] == s1["user_roda_ficticio"]["client_id"]


def test_startup_can_create_missing_admin_without_touching_others(db_session):
    # remove admin existente
    admin = db_session.query(User).filter(User.username == "admin").one()
    db_session.delete(admin)
    db_session.commit()

    before_others = {
        u.username: (u.client_id, u.is_admin, u.password_hash)
        for u in db_session.query(User).all()
    }
    created = apply_non_destructive_startup_seeds(db_session)
    assert created["admin"] is True
    new_admin = db_session.query(User).filter(User.username == "admin").one()
    assert new_admin.is_admin is True

    for username, triple in before_others.items():
        u = db_session.query(User).filter(User.username == username).one()
        assert (u.client_id, u.is_admin, u.password_hash) == triple


def test_startup_never_clears_tenant_links(db_session):
    apply_non_destructive_startup_seeds(db_session)
    linked = (
        db_session.query(User)
        .filter(User.username.in_(["user_conver_ficticio", "user_roda_ficticio", "user_comum_ficticio"]))
        .all()
    )
    assert all(u.client_id is not None for u in linked)
    assert {u.client_id for u in linked} == {2, 4}
