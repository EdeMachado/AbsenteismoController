"""Wire PR #4 JWT/session auth into Epic 1 ingestion tenant guard.

No browser identity headers. No parallel auth. Fail-closed without Bearer token.
"""

from __future__ import annotations

from typing import Any, Optional

from jose import JWTError, jwt
from sqlalchemy.orm import Session

from backend.auth import ALGORITHM, SECRET_KEY
from backend import database as database_module
from backend.ingestion.exceptions import AuthRequiredError, TenantGuardError
from backend.ingestion.tenant_adapter import TenantContext, TenantGuard
from backend.models import User
from backend.tenant import resolve_authorized_client


class Pr4RequestTenantGuard:
    """Resolves tenant from Authorization Bearer + PR #4 resolve_authorized_client."""

    def __init__(self, request: Any) -> None:
        self.request = request

    def _extract_bearer(self) -> Optional[str]:
        auth = None
        if hasattr(self.request, "headers"):
            auth = self.request.headers.get("Authorization") or self.request.headers.get(
                "authorization"
            )
        if not auth or not isinstance(auth, str):
            return None
        parts = auth.split(None, 1)
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return None
        return parts[1].strip() or None

    def _load_user(self, db: Session) -> User:
        token = self._extract_bearer()
        if not token:
            raise AuthRequiredError("authentication required")
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username = payload.get("sub")
            if not username:
                raise AuthRequiredError("authentication required")
        except JWTError as exc:
            raise AuthRequiredError("invalid or expired token") from exc
        user = db.query(User).filter(User.username == username).first()
        if user is None or not user.is_active:
            raise AuthRequiredError("authentication required")
        return user

    def require_tenant(self, requested_client_id: int | None) -> TenantContext:
        # Resolve SessionLocal at call time (supports staging DB rebind).
        db = database_module.SessionLocal()
        try:
            user = self._load_user(db)
            try:
                client = resolve_authorized_client(db, user, requested_client_id)
            except Exception as exc:
                # Map FastAPI HTTPException from tenant guard
                status_code = getattr(exc, "status_code", None)
                if status_code == 401:
                    raise AuthRequiredError("authentication required") from exc
                if status_code in {403, 404, 400}:
                    detail = getattr(exc, "detail", "tenant access denied")
                    raise TenantGuardError(str(detail)) from exc
                raise
            return TenantContext(
                user_id=int(user.id) if user.id is not None else None,
                username=str(user.username) if user.username else None,
                client_id=int(client.id),
                role="admin" if getattr(user, "is_admin", False) else "user",
                is_authenticated=True,
                is_global_admin=bool(getattr(user, "is_admin", False)),
            )
        finally:
            db.close()


def pr4_tenant_guard_factory(request: Any) -> TenantGuard:
    return Pr4RequestTenantGuard(request)


def wire_pr4_tenant_guard() -> None:
    """Connect PR #4 factory for ingestion HTTP (idempotent)."""
    from backend.ingestion.tenant_adapter import set_pr4_tenant_guard_factory

    set_pr4_tenant_guard_factory(pr4_tenant_guard_factory)
