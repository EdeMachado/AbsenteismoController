"""Épico 1 — Intelligent data ingestion (feature-flagged, off by default).

All services in this package are inert unless ENABLE_INTELLIGENT_INGESTION=true.
They must not alter production data, existing uploads, or current upload routes.
"""

from __future__ import annotations

import os

PIPELINE_VERSION = "epic1-ingestion-v1"
FEATURE_FLAG_ENV = "ENABLE_INTELLIGENT_INGESTION"


def is_intelligent_ingestion_enabled() -> bool:
    """Return True only when the feature flag is explicitly enabled."""
    raw = (os.environ.get(FEATURE_FLAG_ENV) or "false").strip().lower()
    return raw in {"1", "true", "yes", "on"}


__all__ = [
    "PIPELINE_VERSION",
    "FEATURE_FLAG_ENV",
    "is_intelligent_ingestion_enabled",
]
