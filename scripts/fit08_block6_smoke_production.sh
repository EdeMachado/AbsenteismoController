#!/usr/bin/env bash
# FIT-08 BLOCO 6 — SMOKE TEST DE PRODUÇÃO (somente leitura)
# Sem login real, sem alteração de banco, sem restart/pip/migration/rollback.
set -euo pipefail

APP=/var/www/absenteismo
TARGET_HEAD=540cda0806326aa14ced57d42fd43e8a69817d08
BASE=http://127.0.0.1:8000
HTTPS_BASE=https://www.absenteismocontroller.com.br
OFFICIAL_ORIGIN=https://www.absenteismocontroller.com.br
RANDOM_ORIGIN=https://evil-example-$(date +%s).invalid
DB="$APP/database/absenteismo.db"
SERVICE=absenteismocontroller.service
PY=/var/www/absenteismo/venv/bin/python3

HEAD=""
SERVICE_STATUS=""
PORT_8000=no
HEALTH_HTTP=""
HEALTH_STATUS=""
DATABASE_HEALTHY=no
DATABASE_INTEGRITY=no
PUBLIC_ROUTES_OK=no
PROTECTED_ROUTES_OK=no
EXPERIMENTAL_ROUTES_OFF=no
API_DOCS_OFF=no
SECURITY_HEADERS_OK=no
CORS_OK=no
CLIENT_2_OK=no
CLIENT_4_OK=no
USERS_OK=no
COMMON_PASSWORDS_ZERO=no
DB_PRESERVED=no
SMOKE_RESULT=NO_GO

print_summary() {
  echo "======== RESUMO ========"
  echo "HEAD=${HEAD:-}"
  echo "SERVICE_STATUS=${SERVICE_STATUS:-}"
  echo "PORT_8000=${PORT_8000:-no}"
  echo "HEALTH_HTTP=${HEALTH_HTTP:-}"
  echo "HEALTH_STATUS=${HEALTH_STATUS:-}"
  echo "DATABASE_HEALTHY=${DATABASE_HEALTHY:-no}"
  echo "DATABASE_INTEGRITY=${DATABASE_INTEGRITY:-no}"
  echo "PUBLIC_ROUTES_OK=${PUBLIC_ROUTES_OK:-no}"
  echo "PROTECTED_ROUTES_OK=${PROTECTED_ROUTES_OK:-no}"
  echo "EXPERIMENTAL_ROUTES_OFF=${EXPERIMENTAL_ROUTES_OFF:-no}"
  echo "API_DOCS_OFF=${API_DOCS_OFF:-no}"
  echo "SECURITY_HEADERS_OK=${SECURITY_HEADERS_OK:-no}"
  echo "CORS_OK=${CORS_OK:-no}"
  echo "CLIENT_2_OK=${CLIENT_2_OK:-no}"
  echo "CLIENT_4_OK=${CLIENT_4_OK:-no}"
  echo "USERS_OK=${USERS_OK:-no}"
  echo "COMMON_PASSWORDS_ZERO=${COMMON_PASSWORDS_ZERO:-no}"
  echo "DB_PRESERVED=${DB_PRESERVED:-no}"
  echo "SMOKE_RESULT=${SMOKE_RESULT:-NO_GO}"
}

fail() {
  echo "FAIL: $*" >&2
  SMOKE_RESULT=NO_GO
  print_summary
  exit 1
}

http_code() {
  local method=${1:-GET}
  local url=$2
  shift 2 || true
  curl -sS -o /dev/null -w '%{http_code}' -m 12 -X "$method" "$url" "$@" || echo ERR
}

http_body() {
  curl -sS -m 12 "$@" || true
}

echo "=== FIT-08 BLOCO 6 — SMOKE PRODUÇÃO (READ ONLY) ==="

[ -d "$APP" ] || fail "APP ausente"
cd "$APP"
[ -x "$PY" ] || fail "python venv ausente"
[ -f "$DB" ] || fail "banco ausente"

HEAD=$(git rev-parse HEAD)
echo "HEAD=$HEAD"
[ "$HEAD" = "$TARGET_HEAD" ] || fail "HEAD != TARGET"

SERVICE_STATUS=$(systemctl is-active "$SERVICE" 2>/dev/null || echo inactive)
echo "SERVICE_STATUS=$SERVICE_STATUS"
[ "$SERVICE_STATUS" = "active" ] || fail "serviço não active"

if ss -ltn 2>/dev/null | grep -qE '127\.0\.0\.1:8000([[:space:]]|$)'; then
  PORT_8000=yes
else
  PORT_8000=$("$PY" - <<'PY'
import socket
s=socket.socket(); s.settimeout(1)
try:
    s.connect(("127.0.0.1", 8000)); print("yes")
except Exception:
    print("no")
finally:
    s.close()
PY
)
fi
echo "PORT_8000=$PORT_8000"
[ "$PORT_8000" = "yes" ] || fail "porta 8000 não escuta"

DB_SHA_BEFORE=$(sha256sum "$DB" | awk '{print $1}')
DB_SIZE_BEFORE=$(stat -c '%s' "$DB")
echo "DB_SHA_BEFORE=$DB_SHA_BEFORE"
echo "DB_SIZE_BEFORE=$DB_SIZE_BEFORE"

# --- health ---
HEALTH_TMP=$(mktemp)
trap 'rm -f "$HEALTH_TMP"' EXIT
HEALTH_HTTP=$(curl -sS -m 12 -o "$HEALTH_TMP" -w '%{http_code}' "$BASE/api/health" || echo ERR)
echo "HEALTH_HTTP=$HEALTH_HTTP"
[ "$HEALTH_HTTP" = "200" ] || fail "GET /api/health != 200"

HEALTH_STATUS=$("$PY" -c 'import json,sys; print(json.load(open(sys.argv[1],encoding="utf-8")).get("status",""))' "$HEALTH_TMP")
DATABASE_HEALTHY=$("$PY" -c 'import json,sys; d=json.load(open(sys.argv[1],encoding="utf-8")); print("yes" if (d.get("checks") or {}).get("database",{}).get("healthy") is True else "no")' "$HEALTH_TMP")
DATABASE_INTEGRITY=$("$PY" -c 'import json,sys; db=(json.load(open(sys.argv[1],encoding="utf-8")).get("checks") or {}).get("database") or {}; print("yes" if (db.get("integrity_ok") is True or db.get("integrity_check") is True) else "no")' "$HEALTH_TMP")
echo "HEALTH_STATUS=$HEALTH_STATUS"
echo "DATABASE_HEALTHY=$DATABASE_HEALTHY"
echo "DATABASE_INTEGRITY=$DATABASE_INTEGRITY"
[ "$HEALTH_STATUS" = "ok" ] || fail "health status != ok"
[ "$DATABASE_HEALTHY" = "yes" ] || fail "database.healthy != true"
[ "$DATABASE_INTEGRITY" = "yes" ] || fail "database integrity flag != true"

# --- páginas principais (200 ou redirect para login) ---
echo "--- páginas ---"
page_ok=yes
for path in / /login /dashboard /clientes /funcionarios /upload /produtividade /dados-powerbi; do
  # -L desativado: observar redirect
  code=$(curl -sS -o /dev/null -w '%{http_code}' -m 12 "$BASE$path" || echo ERR)
  loc=$(curl -sS -o /dev/null -D - -m 12 "$BASE$path" 2>/dev/null | tr -d '\r' | awk 'tolower($1)=="location:"{print $2; exit}')
  echo "PAGE $path -> $code loc=${loc:-}"
  case "$code" in
    200) ;;
    301|302|303|307|308)
      case "${loc,,}" in
        *login*|/login|/login?*|*/login|*/login?*) ;;
        *) page_ok=no; echo "FAIL: redirect sem login em $path" ;;
      esac
      ;;
    *) page_ok=no; echo "FAIL: página $path code=$code" ;;
  esac
done
[ "$page_ok" = "yes" ] || fail "páginas principais inválidas"
PUBLIC_ROUTES_OK=yes

# --- APIs públicas ---
echo "--- APIs públicas ---"
hcode=$(http_code GET "$BASE/api/health")
[ "$hcode" = "200" ] || fail "health público falhou"
# login acessível (sem credenciais reais): endpoint responde 401/422, não 404/500
lcode=$(curl -sS -o /dev/null -w '%{http_code}' -m 12 -X POST "$BASE/api/auth/login" \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  --data 'username=smoke-invalid&password=smoke-invalid' || echo ERR)
echo "LOGIN_PROBE=$lcode"
case "$lcode" in 401|422|400) ;; *) fail "login não acessível de forma esperada ($lcode)" ;; esac

# --- APIs protegidas sem token ---
echo "--- APIs protegidas sem token ---"
prot_ok=yes
for path in /api/clientes /api/atestados /api/uploads /api/usuarios /api/funcionarios /api/produtividade; do
  code=$(http_code GET "$BASE$path")
  echo "ANON $path -> $code"
  case "$code" in
    401|403) ;;
    200|500|ERR) prot_ok=no; echo "FAIL: $path=$code" ;;
    *)
      # 404 pode ocorrer se rota não existir — aceitável apenas se não for 200/500
      if [ "$code" = "404" ]; then echo "NOTE: $path 404"; else prot_ok=no; echo "FAIL: $path=$code"; fi
      ;;
  esac
done
[ "$prot_ok" = "yes" ] || fail "APIs protegidas sem token inválidas"
PROTECTED_ROUTES_OK=yes

# --- experimentais / docs ---
echo "--- experimentais + docs ---"
exp_ok=yes
for path in /api/ingestion /api/ingestion/preview /api/ingestion/import /experimental/ingestion /api/performance /api/performance/shadow; do
  code=$(http_code GET "$BASE$path")
  echo "EXP $path -> $code"
  case "$code" in
    404|401|403|405) ;;
    200|500) exp_ok=no ;;
    *) ;;
  esac
done
for path in /docs /redoc /openapi.json; do
  code=$(http_code GET "$BASE$path")
  echo "DOCS $path -> $code"
  case "$code" in
    404|401|403) ;;
    200) exp_ok=no; echo "FAIL: docs expostos $path" ;;
    *) ;;
  esac
done
[ "$exp_ok" = "yes" ] || fail "rotas experimentais/docs não OFF"
EXPERIMENTAL_ROUTES_OFF=yes
API_DOCS_OFF=yes

# --- security headers (local API) ---
echo "--- security headers ---"
HDRS=$(curl -sS -D - -o /dev/null -m 12 "$BASE/api/health" | tr -d '\r')
need_ok=yes
for h in content-security-policy x-frame-options x-content-type-options referrer-policy permissions-policy; do
  if echo "$HDRS" | grep -Eiq "^${h}:"; then
    echo "HDR_OK $h"
  else
    echo "HDR_MISS $h"
    need_ok=no
  fi
done
CC=$(echo "$HDRS" | awk 'tolower($1)=="cache-control:"{print tolower($0)}')
echo "CACHE_CONTROL_LINE=$CC"
echo "$CC" | grep -Eq 'no-store|no-cache|private' || need_ok=no

# HSTS no domínio HTTPS oficial
HSTS_LINE=$(curl -sS -D - -o /dev/null -m 15 "$HTTPS_BASE/api/health" 2>/dev/null | tr -d '\r' | awk 'tolower($1)=="strict-transport-security:"{print; exit}' || true)
echo "HSTS_LINE=${HSTS_LINE:-ABSENT_OR_HTTPS_UNREACHABLE}"
if [ -z "${HSTS_LINE:-}" ]; then
  need_ok=no
  echo "FAIL: Strict-Transport-Security ausente no domínio HTTPS"
else
  echo "HDR_OK strict-transport-security"
fi
[ "$need_ok" = "yes" ] || fail "security headers incompletos"
SECURITY_HEADERS_OK=yes

# --- CORS ---
echo "--- CORS ---"
CORS_OK_OFFICIAL=$(curl -sS -D - -o /dev/null -m 12 -X OPTIONS "$BASE/api/health" \
  -H "Origin: $OFFICIAL_ORIGIN" \
  -H "Access-Control-Request-Method: GET" | tr -d '\r' | awk 'tolower($1)=="access-control-allow-origin:"{print $2; exit}')
CORS_BAD=$(curl -sS -D - -o /dev/null -m 12 -X OPTIONS "$BASE/api/health" \
  -H "Origin: $RANDOM_ORIGIN" \
  -H "Access-Control-Request-Method: GET" | tr -d '\r' | awk 'tolower($1)=="access-control-allow-origin:"{print $2; exit}')
echo "CORS_OFFICIAL=${CORS_OK_OFFICIAL:-ABSENT}"
echo "CORS_RANDOM=${CORS_BAD:-ABSENT}"
[ "${CORS_OK_OFFICIAL:-}" = "$OFFICIAL_ORIGIN" ] || fail "CORS oficial não refletido"
if [ -n "${CORS_BAD:-}" ]; then
  fail "CORS permitiu origem aleatória"
fi
CORS_OK=yes

# --- banco read-only / inventário agregado (sem PII) ---
echo "--- inventário agregado ---"
QC=$(sqlite3 "$DB" 'PRAGMA quick_check;' | head -1)
IC=$(sqlite3 "$DB" 'PRAGMA integrity_check;' | head -1)
echo "PRAGMA_QUICK_CHECK=$QC"
echo "PRAGMA_INTEGRITY_CHECK=$IC"
[ "$QC" = "ok" ] || fail "quick_check != ok"
[ "$IC" = "ok" ] || fail "integrity_check != ok"

C2=$(sqlite3 "$DB" "SELECT COUNT(*) FROM clients WHERE id=2;")
C4=$(sqlite3 "$DB" "SELECT COUNT(*) FROM clients WHERE id=4;")
U2=$(sqlite3 "$DB" "SELECT COUNT(*) FROM uploads WHERE client_id=2;")
U4=$(sqlite3 "$DB" "SELECT COUNT(*) FROM uploads WHERE client_id=4;")
E2=$(sqlite3 "$DB" "SELECT COUNT(*) FROM atestados WHERE client_id=2;")
E4=$(sqlite3 "$DB" "SELECT COUNT(*) FROM atestados WHERE client_id=4;")
USERS_TOTAL=$(sqlite3 "$DB" "SELECT COUNT(*) FROM users;")
ADMINS_ACTIVE=$(sqlite3 "$DB" "SELECT COUNT(*) FROM users WHERE IFNULL(is_admin,0)=1 AND IFNULL(is_active,0)=1;")
ORPHAN_NON_ADMIN=$(sqlite3 "$DB" "SELECT COUNT(*) FROM users WHERE IFNULL(is_admin,0)=0 AND client_id IS NULL;")

echo "CLIENT_2_PRESENT=$C2 UPLOADS=$U2 EVENTS=$E2"
echo "CLIENT_4_PRESENT=$C4 UPLOADS=$U4 EVENTS=$E4"
echo "USERS_TOTAL=$USERS_TOTAL ADMINS_ACTIVE=$ADMINS_ACTIVE ORPHAN_NON_ADMIN=$ORPHAN_NON_ADMIN"

[ "$C2" = "1" ] && [ "$U2" = "18" ] && [ "$E2" = "4520" ] && CLIENT_2_OK=yes || fail "contagens client 2 divergem"
[ "$C4" = "1" ] && [ "$U4" = "14" ] && [ "$E4" = "333" ] && CLIENT_4_OK=yes || fail "contagens client 4 divergem"
[ "$USERS_TOTAL" = "3" ] && [ "$ADMINS_ACTIVE" = "2" ] && [ "$ORPHAN_NON_ADMIN" = "0" ] && USERS_OK=yes || fail "contagens de usuários divergem"

echo "--- common password count (hashes never printed) ---"
COMMON_COUNT=$("$PY" - <<PY
import sqlite3
import bcrypt
db = "$DB"
commons = [
    b"admin123", b"admin", b"123456", b"password", b"senha", b"senha123",
    b"12345678", b"admin@123", b"Admin123", b"changeme", b"qwerty",
]
con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
rows = con.execute("SELECT password_hash FROM users").fetchall()
con.close()
hits = 0
for (h,) in rows:
    if not h:
        continue
    hb = h.encode("utf-8") if isinstance(h, str) else h
    for p in commons:
        try:
            if bcrypt.checkpw(p, hb):
                hits += 1
                break
        except Exception:
            continue
print(hits)
PY
)
echo "COMMON_PASSWORD_HITS=$COMMON_COUNT"
[ "$COMMON_COUNT" = "0" ] || fail "contas com senha comum > 0"
COMMON_PASSWORDS_ZERO=yes

DB_SHA_AFTER=$(sha256sum "$DB" | awk '{print $1}')
DB_SIZE_AFTER=$(stat -c '%s' "$DB")
[ "$DB_SHA_AFTER" = "$DB_SHA_BEFORE" ] && [ "$DB_SIZE_AFTER" = "$DB_SIZE_BEFORE" ] || fail "banco alterado durante smoke"
DB_PRESERVED=yes
echo "DB_SIZE=$DB_SIZE_AFTER"

SMOKE_RESULT=GO
print_summary
