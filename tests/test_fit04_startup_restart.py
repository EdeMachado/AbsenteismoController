"""FIT-04 — startup seed is non-destructive across repeated invocations."""
from __future__ import annotations

import os

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

os.environ["SECRET_KEY"] = "fit04-test-secret-key-not-for-production"
os.environ.setdefault("ENVIRONMENT", "test")
os.environ["ENABLE_INTELLIGENT_INGESTION"] = "false"
os.environ["ENABLE_BIOMED_PERFORMANCE_ENGINE"] = "false"

from backend.auth import get_password_hash
from backend.database import Base
from backend.main import apply_non_destructive_startup_seeds
from backend.models import Client, Produtividade, Upload, User


def _user_row(session, username: str):
    u = session.query(User).filter(User.username == username).first()
    return (u.username, u.client_id, bool(u.is_admin), bool(u.is_active), u.password_hash)


def test_startup_seed_three_times_preserves_tenants_and_hashes():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    session = Session()
    try:
        session.add_all(
            [
                Client(id=2, nome="Alpha", situacao="ativo"),
                Client(id=4, nome="Beta", situacao="ativo"),
            ]
        )
        hash_a = get_password_hash("pass-a-stable")
        hash_adm = get_password_hash("pass-adm-stable")
        session.add_all(
            [
                User(
                    username="user_a",
                    email="a@fit04.test",
                    password_hash=hash_a,
                    is_active=True,
                    is_admin=False,
                    client_id=2,
                ),
                User(
                    username="admin_rc",
                    email="adm@fit04.test",
                    password_hash=hash_adm,
                    is_active=True,
                    is_admin=True,
                    client_id=None,
                ),
            ]
        )
        session.add(Upload(client_id=2, filename="a.xlsx", mes_referencia="2026-01"))
        session.add(
            Produtividade(
                client_id=2, mes_referencia="2026-01", numero_tipo="1", total=5
            )
        )
        session.commit()

        before_users = [_user_row(session, "user_a"), _user_row(session, "admin_rc")]
        before_clients = sorted(
            (c.id, c.nome) for c in session.query(Client).all()
        )
        before_uploads = session.query(Upload).count()
        before_prod = session.query(Produtividade).count()

        for _ in range(3):
            apply_non_destructive_startup_seeds(session)
            session.commit()

        after_users = [_user_row(session, "user_a"), _user_row(session, "admin_rc")]
        after_clients = sorted((c.id, c.nome) for c in session.query(Client).all())

        assert after_users == before_users
        assert after_clients == before_clients
        assert session.query(Upload).count() == before_uploads
        assert session.query(Produtividade).count() == before_prod
        # Must not invent default admin password user
        assert session.query(User).filter(User.username == "admin").first() is None
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()
