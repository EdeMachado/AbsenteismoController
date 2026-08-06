#!/usr/bin/env bash
# FIT-06 / FIT06-DR1 — Production diagnostic + consistent SQLite backup (MANUAL SSH ONLY)
#
# DOES NOT:
#   - stop/restart services
#   - alter the live database
#   - merge/deploy/pull/checkout
#   - print usernames, emails, password hashes, tokens, or SECRET_KEY values
#
# USAGE (on VPS, after human authorization):
#   sudo bash scripts/fit06_prod_diag_backup.sh
# Or copy this block into an SSH session and run as root/operator.
#
# Defaults match known production layout; override with env if needed.
set -euo pipefail

APP_DIR="${APP_DIR:-/var/www/absenteismo}"
LIVE_DB="${LIVE_DB:-/var/www/absenteismo/database/absenteismo.db}"
BACKUP_DIR="${BACKUP_DIR:-/root/backups/absenteismo}"
SERVICE="${SERVICE:-absenteismocontroller.service}"
VENV_PY="${VENV_PY:-$APP_DIR/venv/bin/python}"
export SERVICE
TS="$(date +%Y%m%d_%H%M%S)"
OUT_DIR="${OUT_DIR:-$BACKUP_DIR/fit06_diag_$TS}"
BACKUP_DB="$BACKUP_DIR/absenteismo_pre_fit06_${TS}.db"
REPORT="$OUT_DIR/inventory_no_pii.json"
export LIVE_DB BACKUP_DB REPORT

echo "=== FIT06-DR1 diagnostic+backup ==="
echo "TS=$TS"
echo "APP_DIR=$APP_DIR"
echo "LIVE_DB=$LIVE_DB"
echo "BACKUP_DIR=$BACKUP_DIR"
echo "SERVICE=$SERVICE"

# Refuse accidental non-production paths only when FORCE_NONPROD is unset
if [[ "${FORCE_NONPROD:-}" != "1" ]]; then
  if [[ "$LIVE_DB" != "/var/www/absenteismo/database/absenteismo.db" ]]; then
    echo "REFUSING: LIVE_DB is not the known production path. Set FORCE_NONPROD=1 to override." >&2
    exit 2
  fi
fi

mkdir -p "$BACKUP_DIR" "$OUT_DIR"

echo "--- process / cwd ---"
systemctl status "$SERVICE" --no-pager -l | head -n 40 || true
if command -v ss >/dev/null 2>&1; then
  ss -ltnp | grep -E ':8000\b' || true
fi
# Best-effort cwd of python/gunicorn serving the app
pgrep -af 'gunicorn|uvicorn|backend.main' || true

echo "--- live db presence ---"
ls -la "$LIVE_DB"
test -f "$LIVE_DB"

if [[ ! -x "$VENV_PY" ]]; then
  echo "VENV python not executable at $VENV_PY" >&2
  exit 3
fi

echo "--- integrity (live, read-only pragmas) ---"
"$VENV_PY" - <<PY
import json, os, sqlite3, sys
live = ${LIVE_DB@Q}
conn = sqlite3.connect(f"file:{live}?mode=ro", uri=True)
cur = conn.cursor()
quick = cur.execute("PRAGMA quick_check;").fetchone()[0]
integrity = cur.execute("PRAGMA integrity_check;").fetchone()[0]
journal = cur.execute("PRAGMA journal_mode;").fetchone()[0]
print(json.dumps({"quick_check": quick, "integrity_check": integrity, "journal_mode": journal}, ensure_ascii=False))
if str(quick).lower() != "ok" or str(integrity).lower() != "ok":
    sys.exit(4)
conn.close()
PY

echo "--- consistent backup via sqlite3.Connection.backup (venv Python) ---"
"$VENV_PY" - <<PY
import os, sqlite3, sys
src = ${LIVE_DB@Q}
dst = ${BACKUP_DB@Q}
if os.path.exists(dst):
    print("backup already exists", dst, file=sys.stderr)
    sys.exit(5)
src_conn = sqlite3.connect(src)
dst_conn = sqlite3.connect(dst)
try:
    src_conn.backup(dst_conn)
finally:
    dst_conn.close()
    src_conn.close()
print("BACKUP_OK", dst)
PY

echo "--- validate backup ---"
"$VENV_PY" - <<PY
import json, os, sqlite3, sys
bak = ${BACKUP_DB@Q}
conn = sqlite3.connect(f"file:{bak}?mode=ro", uri=True)
cur = conn.cursor()
quick = cur.execute("PRAGMA quick_check;").fetchone()[0]
integrity = cur.execute("PRAGMA integrity_check;").fetchone()[0]
print(json.dumps({"backup_quick_check": quick, "backup_integrity_check": integrity}, ensure_ascii=False))
if str(quick).lower() != "ok" or str(integrity).lower() != "ok":
    sys.exit(6)
conn.close()
print("size_bytes", os.path.getsize(bak))
PY

SHA="$(sha256sum "$BACKUP_DB" | awk '{print $1}')"
echo "BACKUP_SHA256=$SHA"
echo "$SHA  $(basename "$BACKUP_DB")" > "${BACKUP_DB}.sha256"

gzip -c "$BACKUP_DB" > "${BACKUP_DB}.gz"
echo "BACKUP_GZ=${BACKUP_DB}.gz"
ls -la "$BACKUP_DB" "${BACKUP_DB}.gz" "${BACKUP_DB}.sha256"

echo "--- inventory aggregates (NO PII) ---"
"$VENV_PY" - <<PY
import json, os, sqlite3
from collections import Counter

live = ${LIVE_DB@Q}
report_path = ${REPORT@Q}
conn = sqlite3.connect(f"file:{live}?mode=ro", uri=True)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

def table_exists(name: str) -> bool:
    r = cur.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (name,),
    ).fetchone()
    return r is not None

tables = [r[0] for r in cur.execute(
    "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
)]
counts = {}
for t in tables:
    try:
        counts[t] = cur.execute(f"SELECT COUNT(*) FROM [{t}]").fetchone()[0]
    except Exception:
        counts[t] = None

clients = []
if table_exists("clients"):
    for row in cur.execute("SELECT id, nome FROM clients ORDER BY id"):
        clients.append({"id": row["id"], "nome": row["nome"]})

users = {
    "total": 0,
    "ativos": 0,
    "inativos": 0,
    "administradores_ativos": 0,
    "nao_admin_sem_tenant": 0,
    "por_client_id": {},
    "duplicate_username_count": 0,
}
if table_exists("users"):
    users["total"] = cur.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    users["ativos"] = cur.execute("SELECT COUNT(*) FROM users WHERE is_active=1").fetchone()[0]
    users["inativos"] = cur.execute("SELECT COUNT(*) FROM users WHERE is_active=0").fetchone()[0]
    users["administradores_ativos"] = cur.execute(
        "SELECT COUNT(*) FROM users WHERE is_admin=1 AND is_active=1"
    ).fetchone()[0]
    users["nao_admin_sem_tenant"] = cur.execute(
        "SELECT COUNT(*) FROM users WHERE (is_admin=0 OR is_admin IS NULL) AND client_id IS NULL"
    ).fetchone()[0]
    por = {}
    for row in cur.execute(
        "SELECT client_id, COUNT(*) AS c FROM users GROUP BY client_id ORDER BY client_id"
    ):
        key = "NULL" if row["client_id"] is None else str(row["client_id"])
        por[key] = row["c"]
    users["por_client_id"] = por
    users["duplicate_username_count"] = cur.execute(
        "SELECT COUNT(*) FROM (SELECT username FROM users GROUP BY username HAVING COUNT(*)>1)"
    ).fetchone()[0]
    # Default-password check: only count whether ANY known default hashes would match
    # We do NOT print hashes. We only attempt bcrypt verify against synthetic defaults if bcrypt available.
    default_hits = 0
    try:
        import bcrypt
        candidates = [b"admin", b"admin123", b"123456", b"password"]
        for (ph,) in cur.execute("SELECT password_hash FROM users WHERE is_active=1"):
            if not ph:
                continue
            hb = ph.encode() if isinstance(ph, str) else ph
            for cand in candidates:
                try:
                    if bcrypt.checkpw(cand, hb):
                        default_hits += 1
                        break
                except Exception:
                    pass
    except Exception:
        default_hits = -1  # unknown / bcrypt unavailable
    users["active_accounts_matching_common_default_passwords"] = default_hits

access = {
    "admins_is_admin_true": 0,
    "users_tenant_2": 0,
    "users_tenant_4": 0,
    "users_sem_tenant_nao_admin": users["nao_admin_sem_tenant"],
    "users_inativos": users["inativos"],
}
if table_exists("users"):
    access["admins_is_admin_true"] = cur.execute(
        "SELECT COUNT(*) FROM users WHERE is_admin=1"
    ).fetchone()[0]
    access["users_tenant_2"] = cur.execute(
        "SELECT COUNT(*) FROM users WHERE client_id=2"
    ).fetchone()[0]
    access["users_tenant_4"] = cur.execute(
        "SELECT COUNT(*) FROM users WHERE client_id=4"
    ).fetchone()[0]

competencias = []
if table_exists("uploads") and table_exists("clients"):
    q = """
    SELECT u.client_id AS client_id,
           MIN(u.mes_referencia) AS primeiro_mes,
           MAX(u.mes_referencia) AS ultimo_mes,
           COUNT(DISTINCT u.mes_referencia) AS qtd_competencias,
           COUNT(*) AS qtd_uploads
    FROM uploads u
    GROUP BY u.client_id
    ORDER BY u.client_id
    """
    for row in cur.execute(q):
        eventos = None
        if table_exists("atestados"):
            eventos = cur.execute(
                """
                SELECT COUNT(*) FROM atestados a
                JOIN uploads up ON up.id = a.upload_id
                WHERE up.client_id = ?
                """,
                (row["client_id"],),
            ).fetchone()[0]
        competencias.append(
            {
                "client_id": row["client_id"],
                "primeiro_mes": row["primeiro_mes"],
                "ultimo_mes": row["ultimo_mes"],
                "qtd_competencias": row["qtd_competencias"],
                "qtd_uploads": row["qtd_uploads"],
                "qtd_eventos": eventos,
            }
        )

payload = {
    "fit06": "FIT06-DR1",
    "live_db": live,
    "clients": clients,
    "users_aggregates": users,
    "access_snapshot": access,
    "table_counts": counts,
    "competencias_por_cliente": competencias,
}
with open(report_path, "w", encoding="utf-8") as f:
    json.dump(payload, f, ensure_ascii=False, indent=2)
print("REPORT", report_path)
print(json.dumps(payload, ensure_ascii=False, indent=2))
conn.close()
PY

echo "--- config presence (NO SECRET VALUES) ---"
# Inspect systemd unit Environment / EnvironmentFile without printing secrets
UNIT_FILE="$(systemctl show -p FragmentPath "$SERVICE" | cut -d= -f2-)"
echo "UNIT_FILE=$UNIT_FILE"
"$VENV_PY" - <<'PY'
import os, re, json, subprocess, shlex
service = os.environ.get("SERVICE", "absenteismocontroller.service")
# Pull Environment= and EnvironmentFiles from systemd (values redacted for SECRET_KEY)
out = subprocess.check_output(["systemctl", "show", service, "-p", "Environment", "-p", "EnvironmentFiles"], text=True)
keys_of_interest = [
    "ENVIRONMENT",
    "ENABLE_INTELLIGENT_INGESTION",
    "ENABLE_BIOMED_PERFORMANCE_ENGINE",
    "ENABLE_API_DOCS",
    "CORS_ALLOWED_ORIGINS",
    "SECRET_KEY",
    "ABSENTEISMO_SQLITE_PATH",
    "INGESTION_SQLITE_PATH",
    "INGESTION_ALLOW_TEST_DEPENDENCIES",
]
present = {k: False for k in keys_of_interest}
normalized = {}
# Parse Environment=KEY=VALUE pairs
for line in out.splitlines():
    if line.startswith("Environment="):
        raw = line[len("Environment="):]
        # systemd may space-separate
        for part in shlex.split(raw):
            if "=" not in part:
                continue
            k, v = part.split("=", 1)
            if k in present:
                present[k] = True
                if k == "SECRET_KEY":
                    normalized[k] = "PRESENT" if v else "EMPTY"
                else:
                    normalized[k] = v.strip().lower() if v else ""
print(json.dumps({"env_present": present, "env_normalized_no_secrets": normalized}, ensure_ascii=False, indent=2))
PY

echo "--- server compatibility (read-only) ---"
"$VENV_PY" - <<'PY'
import importlib, json, platform, shutil, sys
mods = [
    "fastapi", "sqlalchemy", "jose", "multipart", "openpyxl", "pandas", "fpdf", "pptx", "gunicorn", "bcrypt", "dotenv"
]
info = {
    "python": sys.version.split()[0],
    "platform": platform.platform(),
    "disk_free_gb": None,
    "modules": {},
}
try:
    usage = shutil.disk_usage("/")
    info["disk_free_gb"] = round(usage.free / (1024**3), 2)
except Exception:
    pass
for m in mods:
    try:
        mod = importlib.import_module(m if m != "jose" else "jose")
        ver = getattr(mod, "__version__", None) or getattr(mod, "VERSION", None) or "imported"
        info["modules"][m] = str(ver)
    except Exception as e:
        info["modules"][m] = f"MISSING:{type(e).__name__}"
print(json.dumps(info, ensure_ascii=False, indent=2))
PY
command -v nginx >/dev/null && nginx -v 2>&1 || echo "nginx: not found"
command -v git >/dev/null && git --version || echo "git: not found"
systemctl --version | head -n1 || true
free -h | head -n2 || true
df -h "$APP_DIR" | tail -n1 || true

echo "=== FIT06-DR1 DONE ==="
echo "BACKUP_DB=$BACKUP_DB"
echo "BACKUP_SHA256=$SHA"
echo "REPORT=$REPORT"
echo "NOTE: service was NOT restarted; live DB was NOT modified."
