"""BioMed Executive Intelligence (EXEC-01) — experimental UI/API.

Disabled by default via ENABLE_EXECUTIVE_UI=false.
Does not alter legacy dashboard, production DB schema, or other feature flags.
"""

from __future__ import annotations

import os

FEATURE_FLAG_ENV = "ENABLE_EXECUTIVE_UI"
ENGINE_VERSION = "exec01-executive-v1"
SMALL_GROUP_THRESHOLD = 5


def is_executive_ui_enabled() -> bool:
    raw = (os.environ.get(FEATURE_FLAG_ENV) or "false").strip().lower()
    return raw in {"1", "true", "yes", "on"}


__all__ = [
    "FEATURE_FLAG_ENV",
    "ENGINE_VERSION",
    "SMALL_GROUP_THRESHOLD",
    "is_executive_ui_enabled",
]
