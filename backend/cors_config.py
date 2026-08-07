"""CORS origin policy by environment (FIT-04).

Production: no wildcard; only explicit CORS_ALLOWED_ORIGINS.
Staging/dev/test: configurable list; empty → same-origin only (no "*").
"""

from __future__ import annotations

import os
from typing import List


def app_environment() -> str:
    return (os.environ.get("ENVIRONMENT") or "production").strip().lower()


def is_production_like() -> bool:
    return app_environment() in {"production", "prod"}


def cors_allowed_origins() -> List[str]:
    """
    Resolve allowed CORS origins.

    - CORS_ALLOWED_ORIGINS: comma-separated list (optional)
    - Production: requires explicit origins; never returns "*"
    - Non-production: if unset, returns [] (same-origin / TestClient still works)
    """
    raw = (os.environ.get("CORS_ALLOWED_ORIGINS") or "").strip()
    if raw:
        origins = [o.strip() for o in raw.split(",") if o.strip()]
        if is_production_like() and ("*" in origins or any(o == "*" for o in origins)):
            raise RuntimeError(
                "CORS_ALLOWED_ORIGINS must not contain '*' in production"
            )
        return origins

    if is_production_like():
        # Same-origin FastAPI+static deployment: empty list disables cross-origin.
        return []

    # Staging/local: no silent wildcard; configure CORS_ALLOWED_ORIGINS if needed.
    return []


def cors_allow_credentials() -> bool:
    origins = cors_allowed_origins()
    # credentials + "*" is invalid; with empty origins, credentials unused
    return bool(origins) and "*" not in origins
