"""Central authorization dependencies for legacy + foundation APIs (FIT-03).

Reuses PR #4 tenant rules via resolve_authorized_client / require_admin_user.
No parallel auth system.
"""

from __future__ import annotations

import os
from typing import Optional

from fastapi import Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.auth import get_current_active_user, get_current_user
from backend.database import get_db
from backend.models import Client, User
from backend.tenant import require_admin_user, resolve_authorized_client

# Intentional public API paths (method-agnostic path match).
PUBLIC_API_PATHS = frozenset(
    {
        "/api/auth/login",
        "/api/health",
    }
)

# Optional public paths controlled by env (default off in production-like).
def api_docs_enabled() -> bool:
    raw = (os.environ.get("ENABLE_API_DOCS") or "").strip().lower()
    if raw in {"1", "true", "yes", "on"}:
        return True
    if raw in {"0", "false", "no", "off"}:
        return False
    # Default: enabled only when ENVIRONMENT is development/staging
    env = (os.environ.get("ENVIRONMENT") or "production").strip().lower()
    return env in {"development", "dev", "staging", "test", "local"}


def require_authenticated_user(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """Authenticated active user (alias for clarity in route signatures)."""
    return current_user


def require_admin(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """Explicit is_admin=True required."""
    return require_admin_user(current_user)


def require_tenant_client(
    client_id: int = Query(..., description="ID do cliente (obrigatório)"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Client:
    """
    Resolve authorized tenant for query-param client_id routes.
    Non-admin: client_id must match user.client_id.
    Admin: explicit client_id required (no fallback).
    """
    return resolve_authorized_client(db, current_user, client_id)


def assert_tenant_access(
    db: Session,
    current_user: User,
    requested_client_id: Optional[int],
) -> Client:
    """Programmatic tenant assert (path params / body)."""
    return resolve_authorized_client(db, current_user, requested_client_id)


def is_public_api_path(path: str) -> bool:
    if path in PUBLIC_API_PATHS:
        return True
    # login variants
    if path.rstrip("/") == "/api/auth/login":
        return True
    if path.rstrip("/") == "/api/health":
        return True
    return False
