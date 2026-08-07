"""FIT-02: PR #4 bridge for ingestion tenant guard (disposable DB only)."""

from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from starlette.requests import Request

from backend.auth import create_access_token, get_password_hash
from backend.ingestion.exceptions import AuthRequiredError, TenantGuardError
from backend.ingestion.pr4_bridge import Pr4RequestTenantGuard, wire_pr4_tenant_guard
from backend.ingestion.tenant_adapter import (
    get_pr4_tenant_guard_factory,
    set_pr4_tenant_guard_factory,
)
from backend.models import Client, User


@pytest.fixture()
def bridge_db(tmp_path, monkeypatch):
    import backend.database as database
    from backend.database import Base

    db_path = tmp_path / "pr4_bridge.sqlite"
    monkeypatch.setenv("ABSENTEISMO_SQLITE_PATH", str(db_path))
    database.DB_PATH = str(db_path)
    database.SQLALCHEMY_DATABASE_URL = f"sqlite:///{db_path}"
    database.engine = create_engine(
        database.SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False},
    )
    database.SessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=database.engine
    )
    Base.metadata.create_all(bind=database.engine)

    cid = 9101
    db = database.SessionLocal()
    db.add(Client(id=cid, nome="Bridge Cliente", nome_fantasia="Bridge"))
    db.add(
        User(
            username="bridge_user",
            email="bridge@fit02.test",
            password_hash=get_password_hash("bridge-pass"),
            is_admin=False,
            is_active=True,
            client_id=cid,
        )
    )
    db.commit()
    db.close()
    yield cid
    set_pr4_tenant_guard_factory(None)


def _request_with_auth(token: str | None) -> Request:
    headers = []
    if token:
        headers.append((b"authorization", f"Bearer {token}".encode("utf-8")))
    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": "/",
        "raw_path": b"/",
        "query_string": b"",
        "headers": headers,
        "client": ("127.0.0.1", 123),
        "server": ("test", 80),
    }
    return Request(scope)


def test_wire_pr4_sets_factory():
    set_pr4_tenant_guard_factory(None)
    wire_pr4_tenant_guard()
    assert get_pr4_tenant_guard_factory() is not None
    set_pr4_tenant_guard_factory(None)


def test_pr4_guard_requires_bearer(bridge_db):
    guard = Pr4RequestTenantGuard(_request_with_auth(None))
    with pytest.raises(AuthRequiredError):
        guard.require_tenant(bridge_db)


def test_pr4_guard_happy_path(bridge_db):
    token = create_access_token({"sub": "bridge_user"})
    guard = Pr4RequestTenantGuard(_request_with_auth(token))
    ctx = guard.require_tenant(bridge_db)
    assert ctx.client_id == bridge_db
    assert ctx.username == "bridge_user"


def test_pr4_guard_blocks_cross_tenant(bridge_db):
    token = create_access_token({"sub": "bridge_user"})
    guard = Pr4RequestTenantGuard(_request_with_auth(token))
    with pytest.raises(TenantGuardError):
        guard.require_tenant(bridge_db + 1)
