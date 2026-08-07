#!/usr/bin/env bash
# RC-1.7 Block 1 — Predeploy READ-ONLY diagnostics
#
# DOES NOT: restart, pull, migrate, alter DB, alter .env, print secrets.
#
# USAGE (on VPS, after human authorization for READ-ONLY check):
#   sudo bash scripts/rc17_block1_predeploy_readonly.sh
#
set -euo pipefail

APP_DIR="${APP_DIR:-/var/www/absenteismo}"
LIVE_DB="${LIVE_DB:-/var/www/absenteismo/database/absenteismo.db}"
SERVICE="${SERVICE:-absenteismocontroller.service}"
VENV_PY="${VENV_PY:-$APP_DIR/venv/bin/python}"
HEALTH_URL="${HEALTH_URL:-http://127.0.0.1:8000/api/health}"
TARGET_HEAD="${TARGET_HEAD:-fefa1996d37004c88dfb2087166544ea05be9e8f}"
PRODUCTION_EXPECTED_HEAD="${PRODUCTION_EXPECTED_HEAD:-540cda0806326aa14ced57d42fd43e8a69817d08}"
MAIN_RELEASE_MERGE="${MAIN_RELEASE_MERGE:-9ed88591f08a5261abb09d7d9e03493a52dff2c3}"

GO=1
fail() { echo "NO_GO: $*" >&2; GO=0; }
ok() { echo "OK: $*"; }

echo "=== RC-1.7 BLOCK1 predeploy readonly ==="
echo "TS=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "APP_DIR=$APP_DIR"
echo "LIVE_DB=$LIVE_DB"
echo "SERVICE=$SERVICE"
echo "TARGET_HEAD=$TARGET_HEAD"
echo "PRODUCTION_EXPECTED_HEAD=$PRODUCTION_EXPECTED_HEAD"

if [[ "${FORCE_NONPROD:-}" != "1" ]]; then
  if [[ "$APP_DIR" != "/var/www/absenteismo" ]] || [[ "$LIVE_DB" != "/var/www/absenteismo/database/absenteismo.db" ]]; then
    echo "REFUSING: paths are not known production layout (set FORCE_NONPROD=1 to override)." >&2
    exit 2
  fi
fi

cd "$APP_DIR"
echo "--- pwd ---"
pwd

echo "--- branch / HEAD ---"
BRANCH="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo UNKNOWN)"
LOCAL_HEAD="$(git rev-parse HEAD 2>/dev/null || echo UNKNOWN)"
echo "BRANCH=$BRANCH"
echo "LOCAL_HEAD=$LOCAL_HEAD"

echo "--- fetch origin (read refs only) ---"
git fetch origin main --quiet
ORIGIN_MAIN="$(git rev-parse origin/main)"
echo "ORIGIN_MAIN=$ORIGIN_MAIN"
if [[ "$ORIGIN_MAIN" != "$TARGET_HEAD" ]]; then
  fail "origin/main != TARGET_HEAD ($ORIGIN_MAIN != $TARGET_HEAD)"
else
  ok "origin/main matches TARGET_HEAD"
fi

# Confirm docs-only delta between release merge and target
DOC_DELTA="$(git diff --name-only "$MAIN_RELEASE_MERGE".."$TARGET_HEAD" || true)"
echo "DOCS_DELTA_9ed8859_to_TARGET:"
echo "$DOC_DELTA"
if [[ -n "$DOC_DELTA" ]] && echo "$DOC_DELTA" | grep -vqE '^docs/'; then
  fail "non-docs files between MAIN_RELEASE_MERGE and TARGET_HEAD"
else
  ok "delta MAIN_RELEASE_MERGE..TARGET is docs-only (or empty)"
fi

echo "--- git status (tracked) ---"
# Tracked cleanliness: no modified/staged tracked files
if [[ -n "$(git status --porcelain --untracked-files=no 2>/dev/null || true)" ]]; then
  git status --porcelain --untracked-files=no
  fail "tracked working tree is dirty"
else
  ok "tracked working tree clean"
fi

echo "--- untracked (critical preserve list) ---"
for p in database .env gunicorn_config.py logs nohup.out; do
  if [[ -e "$p" ]]; then
    echo "PRESENT_UNTRACKED_OR_LOCAL=$p"
  else
    echo "MISSING_LOCAL=$p"
  fi
done
# List untracked top-level (names only)
git status --porcelain -u | awk '{print $2}' | head -n 40 || true

echo "--- service ---"
if systemctl is-active --quiet "$SERVICE"; then
  ok "service active"
  systemctl is-active "$SERVICE"
else
  fail "service not active"
  systemctl status "$SERVICE" --no-pager -l | head -n 30 || true
fi

echo "--- port 8000 ---"
if command -v ss >/dev/null 2>&1; then
  ss -ltnp | grep -E ':8000\b' || fail "nothing listening on :8000"
else
  echo "ss not available; skip listen check"
fi

echo "--- health ---"
HEALTH_CODE="$(curl -s -o /tmp/rc17_health.json -w '%{http_code}' "$HEALTH_URL" || echo 000)"
echo "HEALTH_HTTP=$HEALTH_CODE"
if [[ "$HEALTH_CODE" != "200" ]]; then
  fail "health not 200"
else
  ok "health 200"
  # print non-sensitive fields only
  if [[ -x "$VENV_PY" ]]; then
    "$VENV_PY" - <<'PY'
import json
from pathlib import Path
raw = Path("/tmp/rc17_health.json").read_text(encoding="utf-8")
data = json.loads(raw)
safe = {k: data.get(k) for k in ("status", "version", "timestamp", "database") if k in data}
# nested database health without paths/secrets
db = data.get("database") if isinstance(data.get("database"), dict) else None
if db:
    safe["database"] = {k: db.get(k) for k in ("healthy", "connected", "integrity_check", "size_mb") if k in db}
print(json.dumps(safe, ensure_ascii=False))
PY
  fi
fi

echo "--- DB existence / integrity (read-only) ---"
if [[ ! -f "$LIVE_DB" ]]; then
  fail "LIVE_DB missing"
else
  ok "LIVE_DB exists"
  ls -la "$LIVE_DB"
  DB_SIZE="$(stat -c%s "$LIVE_DB" 2>/dev/null || wc -c <"$LIVE_DB")"
  DB_SHA="$(sha256sum "$LIVE_DB" | awk '{print $1}')"
  echo "DB_SIZE_BYTES=$DB_SIZE"
  echo "DB_SHA256=$DB_SHA"
  if [[ ! -x "$VENV_PY" ]]; then
    fail "venv python missing at $VENV_PY"
  else
    "$VENV_PY" - <<PY
import json, sqlite3, sys
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
    ok "DB quick_check + integrity_check ok"
  fi
fi

echo "--- disk / memory ---"
df -h "$APP_DIR" | tail -n1 || true
free -h | head -n2 || true

echo "--- .env / SECRET_KEY presence (values NEVER printed) ---"
ENV_FILE="$APP_DIR/.env"
if [[ -f "$ENV_FILE" ]]; then
  ok ".env present"
else
  fail ".env missing"
fi

# Detect SECRET_KEY presence without printing value (env file or systemd)
SECRET_PRESENT=0
if [[ -f "$ENV_FILE" ]] && grep -Eq '^[[:space:]]*SECRET_KEY[[:space:]]*=' "$ENV_FILE"; then
  SECRET_PRESENT=1
fi
# systemd Environment / EnvironmentFiles (names only)
UNIT_ENV="$(systemctl show -p Environment -p EnvironmentFiles "$SERVICE" 2>/dev/null || true)"
if echo "$UNIT_ENV" | grep -q 'SECRET_KEY'; then
  SECRET_PRESENT=1
fi
if [[ "$SECRET_PRESENT" -eq 1 ]]; then
  ok "SECRET_KEY present (value redacted)"
else
  fail "SECRET_KEY not detected"
fi

echo "--- CORS / flags (names + boolean presence; no secrets) ---"
"$VENV_PY" - <<PY
import os, re, json
from pathlib import Path

env_path = Path(${ENV_FILE@Q})
vals = {}
if env_path.is_file():
    for line in env_path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        vals[k.strip()] = v.strip().strip('"').strip("'")

# overlay process env for keys of interest (still never print SECRET_KEY)
keys = [
    "ENVIRONMENT",
    "CORS_ALLOWED_ORIGINS",
    "ENABLE_EXECUTIVE_UI",
    "ENABLE_EXECUTIVE_PRESENTATION",
    "ENABLE_INTELLIGENT_INGESTION",
    "ENABLE_BIOMED_PERFORMANCE_ENGINE",
    "ENABLE_API_DOCS",
    "ENABLE_PREVIEW_SURFACES",
]
report = {}
for k in keys:
    raw = os.environ.get(k, vals.get(k))
    if raw is None:
        report[k] = {"present": False, "effective_default_note": "absent — app defaults apply"}
    else:
        report[k] = {"present": True, "value": raw}
print(json.dumps(report, ensure_ascii=False, indent=2))
cors = report.get("CORS_ALLOWED_ORIGINS", {})
if cors.get("present") and "*" in str(cors.get("value", "")):
    raise SystemExit("CORS contains wildcard — NO_GO")
PY

echo "--- rollback head (current production HEAD) ---"
echo "ROLLBACK_HEAD=$LOCAL_HEAD"
echo "EXPECTED_PRODUCTION_HEAD_BEFORE_DEPLOY=$PRODUCTION_EXPECTED_HEAD"
if [[ "$LOCAL_HEAD" != "$PRODUCTION_EXPECTED_HEAD" ]]; then
  echo "WARN: local HEAD differs from PRODUCTION_EXPECTED_HEAD — record actual ROLLBACK_HEAD above"
fi

echo "--- migration stance ---"
echo "MIGRATION_REQUIRED=no"
echo "DEPLOY_DE_CODIGO_SEM_MIGRATION=true"

echo "=== BLOCK1 SUMMARY ==="
if [[ "$GO" -eq 1 ]]; then
  echo "BLOCK1_RESULT=GO"
  exit 0
fi
echo "BLOCK1_RESULT=NO_GO"
exit 1
