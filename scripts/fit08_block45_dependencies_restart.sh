#!/usr/bin/env bash
# FIT-08 BLOCO 4+5 — DEPENDÊNCIAS, IMPORT CHECK E RESTART ÚNICO
# Sem migration, sem alterar .env/banco, sem rollback automático, sem smoke funcional.
set -euo pipefail

APP=/var/www/absenteismo
TARGET_HEAD=540cda0806326aa14ced57d42fd43e8a69817d08
PY=/var/www/absenteismo/venv/bin/python3
PIP=/var/www/absenteismo/venv/bin/pip
DB="$APP/database/absenteismo.db"
SERVICE=absenteismocontroller.service

HEAD=""
DB_SHA_BEFORE=""
DB_SHA_AFTER=""
DB_SIZE_BEFORE=""
DB_SIZE_AFTER=""
SERVICE_PID_BEFORE=""
SERVICE_PID_AFTER=""
SERVICE_STATUS_BEFORE=""
SERVICE_STATUS=""
PY_COMPILE_OK=no
IMPORT_MAIN_OK=no
FOUNDATION_IMPORTS_OK=no
FLAGS_OFF=no
API_DOCS_OFF=no
DB_PRESERVED=no
SERVICE_RESTARTED=no
BLOCK45_RESULT=NO_GO
RESTART_ATTEMPTED=no
RESTART_TS=""

print_summary() {
  echo "======== RESUMO ========"
  echo "HEAD=${HEAD:-}"
  echo "DB_SHA_BEFORE=${DB_SHA_BEFORE:-}"
  echo "DB_SHA_AFTER=${DB_SHA_AFTER:-}"
  echo "DB_SIZE_BEFORE=${DB_SIZE_BEFORE:-}"
  echo "DB_SIZE_AFTER=${DB_SIZE_AFTER:-}"
  echo "SERVICE_PID_BEFORE=${SERVICE_PID_BEFORE:-}"
  echo "SERVICE_PID_AFTER=${SERVICE_PID_AFTER:-}"
  echo "PY_COMPILE_OK=${PY_COMPILE_OK:-no}"
  echo "IMPORT_MAIN_OK=${IMPORT_MAIN_OK:-no}"
  echo "FOUNDATION_IMPORTS_OK=${FOUNDATION_IMPORTS_OK:-no}"
  echo "FLAGS_OFF=${FLAGS_OFF:-no}"
  echo "API_DOCS_OFF=${API_DOCS_OFF:-no}"
  echo "DB_PRESERVED=${DB_PRESERVED:-no}"
  echo "SERVICE_RESTARTED=${SERVICE_RESTARTED:-no}"
  echo "SERVICE_STATUS=${SERVICE_STATUS:-}"
  echo "BLOCK45_RESULT=${BLOCK45_RESULT:-NO_GO}"
}

fail() {
  echo "FAIL: $*" >&2
  BLOCK45_RESULT=NO_GO
  if [ "$RESTART_ATTEMPTED" = "yes" ]; then
    SERVICE_STATUS=$(systemctl is-active "$SERVICE" 2>/dev/null || echo inactive)
    SERVICE_PID_AFTER=$(systemctl show -p MainPID --value "$SERVICE" 2>/dev/null || echo "")
    echo "NOTE: restart foi tentado; rollback/banco NÃO serão restaurados automaticamente." >&2
  else
    echo "NOTE: restart NÃO foi executado." >&2
  fi
  print_summary
  exit 1
}

sha_file() { sha256sum "$1" | awk '{print $1}'; }
size_file() { stat -c '%s' "$1"; }

ingestion_tables() {
  sqlite3 "$DB" "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'ingestion_%' ORDER BY name;"
}

echo "=== FIT-08 BLOCO 4+5 — DEPS + IMPORT + RESTART ÚNICO ==="

[ -d "$APP" ] || fail "APP ausente: $APP"
cd "$APP"
[ "$(pwd)" = "$APP" ] || fail "pwd != APP"

HEAD=$(git rev-parse HEAD)
echo "HEAD=$HEAD"
[ "$HEAD" = "$TARGET_HEAD" ] || fail "HEAD != TARGET_HEAD ($TARGET_HEAD)"

[ -f "$APP/requirements.txt" ] || fail "requirements.txt ausente"
[ -x "$PY" ] || fail "python venv ausente: $PY"
[ -x "$PIP" ] || fail "pip venv ausente: $PIP"
[ -f "$DB" ] || fail "banco ausente: $DB"
[ -f "$APP/.env" ] || fail ".env ausente"

DB_SHA_BEFORE=$(sha_file "$DB")
DB_SIZE_BEFORE=$(size_file "$DB")
SERVICE_STATUS_BEFORE=$(systemctl is-active "$SERVICE" 2>/dev/null || echo inactive)
SERVICE_PID_BEFORE=$(systemctl show -p MainPID --value "$SERVICE" 2>/dev/null || echo "0")
ING_TABLES_BEFORE=$(ingestion_tables || true)

echo "DB_SHA_BEFORE=$DB_SHA_BEFORE"
echo "DB_SIZE_BEFORE=$DB_SIZE_BEFORE"
echo "SERVICE_STATUS_BEFORE=$SERVICE_STATUS_BEFORE"
echo "SERVICE_PID_BEFORE=$SERVICE_PID_BEFORE"
echo "INGESTION_TABLES_BEFORE=${ING_TABLES_BEFORE:-<none>}"

# Carrega .env para o processo de import (não imprime SECRET_KEY)
set -a
# shellcheck disable=SC1091
source "$APP/.env"
set +a
echo "SECRET_KEY=PRESENT_IN_ENV=$([ -n "${SECRET_KEY:-}" ] && echo yes || echo no)"
[ -n "${SECRET_KEY:-}" ] || fail "SECRET_KEY ausente no ambiente após source .env"

echo "--- pip install -r requirements.txt (sem --upgrade global; sem requirements-dev) ---"
"$PIP" install -r "$APP/requirements.txt"
if [ -f "$APP/requirements-dev.txt" ]; then
  echo "NOTE: requirements-dev.txt presente — NÃO instalado"
fi

echo "--- py_compile ---"
"$PY" -m py_compile \
  backend/main.py \
  backend/auth.py \
  backend/authz.py \
  backend/cors_config.py \
  backend/route_security_registry.py
PY_COMPILE_OK=yes
echo "PY_COMPILE_OK=yes"

echo "--- import backend.main + flags ---"
IMPORT_OUT=$("$PY" - <<'PY'
import os
import backend.main as m
from backend.authz import api_docs_enabled
from backend.ingestion import FEATURE_FLAG_ENV as ING_FLAG
from backend.performance import FEATURE_FLAG_ENV as PERF_FLAG

title = m.app.title
docs_on = api_docs_enabled()
docs_url = m.app.docs_url
openapi_url = m.app.openapi_url

def off(name: str) -> bool:
    raw = (os.environ.get(name) or "false").strip().lower()
    return raw in {"", "0", "false", "no", "off"}

ing_off = off(ING_FLAG)
perf_off = off(PERF_FLAG)
env = (os.environ.get("ENVIRONMENT") or "").strip().lower()
api_docs_off = (not docs_on) and docs_url is None and openapi_url is None

print(f"APP_TITLE={title}")
print(f"ENVIRONMENT={env}")
print(f"INGESTION_OFF={str(ing_off).lower()}")
print(f"PERFORMANCE_OFF={str(perf_off).lower()}")
print(f"API_DOCS_OFF={str(api_docs_off).lower()}")
print(f"DOCS_URL={docs_url}")
if env != "production":
    raise SystemExit("ENVIRONMENT != production")
if not ing_off or not perf_off:
    raise SystemExit("experimental flags not OFF")
if not api_docs_off:
    raise SystemExit("API docs not OFF")
if title != "AbsenteismoController":
    raise SystemExit(f"unexpected title: {title}")
PY
) || fail "import backend.main / flags falhou"
echo "$IMPORT_OUT"
IMPORT_MAIN_OK=yes
echo "$IMPORT_OUT" | grep -q 'INGESTION_OFF=true' || fail "INGESTION não OFF"
echo "$IMPORT_OUT" | grep -q 'PERFORMANCE_OFF=true' || fail "PERFORMANCE não OFF"
echo "$IMPORT_OUT" | grep -q 'API_DOCS_OFF=true' || fail "API docs não OFF"
FLAGS_OFF=yes
API_DOCS_OFF=yes

echo "--- foundation package imports ---"
"$PY" - <<'PY' || fail "foundation imports falharam"
import backend.services  # noqa: F401
import backend.ingestion  # noqa: F401
import backend.performance  # noqa: F401
print("FOUNDATION_IMPORTS_OK=yes")
PY
FOUNDATION_IMPORTS_OK=yes

# Banco intacto antes do restart; sem tabelas ingestion_* novas
DB_SHA_MID=$(sha_file "$DB")
DB_SIZE_MID=$(size_file "$DB")
[ "$DB_SHA_MID" = "$DB_SHA_BEFORE" ] && [ "$DB_SIZE_MID" = "$DB_SIZE_BEFORE" ] || fail "banco alterado antes do restart"
ING_TABLES_MID=$(ingestion_tables || true)
[ "$ING_TABLES_MID" = "$ING_TABLES_BEFORE" ] || fail "tabelas ingestion_* mudaram (migration indevida?)"
if [ -n "$ING_TABLES_MID" ]; then
  echo "WARN: tabelas ingestion_* já existiam antes: $ING_TABLES_MID"
fi
echo "DB_PRE_RESTART_PRESERVED=yes"
echo "NO_NEW_INGESTION_TABLES=yes"

echo "--- systemctl restart (único) ---"
RESTART_TS=$(date -u +"%Y-%m-%d %H:%M:%S UTC")
RESTART_ATTEMPTED=yes
systemctl restart "$SERVICE"
SERVICE_RESTARTED=yes

# Aguardar até 20s por active + porta
ok=0
for i in $(seq 1 20); do
  sleep 1
  st=$(systemctl is-active "$SERVICE" 2>/dev/null || echo inactive)
  pid=$(systemctl show -p MainPID --value "$SERVICE" 2>/dev/null || echo "0")
  port_probe=no
  if ss -ltn 2>/dev/null | grep -qE '127\.0\.0\.1:8000([[:space:]]|$)'; then
    port_probe=yes
  else
    port_probe=$("$PY" - <<'PY'
import socket
s = socket.socket()
s.settimeout(1)
try:
    s.connect(("127.0.0.1", 8000))
    print("yes")
except Exception:
    print("no")
finally:
    s.close()
PY
)
  fi
  echo "wait ${i}s status=$st pid=$pid port=$port_probe"
  if [ "$st" = "active" ] && [ -n "$pid" ] && [ "$pid" != "0" ] && [ "$pid" != "$SERVICE_PID_BEFORE" ] && [ "$port_probe" = "yes" ]; then
    ok=1
    SERVICE_STATUS=$st
    SERVICE_PID_AFTER=$pid
    break
  fi
done
[ "$ok" = "1" ] || fail "serviço não ficou active com novo PID e porta 8000 em 20s"

echo "--- logs desde o restart ---"
journalctl -u "$SERVICE" --since "$RESTART_TS" --no-pager -n 200 || true

if journalctl -u "$SERVICE" --since "$RESTART_TS" --no-pager -n 400 2>/dev/null | grep -Eqi 'Traceback \(most recent call last\)|FATAL|Worker failed to boot'; then
  # Allow non-fatal noise only if service still active — still NO-GO on clear fatal patterns
  fail "traceback/fatal detectado nos logs pós-restart"
fi

DB_SHA_AFTER=$(sha_file "$DB")
DB_SIZE_AFTER=$(size_file "$DB")
[ "$DB_SHA_AFTER" = "$DB_SHA_BEFORE" ] && [ "$DB_SIZE_AFTER" = "$DB_SIZE_BEFORE" ] || fail "banco alterado após restart"
DB_PRESERVED=yes
ING_TABLES_AFTER=$(ingestion_tables || true)
[ "$ING_TABLES_AFTER" = "$ING_TABLES_BEFORE" ] || fail "tabelas ingestion_* mudaram após restart"

BLOCK45_RESULT=GO
print_summary
