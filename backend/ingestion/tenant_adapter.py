"""Tenant/auth adapter for Epic 1 — fail-closed; no parallel auth; no browser identity headers.

Wire `set_pr4_tenant_guard_factory` when PR #4 is merged. Until then, HTTP routes
must not operate (503). Unit tests may inject TenantContext via FastAPI dependency
overrides or ExplicitTenantGuard — never via public HTTP headers.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Callable, Protocol

from backend.ingestion.exceptions import AuthRequiredError, TenantGuardError

FEATURE_TEST_DEPS_ENV = "INGESTION_ALLOW_TEST_DEPENDENCIES"


@dataclass(frozen=True)
class TenantContext:
    user_id: int | None
    username: str | None
    client_id: int
    role: str | None = None
    is_authenticated: bool = True
    is_global_admin: bool = False


class TenantGuard(Protocol):
    def require_tenant(self, requested_client_id: int | None) -> TenantContext: ...


class ExplicitTenantGuard:
    """
    Test-only / explicit-injection guard.
    Trusts a pre-built TenantContext — never constructed from browser headers.
    Global-admin policy mirrors PR #4 intent: may operate on an explicit requested client.
    """

    def __init__(self, context: TenantContext | None) -> None:
        self.context = context

    def require_tenant(self, requested_client_id: int | None) -> TenantContext:
        if self.context is None or not self.context.is_authenticated:
            raise AuthRequiredError("authentication required")
        if requested_client_id is None:
            return self.context
        req = int(requested_client_id)
        if req == self.context.client_id:
            return self.context
        if self.context.is_global_admin:
            return TenantContext(
                user_id=self.context.user_id,
                username=self.context.username,
                client_id=req,
                role=self.context.role,
                is_authenticated=True,
                is_global_admin=True,
            )
        raise TenantGuardError("cross-tenant access blocked")


def assert_same_tenant(ctx: TenantContext, client_id: int) -> None:
    if ctx.client_id != client_id:
        raise TenantGuardError("tenant mismatch")


_PR4_TENANT_GUARD_FACTORY: Callable[[Any], TenantGuard] | None = None


def set_pr4_tenant_guard_factory(factory: Callable[[Any], TenantGuard] | None) -> None:
    """Register PR #4 guard factory. Pass None to disconnect (fail-closed)."""
    global _PR4_TENANT_GUARD_FACTORY
    _PR4_TENANT_GUARD_FACTORY = factory


def get_pr4_tenant_guard_factory() -> Callable[[Any], TenantGuard] | None:
    return _PR4_TENANT_GUARD_FACTORY


def allow_test_dependencies() -> bool:
    """Explicit test harness only — never a production fallback."""
    raw = (os.environ.get(FEATURE_TEST_DEPS_ENV) or "false").strip().lower()
    return raw in {"1", "true", "yes", "on"}


def is_ingestion_auth_available() -> bool:
    """True when PR #4 factory is connected (or test deps flag for harness wiring)."""
    if get_pr4_tenant_guard_factory() is not None:
        return True
    return allow_test_dependencies()


def require_ingestion_tenant(
    request: Any,
    requested_client_id: int | None = None,
) -> TenantContext:
    """
    Fail-closed tenant resolution for HTTP ingestion routes.

    Without PR #4 factory → AuthRequiredError (mapped to 503 at HTTP boundary).
    Never reads X-Ingestion-* or any browser identity header.
    """
    factory = get_pr4_tenant_guard_factory()
    if factory is None:
        raise AuthRequiredError("ingestion authentication unavailable")
    guard = factory(request)
    return guard.require_tenant(requested_client_id)
