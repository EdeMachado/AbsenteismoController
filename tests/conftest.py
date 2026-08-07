"""Global pytest bootstrap for disposable SQLite (FIT-06 CI).

Ensures TestClient startup never targets a missing directory or production path,
and that the empty disposable DB has schema for global-app tests (no fixtures).
"""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

# Must run before backend.database / backend.main import in test modules.
_prod = "/var/www/absenteismo/database/absenteismo.db"
_path = (os.environ.get("ABSENTEISMO_SQLITE_PATH") or "").strip()
if not _path or _path == _prod:
    _dir = Path(tempfile.mkdtemp(prefix="abs-pytest-sqlite-"))
    _path = str(_dir / "ci.sqlite")
    os.environ["ABSENTEISMO_SQLITE_PATH"] = _path
else:
    Path(_path).parent.mkdir(parents=True, exist_ok=True)

os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("ENABLE_INTELLIGENT_INGESTION", "false")
os.environ.setdefault("ENABLE_BIOMED_PERFORMANCE_ENGINE", "false")
os.environ.setdefault("ENABLE_EXECUTIVE_UI", "false")
os.environ.setdefault("SECRET_KEY", "pytest-secret-not-for-production")

# Ensure default relative database/ exists as a safety net for any leftover imports.
Path("database").mkdir(exist_ok=True)

# Empty CI SQLite needs tables before tests that use the global app engine
# (e.g. FIT-04 CORS login header check) without a per-test fixture.
import backend.models  # noqa: E402,F401 — register metadata on Base
from backend.database import Base, engine  # noqa: E402

Base.metadata.create_all(bind=engine)
