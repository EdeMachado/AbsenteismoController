#!/usr/bin/env python3
"""FIT-04 Release Candidate — disposable staging SQLite (never production).

Creates /tmp/abs-fit04-rc-<timestamp>/ with a synthetic DB seeded for browser
validation profiles: admin, tenant A (id=2), tenant B (id=4), orphan, inactive.

Uses ABSENTEISMO_SQLITE_PATH (see backend/database.py). Does not start the app
or touch /var/www/absenteismo.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Default credentials (overridable via env when running browser harness)
DEFAULTS = {
    "FIT04_ADMIN_USER": "fit04_admin",
    "FIT04_ADMIN_PASS": "Fit04Admin!",
    "FIT04_USER_A_USER": "fit04_user_a",
    "FIT04_USER_A_PASS": "Fit04UserA!",
    "FIT04_USER_B_USER": "fit04_user_b",
    "FIT04_USER_B_PASS": "Fit04UserB!",
    "FIT04_ORPHAN_USER": "fit04_orphan",
    "FIT04_ORPHAN_PASS": "Fit04Orphan!",
    "FIT04_INACTIVE_USER": "fit04_inactive",
    "FIT04_INACTIVE_PASS": "Fit04Inactive!",
}


def _cred(key: str) -> str:
    return (os.environ.get(key) or DEFAULTS[key]).strip()


def main() -> int:
    ts = time.strftime("%Y%m%d-%H%M%S")
    work = Path(f"/tmp/abs-fit04-rc-{ts}")
    work.mkdir(parents=True, exist_ok=False)
    db_path = work / "staging.sqlite"

    # Refuse production live path
    norm = str(db_path).replace("\\", "/").lower()
    if "/var/www/absenteismo/" in norm:
        raise SystemExit("Refusing production path")

    os.environ["ABSENTEISMO_SQLITE_PATH"] = str(db_path)
    os.environ.setdefault("SECRET_KEY", "fit04-staging-secret-not-for-production")
    os.environ.setdefault("ENVIRONMENT", "test")
    os.environ.setdefault("ENABLE_INTELLIGENT_INGESTION", "false")
    os.environ.setdefault("ENABLE_BIOMED_PERFORMANCE_ENGINE", "false")

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

    admin_user = _cred("FIT04_ADMIN_USER")
    admin_pass = _cred("FIT04_ADMIN_PASS")
    user_a = _cred("FIT04_USER_A_USER")
    pass_a = _cred("FIT04_USER_A_PASS")
    user_b = _cred("FIT04_USER_B_USER")
    pass_b = _cred("FIT04_USER_B_PASS")
    orphan_user = _cred("FIT04_ORPHAN_USER")
    orphan_pass = _cred("FIT04_ORPHAN_PASS")
    inactive_user = _cred("FIT04_INACTIVE_USER")
    inactive_pass = _cred("FIT04_INACTIVE_PASS")

    db = database.SessionLocal()
    try:
        # Tenants A=2, B=4 (explicit ids for tenant-isolation checks)
        db.add(
            Client(
                id=2,
                nome="FIT04 Tenant A Ltda",
                nome_fantasia="Tenant A",
                cnpj="11.111.111/0001-11",
            )
        )
        db.add(
            Client(
                id=4,
                nome="FIT04 Tenant B SA",
                nome_fantasia="Tenant B",
                cnpj="44.444.444/0001-44",
            )
        )
        db.flush()

        db.add(
            User(
                username=admin_user,
                email="fit04_admin@fit04.test",
                password_hash=get_password_hash(admin_pass),
                nome_completo="FIT04 Admin",
                is_admin=True,
                is_active=True,
                client_id=None,
            )
        )
        db.add(
            User(
                username=user_a,
                email="fit04_a@fit04.test",
                password_hash=get_password_hash(pass_a),
                nome_completo="FIT04 User A",
                is_admin=False,
                is_active=True,
                client_id=2,
            )
        )
        db.add(
            User(
                username=user_b,
                email="fit04_b@fit04.test",
                password_hash=get_password_hash(pass_b),
                nome_completo="FIT04 User B",
                is_admin=False,
                is_active=True,
                client_id=4,
            )
        )
        db.add(
            User(
                username=orphan_user,
                email="fit04_orphan@fit04.test",
                password_hash=get_password_hash(orphan_pass),
                nome_completo="FIT04 Orphan",
                is_admin=False,
                is_active=True,
                client_id=None,
            )
        )
        db.add(
            User(
                username=inactive_user,
                email="fit04_inactive@fit04.test",
                password_hash=get_password_hash(inactive_pass),
                nome_completo="FIT04 Inactive",
                is_admin=False,
                is_active=False,
                client_id=2,
            )
        )
        db.commit()
    finally:
        db.close()

    meta = {
        "workdir": str(work),
        "db": str(db_path),
        "ABSENTEISMO_SQLITE_PATH": str(db_path),
        "live_db_used": False,
        "tenants": {"A": 2, "B": 4},
        "credentials": {
            "admin": {"username": admin_user, "password": admin_pass},
            "tenant_a": {"username": user_a, "password": pass_a, "client_id": 2},
            "tenant_b": {"username": user_b, "password": pass_b, "client_id": 4},
            "orphan": {"username": orphan_user, "password": orphan_pass},
            "inactive": {"username": inactive_user, "password": inactive_pass},
        },
        "how_to_run_server": (
            f"ABSENTEISMO_SQLITE_PATH={db_path} "
            "SECRET_KEY=fit04-staging-secret-not-for-production "
            "ENVIRONMENT=test "
            "python -m uvicorn backend.main:app --host 127.0.0.1 --port 18081"
        ),
        "how_to_run_browser": (
            f"FIT04_BASE_URL=http://127.0.0.1:18081 FIT04_DB={db_path} "
            "python scripts/fit04_browser_validation.py"
        ),
    }
    meta_path = work / "staging_meta.json"
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")

    print("FIT04_STAGING_WORKDIR", work)
    print("FIT04_DB", db_path)
    print("ABSENTEISMO_SQLITE_PATH", db_path)
    print("META", meta_path)
    print("TENANT_A_ID", 2)
    print("TENANT_B_ID", 4)
    print("CRED_ADMIN", f"{admin_user} / {admin_pass}")
    print("CRED_USER_A", f"{user_a} / {pass_a}")
    print("CRED_USER_B", f"{user_b} / {pass_b}")
    print("CRED_ORPHAN", f"{orphan_user} / {orphan_pass}")
    print("CRED_INACTIVE", f"{inactive_user} / {inactive_pass}")
    print("SERVER_HINT", meta["how_to_run_server"])
    print("BROWSER_HINT", meta["how_to_run_browser"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
