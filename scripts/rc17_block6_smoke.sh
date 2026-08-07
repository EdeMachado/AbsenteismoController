#!/usr/bin/env bash
# RC-1.7 Block 6 — Production smoke (flags OFF / legacy)
#
# DOES NOT print SECRET_KEY, password hashes, tokens, CPF, matrícula, clinical data.
# USAGE:
#   sudo bash scripts/rc17_block6_smoke.sh
#   (read-mostly; set RC17_EXECUTE=1 only if your ops policy requires it)
#
set -euo pipefail

APP_DIR="${APP_DIR:-/var/www/absenteismo}"
LIVE_DB="${LIVE_DB:-/var/www/absenteismo/database/absenteismo.db}"
VENV_PY="${VENV_PY:-$APP_DIR/venv/bin/python}"
BASE="${BASE_URL:-http://127.0.0.1:8000}"
SERVICE="${SERVICE:-absenteismocontroller.service}"
GO=1
fail() { echo "SMOKE_FAIL: $*" >&2; GO=0; }
ok() { echo "SMOKE_OK: $*"; }

echo "=== RC-1.7 BLOCK6 smoke ==="

systemctl is-active --quiet "$SERVICE" && ok "service active" || fail "service inactive"

check_code() {
  local path="$1" expect="$2"
  local code
  code="$(curl -s -o /dev/null -w '%{http_code}' "$BASE$path" || echo 000)"
  if [[ "$code" == "$expect" ]]; then
    ok "$path -> $code"
  else
    fail "$path expected $expect got $code"
  fi
}

# Health + legacy pages
check_code "/api/health" "200"
check_code "/" "200"
check_code "/login" "200"
check_code "/clientes" "200"
check_code "/funcionarios" "200"
check_code "/upload" "200"
check_code "/produtividade" "200"
check_code "/dados_powerbi" "200"
check_code "/dashboard_powerbi" "200"

# Protected API anon -> 401
for p in /api/clientes /api/dashboard /api/users /api/uploads; do
  code="$(curl -s -o /dev/null -w '%{http_code}' "$BASE$p" || echo 000)"
  if [[ "$code" == "401" ]]; then
    ok "$p anon -> 401"
  else
    fail "$p anon expected 401 got $code"
  fi
done

# Docs / preview / staging / ficha / employee token blocked in production
for p in /docs /redoc /openapi.json \
         /preview/landing /preview/ficha-digital /preview/executive \
         /staging/executive-preview \
         /api/preview/ficha/templates /api/preview/ficha/reset \
         /f/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa; do
  code="$(curl -s -o /dev/null -w '%{http_code}' "$BASE$p" || echo 000)"
  # Accept 404 (gate) or 401 for APIs if gate+auth race; prefer 404
  if [[ "$code" == "404" ]]; then
    ok "$p blocked ($code)"
  else
    fail "$p expected 404 (blocked) got $code"
  fi
done

# Legacy exact /preview must remain (upload preview page)
check_code "/preview" "200"

echo "--- security headers (sample /api/health) ---"
HDRS="$(curl -sI "$BASE/api/health" || true)"
echo "$HDRS" | grep -iE '^(HTTP/|x-content-type-options:|x-frame-options:|content-security-policy:|strict-transport-security:|cache-control:)' || true
echo "$HDRS" | grep -qi 'x-content-type-options: *nosniff' && ok "nosniff" || fail "missing nosniff"
echo "$HDRS" | grep -qi 'x-frame-options: *DENY' && ok "DENY frame" || fail "missing X-Frame-Options DENY"

echo "--- CORS official vs random ---"
OFFICIAL="${CORS_OFFICIAL_ORIGIN:-https://www.absenteismocontroller.com.br}"
# Reflect only if configured; never require wildcard
RAND_ORIGIN="https://evil.example.invalid"
rand_acao="$(curl -sI -H "Origin: $RAND_ORIGIN" "$BASE/api/health" | grep -i '^access-control-allow-origin:' || true)"
if [[ -n "$rand_acao" ]] && echo "$rand_acao" | grep -q '\*\|evil.example'; then
  fail "random origin reflected or wildcard CORS: $rand_acao"
else
  ok "random origin not granted"
fi
# Official may or may not be reflected depending on CORS_ALLOWED_ORIGINS; log only
off_acao="$(curl -sI -H "Origin: $OFFICIAL" "$BASE/api/health" | grep -i '^access-control-allow-origin:' || true)"
echo "OFFICIAL_ACAO=${off_acao:-none}"

echo "--- DB integrity + inventory (no PII) ---"
"$VENV_PY" - <<PY
import json, sqlite3, sys, os
live = ${LIVE_DB@Q}
conn = sqlite3.connect(f"file:{live}?mode=ro", uri=True)
cur = conn.cursor()
quick = cur.execute("PRAGMA quick_check;").fetchone()[0]
integrity = cur.execute("PRAGMA integrity_check;").fetchone()[0]
print(json.dumps({"quick_check": quick, "integrity_check": integrity}, ensure_ascii=False))
if str(quick).lower() != "ok" or str(integrity).lower() != "ok":
    sys.exit(4)

def count(table):
    try:
        return cur.execute(f"SELECT COUNT(*) FROM [{table}]").fetchone()[0]
    except Exception:
        return None

clients = []
try:
    clients = [r[0] for r in cur.execute("SELECT id FROM clients ORDER BY id")]
except Exception:
    clients = []
need = {2, 4}
have = set(clients)
print(json.dumps({
    "client_ids": clients,
    "clients_2_and_4_present": need.issubset(have),
    "users_active": count("users"),
    "atestados": count("atestados"),
    "uploads": count("uploads"),
}, ensure_ascii=False))
if not need.issubset(have):
    sys.exit(5)

# Common weak password hashes — count only, never print hashes
# Heuristic: empty password_hash or well-known placeholder markers (not full hash dump)
weak = 0
try:
    rows = cur.execute("SELECT password_hash FROM users WHERE is_active=1").fetchall()
    for (ph,) in rows:
        if not ph or str(ph).strip() in {"", "password", "123456", "admin"}:
            weak += 1
except Exception:
    weak = -1
print(json.dumps({"common_plaintextish_passwords": weak}, ensure_ascii=False))
if weak not in (0, -1) and weak > 0:
    # treat obvious plaintext markers as fail; -1 means column probe skipped
    sys.exit(6)
conn.close()
print("DB_INVENTORY=PASS")
PY

DB_SIZE="$(stat -c%s "$LIVE_DB")"
DB_SHA="$(sha256sum "$LIVE_DB" | awk '{print $1}')"
echo "DB_SIZE_BYTES=$DB_SIZE"
echo "DB_SHA256=$DB_SHA"
echo "NOTE: SHA may change only on legitimate runtime writes; investigate unexpected deltas."

echo "--- flags OFF legacy posture ---"
"$VENV_PY" - <<'PY'
import os
# Do not override production env; report effective
from backend.preview_gate import preview_surfaces_enabled
from backend.executive import is_executive_ui_enabled, is_executive_presentation_enabled
from backend.ingestion import is_intelligent_ingestion_enabled
from backend.performance import is_performance_engine_enabled
from backend.authz import api_docs_enabled
checks = {
    "preview_surfaces_enabled": preview_surfaces_enabled(),
    "executive_ui": is_executive_ui_enabled(),
    "executive_presentation": is_executive_presentation_enabled(),
    "ingestion": is_intelligent_ingestion_enabled(),
    "performance": is_performance_engine_enabled(),
    "api_docs": api_docs_enabled(),
}
print(checks)
assert all(v is False for v in checks.values()), checks
print("LEGACY_WITH_FLAGS_OFF=PASS")
PY

if [[ "$GO" -eq 1 ]]; then
  echo "BLOCK6_RESULT=GO"
  echo "LEGACY_WITH_FLAGS_OFF=PASS"
  exit 0
fi
echo "BLOCK6_RESULT=NO_GO"
echo "LEGACY_WITH_FLAGS_OFF=FAIL"
exit 1
