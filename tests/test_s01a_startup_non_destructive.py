"""
S01-A — startup não destrutivo e sem admin/admin123.
Banco temporário isolado; nomes fictícios.
"""
from __future__ import annotations

import inspect
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
    assert s2["user_conver_ficticio"]["client_id"] == s1["user_conver_ficticio"]["client_id"]
    assert s2["user_roda_ficticio"]["client_id"] == s1["user_roda_ficticio"]["client_id"]


def test_startup_never_clears_tenant_links(db_session):
    apply_non_destructive_startup_seeds(db_session)
    linked = (
        db_session.query(User)
        .filter(User.username.in_(["user_conver_ficticio", "user_roda_ficticio", "user_comum_ficticio"]))
        .all()
    )
    assert all(u.client_id is not None for u in linked)
    assert {u.client_id for u in linked} == {2, 4}


def test_startup_empty_users_does_not_create_admin(db_session):
    db_session.query(User).delete()
    db_session.commit()
    assert db_session.query(User).count() == 0
    created = apply_non_destructive_startup_seeds(db_session)
    assert created["admin"] is False
    assert created["admin_missing_warned"] is True
    assert db_session.query(User).count() == 0


def test_startup_existing_admin_untouched(db_session):
    before = _snapshot(db_session)["admin"]
    created = apply_non_destructive_startup_seeds(db_session)
    assert created["admin"] is False
    after = _snapshot(db_session)["admin"]
    assert after == before


def test_startup_common_user_only_not_promoted():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    session = Session()
    session.add(Client(id=2, nome="Tenant Alpha SA", cnpj="11111111000111"))
    session.add(
        User(
            username="only_common",
            email="only_common@example.test",
            password_hash=get_password_hash("x"),
            is_active=True,
            is_admin=False,
            client_id=2,
        )
    )
    session.commit()
    try:
        created = apply_non_destructive_startup_seeds(session)
        u = session.query(User).filter(User.username == "only_common").one()
        assert u.is_admin is False
        assert u.client_id == 2
        assert created["admin"] is False
        assert session.query(User).filter(User.is_admin == True).count() == 0  # noqa: E712
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


def test_startup_source_has_no_admin123():
    src = inspect.getsource(apply_non_destructive_startup_seeds)
    assert "admin123" not in src
    assert "get_password_hash" not in src


def test_startup_configs_without_creating_user(db_session):
    db_session.query(User).delete()
    db_session.query(Config).delete()
    db_session.commit()
    created = apply_non_destructive_startup_seeds(db_session)
    assert created["admin"] is False
    assert db_session.query(User).count() == 0
    assert created["configs"] >= 1
    assert db_session.query(Config).filter(Config.chave == "nome_sistema").first() is not None
