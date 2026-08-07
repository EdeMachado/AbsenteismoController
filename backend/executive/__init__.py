"""BioMed Executive Intelligence (EXEC-01→03) — experimental UI/API.

Disabled by default via ENABLE_EXECUTIVE_UI=false.
Optional subflag ENABLE_EXECUTIVE_PRESENTATION=false (also OFF by default).
Does not alter legacy dashboard, production DB schema, or other feature flags.
"""

from __future__ import annotations

import os

FEATURE_FLAG_ENV = "ENABLE_EXECUTIVE_UI"
PRESENTATION_FLAG_ENV = "ENABLE_EXECUTIVE_PRESENTATION"
ENGINE_VERSION = "exec03-executive-v1"
SMALL_GROUP_THRESHOLD = 5


def is_executive_ui_enabled() -> bool:
    raw = (os.environ.get(FEATURE_FLAG_ENV) or "false").strip().lower()
    return raw in {"1", "true", "yes", "on"}


def is_executive_presentation_enabled() -> bool:
    """Presentation requires parent UI flag AND ENABLE_EXECUTIVE_PRESENTATION=true.

    Both flags default OFF. Staging may enable both explicitly.
    """
    if not is_executive_ui_enabled():
        return False
    raw = (os.environ.get(PRESENTATION_FLAG_ENV) or "false").strip().lower()
    return raw in {"1", "true", "yes", "on"}


__all__ = [
    "FEATURE_FLAG_ENV",
    "PRESENTATION_FLAG_ENV",
    "ENGINE_VERSION",
    "SMALL_GROUP_THRESHOLD",
    "is_executive_ui_enabled",
    "is_executive_presentation_enabled",
]
