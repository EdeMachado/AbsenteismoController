"""Preview / homologation surface gate (RC-1.5).

Fail-closed in production: no public preview HTML, staging aliases,
synthetic digital-form APIs, or employee demo entry without explicit enable.
"""

from __future__ import annotations

import os

PREVIEW_SURFACES_FLAG = "ENABLE_PREVIEW_SURFACES"


def app_environment() -> str:
    return (os.environ.get("ENVIRONMENT") or "production").strip().lower()


def is_production_like() -> bool:
    return app_environment() in {"production", "prod"}


def preview_surfaces_enabled() -> bool:
    """Homologation/preview surfaces.

    Explicit ENABLE_PREVIEW_SURFACES wins.
    Default: OFF in production/prod; ON in development/dev/staging/test/local.
    """
    raw = (os.environ.get(PREVIEW_SURFACES_FLAG) or "").strip().lower()
    if raw in {"1", "true", "yes", "on"}:
        return True
    if raw in {"0", "false", "no", "off"}:
        return False
    return app_environment() in {"development", "dev", "staging", "test", "testing", "local"}


def is_preview_homologation_path(path: str) -> bool:
    """Homologation / synthetic surfaces only.

    Exact ``/preview`` is the legacy upload-preview HTML page (production).
    Homologation lives under ``/preview/...``.
    ``/api/preview/{upload_id}`` is authenticated legacy preview — not gated here.
    """
    p = path or ""
    if p.startswith("/preview/"):
        return True
    if p.startswith("/staging/"):
        return True
    if p.startswith("/api/preview/ficha"):
        return True
    # Employee demo entry for digital form (opaque token); not production persistence.
    if p.startswith("/f/"):
        return True
    return False
