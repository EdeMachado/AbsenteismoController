"""BioMed Performance Engine — shadow mode (Epic 2A).

Disabled by default via ENABLE_BIOMED_PERFORMANCE_ENGINE=false.
No HTTP endpoints, no UI, no production writes.
"""

from __future__ import annotations

import os

FEATURE_FLAG_ENV = "ENABLE_BIOMED_PERFORMANCE_ENGINE"
ENGINE_VERSION = "epic2a-performance-v1"


def is_performance_engine_enabled() -> bool:
    raw = (os.environ.get(FEATURE_FLAG_ENV) or "false").strip().lower()
    return raw in {"1", "true", "yes", "on"}


__all__ = [
    "FEATURE_FLAG_ENV",
    "ENGINE_VERSION",
    "is_performance_engine_enabled",
    "CanonicalSnapshotAdapter",
    "DataQualityAdapter",
    "PerformanceShadowService",
]


def __getattr__(name: str):
    # Lazy exports to avoid importing SQLAlchemy stacks at package import time
    if name == "CanonicalSnapshotAdapter":
        from backend.performance.canonical_snapshot_adapter import CanonicalSnapshotAdapter

        return CanonicalSnapshotAdapter
    if name == "DataQualityAdapter":
        from backend.performance.data_quality_adapter import DataQualityAdapter

        return DataQualityAdapter
    if name == "PerformanceShadowService":
        from backend.performance.performance_shadow_service import PerformanceShadowService

        return PerformanceShadowService
    raise AttributeError(name)
