#!/usr/bin/env python3
"""FIT-02 smoke on disposable SQLite + free port (default 18080).

Never points at production DB. Sets ABSENTEISMO_SQLITE_PATH before importing app.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    port = int(os.environ.get("FIT02_PORT", "18080"))
    work = Path(tempfile.mkdtemp(prefix="abs-fit02-smoke-"))
    db_path = work / "staging_legacy.sqlite"
    os.environ["ABSENTEISMO_SQLITE_PATH"] = str(db_path)
    os.environ["ENABLE_INTELLIGENT_INGESTION"] = "false"
    os.environ["ENABLE_BIOMED_PERFORMANCE_ENGINE"] = "false"
    os.environ.pop("INGESTION_ALLOW_TEST_DEPENDENCIES", None)

    # Refuse accidental production
    assert "/var/www/absenteismo" not in str(db_path)

    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    import backend.database as database
    from backend.auth import get_password_hash
    from backend.database import Base
    from backend.models import Client, User

    database.DB_PATH = str(db_path)
    database.SQLALCHEMY_DATABASE_URL = f"sqlite:///{db_path}"
    database.engine = create_engine(
        database.SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False},
    )
    database.SessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=database.engine
    )
    Base.metadata.create_all(bind=database.engine)

    db = database.SessionLocal()
    try:
        db.add(Client(id=201, nome="Smoke Empresa A", nome_fantasia="SmokeA"))
        db.add(
            User(
                username="smoke_a",
                email="smoke_a@fit02.test",
                password_hash=get_password_hash("smoke-pass-a"),
                is_admin=False,
                is_active=True,
                client_id=201,
            )
        )
        db.commit()
    finally:
        db.close()

    sha_before = hashlib.sha256(db_path.read_bytes()).hexdigest()

    from fastapi.testclient import TestClient
    from backend.main import app

    client = TestClient(app)
    report = {"workdir": str(work), "db": str(db_path), "port_intended": port, "steps": []}

    def step(name, ok, detail=None):
        report["steps"].append({"name": name, "ok": bool(ok), "detail": detail})
        print(("OK" if ok else "FAIL"), name, detail or "")

    r = client.get("/api/health")
    step("health", r.status_code == 200, r.status_code)

    r = client.post(
        "/api/auth/login",
        data={"username": "smoke_a", "password": "smoke-pass-a"},
    )
    step("login", r.status_code == 200, r.status_code)
    token = (r.json() or {}).get("access_token") if r.status_code == 200 else None
    headers = {"Authorization": f"Bearer {token}"} if token else {}

    r = client.get("/api/clientes", headers=headers)
    step("clientes_auth", r.status_code == 200, r.status_code)

    r = client.get("/")
    step("home_page", r.status_code in {200, 304}, r.status_code)
    r = client.get("/dashboard_powerbi")
    step("dashboard_powerbi_page", r.status_code in {200, 304}, r.status_code)

    r = client.get("/api/ingestion/mapping-profiles?client_id=201", headers=headers)
    step("ingestion_off", r.status_code in {404, 405}, r.status_code)

    r = client.get("/api/uploads?client_id=999", headers=headers)
    step("cross_tenant_uploads", r.status_code in {403, 404}, r.status_code)

    sha_after = hashlib.sha256(db_path.read_bytes()).hexdigest()
    # login updates last_login — hash may change; size should remain plausible
    step("db_exists", db_path.exists(), str(db_path.stat().st_size))
    report["sha_before"] = sha_before
    report["sha_after_login"] = sha_after
    report["live_db_used"] = False
    report["flags"] = {
        "ENABLE_INTELLIGENT_INGESTION": False,
        "ENABLE_BIOMED_PERFORMANCE_ENGINE": False,
    }

    out = work / "smoke_report.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("SMOKE_REPORT", out)
    failed = [s for s in report["steps"] if not s["ok"]]
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
