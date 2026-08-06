"""Tenant/auth adapter compatible with PR #4 — no parallel auth system.

When PR #4 tenant guard is merged, wire `resolve_tenant_context` to that implementation.
Until then, callers inject a context explicitly; routes refuse missing auth.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Protocol

from backend.ingestion.exceptions import AuthRequiredError, TenantGuardError


@dataclass(frozen=True)
class TenantContext:
    user_id: int | None
    username: str | None
    client_id: int
    role: str | None = None
    is_authenticated: bool = True


class TenantGuard(Protocol):
    def require_tenant(self, requested_client_id: int | None) -> TenantContext: ...


class ExplicitTenantGuard:
    """Test/dev guard: trusts only an explicitly provided authenticated context."""

    def __init__(self, context: TenantContext | None) -> None:
        self.context = context

    def require_tenant(self, requested_client_id: int | None) -> TenantContext:
        if self.context is None or not self.context.is_authenticated:
            raise AuthRequiredError("authentication required")
        if requested_client_id is not None and int(requested_client_id) != self.context.client_id:
            # Never trust frontend client_id over session tenant
            raise TenantGuardError("cross-tenant access blocked")
        return self.context


def assert_same_tenant(ctx: TenantContext, client_id: int) -> None:
    if ctx.client_id != client_id:
        raise TenantGuardError("tenant mismatch")


# Hook point for PR #4 integration:
# PR4_TENANT_GUARD_FACTORY: Callable[[Request], TenantGuard] | None = None
PR4_TENANT_GUARD_FACTORY: Callable[..., TenantGuard] | None = None
